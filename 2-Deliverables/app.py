"""Flask web interface for the Sokoban solver."""

from flask import Flask, jsonify, request, render_template
from Sokobot import solve, parse_level

app = Flask(__name__)

# Pre-designed puzzles (name -> level text)
PUZZLES = {
    "Level 1 - Tiny": (
        "######\n"
        "#    #\n"
        "# $@ #\n"
        "# .  #\n"
        "#    #\n"
        "######"
    ),
    "Level 2 - Microban #1": (
        "####\n"
        "# .#\n"
        "#  ###\n"
        "#*@  #\n"
        "#  $ #\n"
        "#  ###\n"
        "####"
    ),
    "Level 3 - Three Boxes": (
        "########\n"
        "#  . . #\n"
        "# $$$$ #\n"
        "# .  . #\n"
        "#  @   #\n"
        "########"
    ),
    "Level 4 - Corridor": (
        " #####\n"
        "##   ##\n"
        "# .$  #\n"
        "# $.@ #\n"
        "##   ##\n"
        " #####"
    ),
    "Level 5 - L-Shape": (
        "#####\n"
        "#   ##\n"
        "# $  #\n"
        "## $ #\n"
        " #.@ #\n"
        " #.  #\n"
        " #####"
    ),
}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/puzzles")
def get_puzzles():
    """Return the list of available pre-designed puzzles."""
    result = {}
    for name, level_text in PUZZLES.items():
        result[name] = level_text
    return jsonify(result)


@app.route("/solve", methods=["POST"])
def solve_puzzle():
    """Accept a puzzle string and return the solution."""
    data = request.get_json()
    if not data or "puzzle" not in data:
        return jsonify({"error": "Missing 'puzzle' field"}), 400

    puzzle_text = data["puzzle"]

    try:
        parse_level(puzzle_text)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    solution = solve(puzzle_text)
    if solution is None:
        return jsonify({"error": "No solution found"}), 200

    return jsonify({"solution": solution, "moves": len(solution)})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
