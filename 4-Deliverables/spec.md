# Ultimate Tic-Tac-Toe — Project Specification

## Overview

A web-based implementation of Ultimate Tic-Tac-Toe (UTTT) where a human plays against an AI powered by Monte Carlo Tree Search (MCTS). The game runs in the browser with a Python backend serving the AI logic via a REST API.

---

## Game Rules

### Board Structure
- The game is played on a **3×3 meta-board**, where each of the 9 cells contains a **3×3 sub-board**.
- Each cell is identified by `(macro_row, macro_col)` and each cell within a sub-board by `(micro_row, micro_col)`.
- Total of **81 playable squares**.

### Gameplay
1. **X goes first** and may play on any of the 81 squares.
2. The `(micro_row, micro_col)` of the move just made **determines the macro cell** where the opponent must play next.
3. This constraint repeats each turn.
4. If the target macro cell is already **won or full (drawn)**, the current player may play on **any active (unfinished) macro cell**.
5. A player **wins a sub-board** by getting three in a row on it (standard tic-tac-toe). The sub-board is then marked with that player's symbol and is closed to further play.
6. A sub-board with no winner but no empty squares is a **local draw** — it counts as neither player's on the meta-board.
7. The game ends when:
   - A player wins **three sub-boards in a row** on the meta-board → that player wins.
   - No winning line is possible on the meta-board and all active boards are full → **global draw**.

---

## Project Structure

```
4-Deliverables/
├── spec.md                  ← this file
├── app.py                   ← Flask backend (API + static serving)
├── uttt.py                  ← Game logic (board state, rules, win detection)
├── mcts.py                  ← MCTS AI implementation
├── templates/
│   └── index.html           ← Single-page frontend
└── static/
    ├── style.css
    └── game.js              ← Frontend game logic and API calls
```

---

## Backend

### Technology
- **Python 3**, **Flask**

### Modules

#### `uttt.py` — Game State
Responsible for all game logic. No I/O.

**State representation:**
```python
{
  "board": [[[None]*3 for _ in range(3)] for _ in range(3)],   # sub-boards[macro][micro] = None/'X'/'O'
  "macro": [[None]*3 for _ in range(3)],                        # macro board winners
  "next_macro": None | (row, col),                              # None = free choice
  "turn": 'X' | 'O',
  "status": 'ongoing' | 'X' | 'O' | 'draw'
}
```

**Key functions:**
- `get_legal_moves(state) -> list[(macro, micro)]` — returns all valid moves given the current constraint.
- `apply_move(state, macro, micro) -> new_state` — returns a new state (immutable updates).
- `check_winner(board_3x3) -> 'X' | 'O' | 'draw' | None` — checks a 3×3 grid for a terminal result.
- `check_game_over(state) -> 'X' | 'O' | 'draw' | None`

#### `mcts.py` — Monte Carlo Tree Search

**Algorithm:**

1. **Selection** — walk the tree from root using UCB1 until reaching an unexpanded node.
2. **Expansion** — add one child node for an untried legal move.
3. **Simulation (Rollout)** — play random legal moves until the game ends.
4. **Backpropagation** — update visit counts and scores up the tree.

**UCB1 formula:**
```
UCB1 = (w / n) + C * sqrt(ln(N) / n)
```
- `w` = wins from this node's perspective
- `n` = visits to this node
- `N` = visits to parent
- `C` = exploration constant (default `√2 ≈ 1.414`, tunable)

**Scoring:**
- Win for the moving player: `+1`
- Loss for the moving player: `-1`
- Draw: `0`

**Move selection:** after the search budget is exhausted, pick the child of the root with the **highest visit count** (most robust child).

**Key class:**
```python
class MCTSNode:
    state: GameState
    parent: MCTSNode | None
    children: list[MCTSNode]
    untried_moves: list
    visits: int
    value: float

def mcts_search(state, iterations=5000, C=1.414) -> (macro, micro)
```

**Iteration budget:** default `5000`. Expose as a configurable parameter.

#### `app.py` — Flask API

| Method | Endpoint      | Body / Params                          | Response                              |
|--------|---------------|----------------------------------------|---------------------------------------|
| POST   | `/new_game`   | `{ "human_player": "X" \| "O" }`      | initial `game_state`                  |
| POST   | `/move`       | `{ "state": ..., "macro": [r,c], "micro": [r,c] }` | updated `game_state` + if AI turn: AI move applied |
| POST   | `/ai_move`    | `{ "state": ..., "iterations": int }` | updated `game_state` after AI move    |

All state is **stateless on the server** — the full game state is sent by the client on each request.

---

## Frontend

### Technology
- Vanilla HTML/CSS/JavaScript (no frameworks)
- Communicates with backend via `fetch()` JSON calls

### Layout

```
┌─────────────────────────────────┐
│         ULTIMATE TIC-TAC-TOE    │
│  You are: X     Turn: X         │
│                                 │
│  ┌───────┬───────┬───────┐      │
│  │ . │ . │ . │ . │ . │ . │      │
│  │ . │ . │ . │ . │ . │ . │      │
│  │ . │ . │ . │ . │ . │ . │      │
│  ├───────┼───────┼───────┤      │
│  │  ...  │  ...  │  ...  │      │
│  ├───────┼───────┼───────┤      │
│  │  ...  │  ...  │  ...  │      │
│  └───────┴───────┴───────┘      │
│                                 │
│  [New Game]  AI Iterations: 5000│
└─────────────────────────────────┘
```

### Visual Rules
- **Active (playable) macro cell**: highlighted with a colored border.
- **Won macro cell**: filled with a large X or O overlay; sub-cells are dimmed and unclickable.
- **Drawn macro cell**: dimmed, unclickable.
- **Valid micro cell**: clickable, hover effect.
- **Thinking indicator**: while awaiting the AI response, display a "Thinking..." overlay and disable input.
- **Game over banner**: display winner or draw result with a restart prompt.

### Interaction Flow
1. Page load → prompt human to choose X or O, start game.
2. Human clicks a valid cell → POST `/move` → update board.
3. If AI's turn: POST `/ai_move` → show "Thinking..." → update board.
4. Repeat until terminal state → show result.

---

## AI Settings

| Parameter   | Default | Notes                                      |
|-------------|---------|---------------------------------------------|
| `iterations`| 5000    | Exposed in UI as a number input (100–50000) |
| `C`         | 1.414   | Exploration constant, hardcoded             |

---

## Win / Draw Detection Logic

### Sub-board winner
Check all 8 lines (3 rows, 3 cols, 2 diagonals) for three matching non-None values.

### Sub-board draw
No winner and no empty cells remaining.

### Meta-board winner
Apply the same 8-line check to the `macro` grid using sub-board winners only (drawn sub-boards count as neither).

### Global draw
No meta-winner and no legal moves remain (all sub-boards are won or drawn).

---

## Error Handling
- Illegal move submitted by client → return `400` with error message.
- AI called on a terminal state → return `400`.
- All other server errors → return `500`.

---

## Milestones

1. **`uttt.py`** — implement and unit-test game logic (legal moves, move application, win detection).
2. **`mcts.py`** — implement MCTS, verify it beats random play consistently.
3. **`app.py`** — wire up Flask endpoints, test with `curl`.
4. **Frontend** — build HTML/CSS/JS, connect to API, test full game loop.
5. **Polish** — highlight active board, animate AI thinking, tune default iterations.
