"""
Flask backend for Ultimate Tic-Tac-Toe.
Stateless: full game state is sent by the client on every request.
"""

from flask import Flask, request, jsonify, render_template
from uttt import new_state, get_legal_moves, apply_move
from mcts import mcts_search

app = Flask(__name__)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/new_game', methods=['POST'])
def new_game():
    data = request.get_json(force=True)
    human = data.get('human_player', 'X')
    if human not in ('X', 'O'):
        return jsonify({'error': 'human_player must be X or O'}), 400
    state = new_state(first_player='X')
    return jsonify({'state': state, 'human_player': human})


@app.route('/move', methods=['POST'])
def move():
    data = request.get_json(force=True)
    state = data.get('state')
    macro = data.get('macro')
    micro = data.get('micro')

    if state is None or macro is None or micro is None:
        return jsonify({'error': 'Missing state, macro, or micro'}), 400

    if state['status'] != 'ongoing':
        return jsonify({'error': 'Game is already over'}), 400

    macro_idx = macro[0] * 3 + macro[1]
    row, col = micro

    legal = get_legal_moves(state)
    if (macro_idx, row, col) not in legal:
        return jsonify({'error': 'Illegal move'}), 400

    new_s = apply_move(state, macro_idx, row, col)
    return jsonify({'state': new_s})


@app.route('/ai_move', methods=['POST'])
def ai_move():
    data = request.get_json(force=True)
    state = data.get('state')
    iterations = int(data.get('iterations', 5000))

    if state is None:
        return jsonify({'error': 'Missing state'}), 400

    if state['status'] != 'ongoing':
        return jsonify({'error': 'Game is already over'}), 400

    iterations = max(100, min(iterations, 50000))
    macro_idx, row, col = mcts_search(state, iterations=iterations)
    new_s = apply_move(state, macro_idx, row, col)
    return jsonify({
        'state': new_s,
        'move': {'macro_idx': macro_idx, 'row': row, 'col': col}
    })


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    app.run(debug=True, port=5000)
