"""
Ultimate Tic-Tac-Toe — Game Logic
State is a plain dict (JSON-serialisable). All functions are pure / non-mutating.
"""

import copy

LINES = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
]


def new_state(first_player="X"):
    return {
        "board":      [[[None]*3 for _ in range(3)] for _ in range(9)],
        "macro":      [None]*9,
        "next_macro": None,
        "turn":       first_player,
        "status":     "ongoing",
    }


def check_winner(flat9):
    """flat9: list of 9 values. Returns 'X', 'O', 'draw', or None."""
    for a, b, c in LINES:
        if flat9[a] and flat9[a] == flat9[b] == flat9[c]:
            return flat9[a]
    if all(v is not None for v in flat9):
        return "draw"
    return None


def _sub_winner(board3x3):
    return check_winner([board3x3[r][c] for r in range(3) for c in range(3)])


def _macro_winner(macro):
    effective = [v if v in ("X", "O") else None for v in macro]
    for a, b, c in LINES:
        if effective[a] and effective[a] == effective[b] == effective[c]:
            return effective[a]
    if all(v is not None for v in macro):
        return "draw"
    return None


def get_legal_moves(state):
    """Return list of (macro_idx, row, col) for all legal moves."""
    if state["status"] != "ongoing":
        return []
    nm = state["next_macro"]
    if nm is not None and state["macro"][nm] is None:
        candidates = [nm]
    else:
        candidates = [i for i in range(9) if state["macro"][i] is None]
    moves = []
    for m in candidates:
        brd = state["board"][m]
        for r in range(3):
            for c in range(3):
                if brd[r][c] is None:
                    moves.append((m, r, c))
    return moves


def apply_move(state, macro_idx, row, col):
    """Return a new state after the current player places at (macro_idx, row, col)."""
    s = copy.deepcopy(state)
    player = s["turn"]

    s["board"][macro_idx][row][col] = player

    result = _sub_winner(s["board"][macro_idx])
    if result is not None:
        s["macro"][macro_idx] = result

    next_m = row * 3 + col
    s["next_macro"] = next_m if s["macro"][next_m] is None else None

    meta = _macro_winner(s["macro"])
    s["status"] = meta if meta is not None else "ongoing"

    s["turn"] = "O" if player == "X" else "X"
    return s


if __name__ == "__main__":
    s = new_state()
    moves = get_legal_moves(s)
    print(f"Initial legal moves: {len(moves)} (expected 81)")
    s = apply_move(s, 4, 1, 1)
    print(f"After X at (4,1,1): next_macro={s['next_macro']}, turn={s['turn']}")
    print(f"Legal moves for O: {len(get_legal_moves(s))} (expected 8, centre taken)")
