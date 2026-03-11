"""
Ultimate Tic-Tac-Toe — Game Logic
State is a plain dict; all functions return new states (no mutation).
"""

import copy


# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------

def new_state(first_player='X'):
    return {
        'board': [[[None]*3 for _ in range(3)] for _ in range(9)],  # board[macro_idx][row][col]
        'macro': [None]*9,       # winner of each sub-board (None / 'X' / 'O' / 'draw')
        'next_macro': None,      # None = free choice; int 0-8 = forced board
        'turn': first_player,
        'status': 'ongoing',     # 'ongoing' / 'X' / 'O' / 'draw'
    }


def rc_to_idx(row, col):
    """Convert (row, col) to flat index 0-8."""
    return row * 3 + col


def idx_to_rc(idx):
    return divmod(idx, 3)


# ---------------------------------------------------------------------------
# Win detection
# ---------------------------------------------------------------------------

LINES = [
    (0,1,2),(3,4,5),(6,7,8),   # rows
    (0,3,6),(1,4,7),(2,5,8),   # cols
    (0,4,8),(2,4,6),           # diagonals
]

def _check_flat(cells):
    """cells: list of 9 values. Returns 'X', 'O', 'draw', or None."""
    for a,b,c in LINES:
        if cells[a] and cells[a] == cells[b] == cells[c]:
            return cells[a]
    if all(v is not None for v in cells):
        return 'draw'
    return None


def check_sub_winner(board_3x3):
    """board_3x3: 3x3 list. Returns 'X', 'O', 'draw', or None."""
    flat = [board_3x3[r][c] for r in range(3) for c in range(3)]
    return _check_flat(flat)


def check_meta_winner(macro):
    """macro: list of 9 values (None/'X'/'O'/'draw'). Returns 'X','O','draw',None."""
    # Only X/O count for meta wins; 'draw' cells are neutral
    effective = [v if v in ('X','O') else None for v in macro]
    for a,b,c in LINES:
        if effective[a] and effective[a] == effective[b] == effective[c]:
            return effective[a]
    # Global draw: no winner possible and no active boards remain
    if all(v is not None for v in macro):
        return 'draw'
    return None


# ---------------------------------------------------------------------------
# Move logic
# ---------------------------------------------------------------------------

def get_legal_moves(state):
    """Return list of (macro_idx, row, col) for all legal moves."""
    if state['status'] != 'ongoing':
        return []

    nm = state['next_macro']
    if nm is not None and state['macro'][nm] is None:
        candidates = [nm]
    else:
        # Free choice: any unfinished board
        candidates = [i for i in range(9) if state['macro'][i] is None]

    moves = []
    for m in candidates:
        board = state['board'][m]
        for r in range(3):
            for c in range(3):
                if board[r][c] is None:
                    moves.append((m, r, c))
    return moves


def apply_move(state, macro_idx, row, col):
    """Return a new state after placing state['turn'] at (macro_idx, row, col)."""
    s = copy.deepcopy(state)
    player = s['turn']

    s['board'][macro_idx][row][col] = player

    # Check if this sub-board is now won/drawn
    result = check_sub_winner(s['board'][macro_idx])
    if result is not None:
        s['macro'][macro_idx] = result

    # Determine next forced board
    next_m = rc_to_idx(row, col)
    if s['macro'][next_m] is None:
        s['next_macro'] = next_m
    else:
        s['next_macro'] = None  # free choice

    # Check meta-board
    meta = check_meta_winner(s['macro'])
    if meta is not None:
        s['status'] = meta
    else:
        s['status'] = 'ongoing'

    s['turn'] = 'O' if player == 'X' else 'X'
    return s


# ---------------------------------------------------------------------------
# Quick smoke test
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    s = new_state()
    moves = get_legal_moves(s)
    print(f"Initial legal moves: {len(moves)} (expected 81)")

    # X plays center of center board
    s = apply_move(s, 4, 1, 1)
    print(f"After X at (4,1,1): next_macro={s['next_macro']}, turn={s['turn']}")
    moves = get_legal_moves(s)
    print(f"Legal moves for O: {len(moves)} (expected 9, board 4 center is taken)")
