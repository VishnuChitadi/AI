"""
Monte Carlo Tree Search for Ultimate Tic-Tac-Toe.
UCB1 selection, random rollouts, +1/0/-1 scoring.
"""

import math
import random
from uttt import get_legal_moves, apply_move


class MCTSNode:
    __slots__ = ("state", "parent", "move", "children",
                 "untried_moves", "visits", "wins")

    def __init__(self, state, parent=None, move=None):
        self.state = state
        self.parent = parent
        self.move = move                        # (macro_idx, row, col) or None for root
        self.children = []
        self.untried_moves = get_legal_moves(state)
        random.shuffle(self.untried_moves)
        self.visits = 0
        self.wins = 0.0

    def is_terminal(self):
        return self.state["status"] != "ongoing"

    def is_fully_expanded(self):
        return len(self.untried_moves) == 0


# ---------------------------------------------------------------------------
# UCB1
# ---------------------------------------------------------------------------

def _ucb1(node, C=math.sqrt(2)):
    if node.visits == 0:
        return float("inf")
    return node.wins / node.visits + C * math.sqrt(math.log(node.parent.visits) / node.visits)


# ---------------------------------------------------------------------------
# MCTS phases
# ---------------------------------------------------------------------------

def _select(node, C):
    while not node.is_terminal():
        if not node.is_fully_expanded():
            return node
        node = max(node.children, key=lambda ch: _ucb1(ch, C))
    return node


def _expand(node):
    move = node.untried_moves.pop()
    child_state = apply_move(node.state, *move)
    child = MCTSNode(child_state, parent=node, move=move)
    node.children.append(child)
    return child


def _rollout(state):
    """Random playout. Returns score from the perspective of the player
    whose turn it was at the START of the rollout."""
    starting_player = state["turn"]
    while state["status"] == "ongoing":
        moves = get_legal_moves(state)
        state = apply_move(state, *random.choice(moves))
    outcome = state["status"]
    if outcome == "draw":
        return 0.0
    return 1.0 if outcome == starting_player else -1.0


def _backpropagate(node, result):
    """Walk up the tree. Flip sign at each level (opponent perspective)."""
    while node is not None:
        node.visits += 1
        node.wins += result
        result = -result
        node = node.parent


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def mcts_search(state, iterations=5000, C=math.sqrt(2)):
    """
    Run MCTS and return (macro_idx, row, col) of the best move.
    'Best' = child of root with the highest visit count.
    """
    if state["status"] != "ongoing":
        raise ValueError("Cannot search a terminal state.")

    root = MCTSNode(state)

    for _ in range(iterations):
        node = _select(root, C)
        if not node.is_terminal():
            node = _expand(node)
        result = _rollout(node.state)
        _backpropagate(node, result)

    best = max(root.children, key=lambda ch: ch.visits)
    return best.move


if __name__ == "__main__":
    from uttt import new_state
    s = new_state()
    print("Running 1 000-iteration MCTS from start…")
    move = mcts_search(s, iterations=1000)
    print(f"Recommended first move: macro={move[0]}, row={move[1]}, col={move[2]}")
