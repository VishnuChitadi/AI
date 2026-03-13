# Ultimate Tic-Tac-Toe — Implementation Plan

## Build Order

Build and verify each layer before moving to the next.

```
1. uttt.py       — game logic (state, moves, win detection)
2. mcts.py       — MCTS AI (selection, expansion, rollout, backprop)
3. app.py        — Flask REST API (stateless endpoints)
4. index.html    — page skeleton + overlay structure
5. style.css     — layout and visual polish
6. game.js       — all client-side game logic
```

---

## Step 1 — `uttt.py`

### State dict (JSON-safe, no tuples/sets)

```python
{
  "board":      [[[None]*3]*3] * 9,  # board[macro][row][col]
  "macro":      [None]*9,            # None | "X" | "O" | "draw"
  "next_macro": None,                # int 0-8 or None (free choice)
  "turn":       "X",
  "status":     "ongoing"            # "ongoing" | "X" | "O" | "draw"
}
```

### Key decisions
- `apply_move` deep-copies state → all functions are pure (safe for MCTS tree)
- `next_macro` is set to the cell index chosen; if that sub-board is already
  resolved, it is set to `None` (free choice)
- Macro winner ignores "draw" cells — only "X" / "O" form winning lines;
  all 9 resolved with no winner → macro draw

### Functions
| Function | Notes |
|---|---|
| `new_state(first_player)` | Returns fresh state |
| `get_legal_moves(state)` | Returns `list[(m, r, c)]` |
| `apply_move(state, m, r, c)` | Returns new state |
| `check_winner(flat9)` | Used for both sub and macro boards |

### Smoke test (run directly)
- Initial legal moves = 81
- After one move, legal moves = 9 (forced sub-board)
- Verify `next_macro` routing and free-choice fallback

---

## Step 2 — `mcts.py`

### Node structure
```python
class MCTSNode:
    state          # game state at this node
    parent         # parent node (None for root)
    move           # (m, r, c) that produced this node
    children       # list of MCTSNode
    untried_moves  # moves not yet expanded (shuffled)
    visits         # int
    wins           # float (cumulative score)
```

### Four phases per iteration

| Phase | Action |
|---|---|
| **Select** | Walk tree with UCB1 until a node with untried moves or terminal |
| **Expand** | Pop one untried move, create child node |
| **Rollout** | Play random moves from child until terminal |
| **Backprop** | Walk up tree: `visits += 1`, `wins += result`; flip result sign each level |

### UCB1
```
score = wins/visits  +  C * sqrt(ln(parent.visits) / visits)
```
- C = √2 (standard; experiment with 1.0–2.0)
- Unvisited nodes → score = +∞ (guaranteed to expand first)

### Rollout scoring
- Scored from the perspective of the player **at the root** of the search
- Win = +1, Draw = 0, Loss = −1
- Sign flips each ply during backpropagation

### Entry point
```python
def mcts_search(state, iterations=5000) -> (macro_idx, row, col)
```
Returns the child of root with the highest visit count (most robust).

### Smoke test
- Run 1 000 iterations from start, confirm a move is returned
- Run from near-terminal state, confirm correct winning move chosen

---

## Step 3 — `app.py`

Stateless Flask server — client owns all state.

### Endpoints

| Route | Method | Request body | Success response |
|---|---|---|---|
| `/` | GET | — | `index.html` |
| `/new_game` | POST | `{ human_player }` | `{ state, human_player }` |
| `/move` | POST | `{ state, macro_idx, row, col }` | `{ state }` |
| `/ai_move` | POST | `{ state, iterations }` | `{ state, move }` |

### Validation
- `/move` — verify `(macro_idx, row, col)` is in `get_legal_moves(state)`
- `/ai_move` — clamp iterations to `[100, 50000]`
- Both — return `400` with `{ error: "..." }` on bad input or finished game

---

## Step 4 — `index.html`

Minimal skeleton; all dynamic content built by JS.

```
body
├── h1 — title
├── #status-bar
├── #controls  (New Game button + iterations input)
├── #meta-board  (9 sub-board divs injected by JS)
├── #thinking  (hidden spinner)
└── #overlay  (visible on load)
    ├── #overlay-message
    ├── #picker  (X / O buttons)
    └── #overlay-restart  (Play Again — hidden until game over)
```

Overlay starts `visible` so player immediately sees the side-picker.

---

## Step 5 — `style.css`

### Layout
- `#meta-board` — CSS Grid 3×3, each cell is a `.sub-board`
- `.sub-board` — CSS Grid 3×3, each cell is a `.cell`
- Gap between sub-boards > gap between cells (visual grouping)

### State classes applied by JS

| Class | When applied |
|---|---|
| `.active` | Sub-board is the forced next target |
| `.won-X` / `.won-O` | Sub-board claimed by that player |
| `.drawn` | Sub-board ended in draw |
| `.legal` | Cell is a playable move (human's turn only) |
| `.X` / `.O` | Cell already occupied |

### Overlay
- Full-screen semi-transparent backdrop
- Centred card with message + buttons
- Toggled by `.visible` class

---

## Step 6 — `game.js`

### State
```js
let gameState = null;   // mirrors server-side state dict
let humanPlayer = null; // "X" or "O"
```

### Flow

```
page load
  → showPicker()

pick side
  → startGame(human)
    → POST /new_game
    → render(state)
    → if AI goes first: doAiMove()

human clicks cell
  → handleCellClick(macro_idx, row, col)
    → POST /move
    → render(state)
    → if ongoing: doAiMove()

doAiMove()
  → show #thinking, disable board
  → POST /ai_move
  → hide #thinking, enable board
  → render(state)
  → if terminal: showGameOver()
```

### `render(state)`
- Clear and rebuild `#meta-board` from scratch each call
- For each sub-board (0–8):
  - Apply state class (`won-X`, `active`, etc.)
  - If won/drawn: inject `.macro-overlay` with large symbol
  - For each cell: show piece symbol, or attach click handler if legal

### Error handling
- `/move` returning 400 → log to console, do not update state
- `/ai_move` returning 400 → log, do not update state

---

## Testing Checklist

- [ ] 81 legal moves at game start
- [ ] Forced sub-board routing works
- [ ] Free-choice when forced board is resolved
- [ ] Sub-board win detection (all 8 lines)
- [ ] Macro win detection (all 8 lines)
- [ ] Draw detection (all sub-boards resolved, no macro winner)
- [ ] AI plays both as X (first) and O (second)
- [ ] "Play Again" resets without page reload
- [ ] Iterations input correctly adjusts AI strength
