# Ultimate Tic-Tac-Toe — Specification

## Overview

A web-based two-player game (human vs. AI) of Ultimate Tic-Tac-Toe. The AI uses
Monte Carlo Tree Search (MCTS) with the UCB1 selection policy and random rollouts.

---

## Game Rules

- The board is a 3×3 grid of 3×3 sub-boards (81 cells total).
- X moves first and may place on any empty cell of any active sub-board.
- The cell position chosen within the sub-board determines which sub-board the
  opponent must play in next (e.g. placing in top-right of any sub-board sends
  the opponent to the top-right sub-board on the macro grid).
- If the forced sub-board is already won or drawn, the opponent may play on any
  active sub-board (free choice).
- Winning a sub-board claims that position on the macro board.
- The first player to win three macro positions in a row (row, column, or
  diagonal) wins the game. If all sub-boards resolve with no macro winner, the
  game is a draw.

---

## Architecture

```
4-Deliverables/TicTacToe/
├── app.py                  # Flask HTTP server (stateless REST API)
├── uttt.py                 # Pure game-logic module
├── mcts.py                 # MCTS AI module
├── templates/
│   └── index.html          # Single-page UI
└── static/
    ├── style.css
    └── game.js             # All client-side logic
```

---

## Backend — `uttt.py`

### State representation (plain dict, JSON-serialisable)

| Key           | Type                        | Description                                      |
|---------------|-----------------------------|--------------------------------------------------|
| `board`       | `list[9][3][3]` of str/null | Cell contents per sub-board                      |
| `macro`       | `list[9]` of str/null       | Winner of each sub-board (null / "X" / "O" / "draw") |
| `next_macro`  | int / null                  | Forced sub-board index, null = free choice       |
| `turn`        | `"X"` or `"O"`             | Whose turn it is                                 |
| `status`      | str                         | `"ongoing"` / `"X"` / `"O"` / `"draw"`          |

### Functions

- `new_state(first_player="X") → state`
- `get_legal_moves(state) → list[(macro_idx, row, col)]`
- `apply_move(state, macro_idx, row, col) → new_state` (immutable; deep-copies)
- `check_winner(cells_9) → "X" | "O" | "draw" | None`

---

## Backend — `mcts.py`

### Algorithm

```
for i in range(iterations):
    node = select(root)          # UCB1 tree descent
    node = expand(node)          # add one child for an untried move
    result = rollout(node.state) # random playout to terminal
    backpropagate(node, result)  # update visits + value up the tree

return argmax(root.children, key=visits)
```

### UCB1

```
UCB1(node) = (value / visits) + C * sqrt(ln(parent.visits) / visits)
```

- C = √2 (default)
- Unvisited nodes return +∞ so they are explored first.

### Rollout scoring (from perspective of player at root)

| Outcome  | Score |
|----------|-------|
| Win      | +1.0  |
| Draw     |  0.0  |
| Loss     | −1.0  |

Backpropagation flips sign at each level (opponent's perspective).

### Tuneable parameter

- `iterations` — default 5 000, range 100–50 000 (user-adjustable via UI).

---

## Backend — `app.py` (Flask, stateless)

The full game state is held in the browser and sent with every request.

| Endpoint    | Method | Body                              | Response                     |
|-------------|--------|-----------------------------------|------------------------------|
| `GET /`     | GET    | —                                 | `index.html`                 |
| `/new_game` | POST   | `{ human_player: "X"\|"O" }`     | `{ state, human_player }`    |
| `/move`     | POST   | `{ state, macro_idx, row, col }` | `{ state }` or 400           |
| `/ai_move`  | POST   | `{ state, iterations }`          | `{ state, move }` or 400     |

---

## Frontend — `game.js`

1. On load — show overlay asking human to pick X or O.
2. `startGame(human)` — POST `/new_game`; if AI goes first, call `doAiMove()`.
3. `handleCellClick(macro_idx, row, col)` — POST `/move`, then `doAiMove()`.
4. `doAiMove()` — POST `/ai_move`; show "thinking" spinner during fetch.
5. `render(state)` — rebuild the entire board DOM from state:
   - Highlight active sub-boards.
   - Overlay X/O/draw on won sub-boards.
   - Attach click handlers only on legal cells when it is the human's turn.
6. On terminal state — show game-over overlay.

---

## UI / UX

- Responsive grid rendered with CSS Grid.
- Active sub-board highlighted in a distinct colour.
- Won sub-boards show a large symbol overlay and are darkened.
- "AI is thinking…" indicator shown during MCTS computation.
- AI iterations slider / number input in the control bar.
- "New Game" button restarts without page reload.
