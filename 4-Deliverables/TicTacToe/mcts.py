"""
Monte Carlo Tree Search for Ultimate Tic-Tac-Toe.
Uses UCB1 for tree descent and random rollouts.
"""

import math
import random
from uttt import get_legal_moves, apply_move


# ---------------------------------------------------------------------------
# Tree node
# ---------------------------------------------------------------------------

class MCTSNode:
    __slots__ = ('state', 'parent', 'move', 'children',
                 'untried_moves', 'visits', 'value')

    def __init__(self, state, parent=None, move=None):
        self.state = state
        self.parent = parent
        self.move = move          # (macro_idx, row, col) that led to this node
        self.children = []
        self.untried_moves = get_legal_moves(state)
        random.shuffle(self.untried_moves)
        self.visits = 0
        self.value = 0.0          # cumulative score from this node's POV

    def is_terminal(self):
        return self.state['status'] != 'ongoing'

    def is_fully_expanded(self):
        return len(self.untried_moves) == 0


# ---------------------------------------------------------------------------
# UCB1
# ---------------------------------------------------------------------------

def ucb1(node, C=math.sqrt(2)):
    if node.visits == 0:
        return float('inf')
    exploitation = node.value / node.visits
    exploration = C * math.sqrt(math.log(node.parent.visits) / node.visits)
    return exploitation + exploration


# ---------------------------------------------------------------------------
# MCTS phases
# ---------------------------------------------------------------------------

def select(node, C):
    """Walk down the tree choosing the child with highest UCB1."""
    while not node.is_terminal():
        if not node.is_fully_expanded():
            return node
        node = max(node.children, key=lambda ch: ucb1(ch, C))
    return node


def expand(node):
    """Pop one untried move, create a child node, return it."""
    move = node.untried_moves.pop()
    child_state = apply_move(node.state, *move)
    child = MCTSNode(child_state, parent=node, move=move)
    node.children.append(child)
    return child


def rollout(state):
    """Play random moves until terminal. Return result relative to the
    player whose turn it was at the START of the rollout."""
    starting_player = state['turn']
    while state['status'] == 'ongoing':
        moves = get_legal_moves(state)
        state = apply_move(state, *random.choice(moves))

    outcome = state['status']   # 'X', 'O', or 'draw'
    if outcome == 'draw':
        return 0.0
    return 1.0 if outcome == starting_player else -1.0


def backpropagate(node, result):
    """Walk up the tree updating visits and value.
    'result' is +1/-1/0 from the perspective of the node's player.
    Each parent flips the sign because it's the opponent's perspective."""
    while node is not None:
        node.visits += 1
        node.value += result
        result = -result
        node = node.parent


# ---------------------------------------------------------------------------
# Main search entry point
# ---------------------------------------------------------------------------

def mcts_search(state, iterations=5000, C=math.sqrt(2)):
    """
    Run MCTS from 'state' for 'iterations' simulations.
    Returns (macro_idx, row, col) of the recommended move.
    """
    if state['status'] != 'ongoing':
        raise ValueError("Cannot search a terminal state.")

    root = MCTSNode(state)

    for _ in range(iterations):
        # 1. Selection
        node = select(root, C)

        # 2. Expansion
        if not node.is_terminal():
            node = expand(node)

        # 3. Rollout
        result = rollout(node.state)

        # 4. Backpropagation
        backpropagate(node, result)

    # Choose most-visited child
    best = max(root.children, key=lambda ch: ch.visits)
    return best.move


if __name__ == '__main__':
    from uttt import new_state
    s = new_state()
    print("Running 1000-iteration MCTS from start...")
    move = mcts_search(s, iterations=1000)
    print(f"Recommended first move: macro={move[0]}, row={move[1]}, col={move[2]}")
