# Implementation Plan — Ultimate Tic-Tac-Toe

## Step 1: Game Logic (`uttt.py`)
- Define state as a plain Python dict (board, macro, next_macro, turn, status)
- Implement `get_legal_moves(state)` — returns list of (macro, micro) tuples respecting the send-to-board constraint
- Implement `apply_move(state, macro, micro)` — returns a new state (no mutation)
- Implement `check_winner(grid)` — checks 8 lines of a 3x3 grid for X/O winner
- Implement `check_sub_board(state, macro)` — updates macro board after a micro move
- Implement `check_game_over(state)` — checks meta-board for winner or global draw
- Write a small smoke test in `__main__` to verify a known game sequence

## Step 2: MCTS AI (`mcts.py`)
- Define `MCTSNode` class with: state, parent, children, untried_moves, visits, value
- Implement `ucb1(node, C)` — returns UCB1 score for a child node
- Implement `select(node)` — walk tree choosing child with highest UCB1 until unexpanded node found
- Implement `expand(node)` — pop one untried move, create and attach child node
- Implement `rollout(state)` — play random legal moves until terminal, return +1/-1/0
- Implement `backpropagate(node, result)` — walk up tree updating visits and value
- Implement `mcts_search(state, iterations, C)` — runs the full loop, returns best (macro, micro)
- Move selection: pick child of root with highest visit count (most robust child)

## Step 3: Flask API (`app.py`)
- Set up Flask app, serve `templates/index.html` at 
`/`
- `POST /new_game` — accepts `{ human_player }`, returns fresh game state
- `POST /move` — accepts `{ state, macro, micro }`, validates move, applies it, returns new state
- `POST /ai_move` — accepts `{ state, iterations }`, runs mcts_search, applies result, returns new state
- Return `400` for illegal moves or moves on terminal states
- Keep server stateless — all state lives in the client request body

## Step 4: Frontend HTML/CSS (`templates/index.html`, `static/style.css`)
- Single HTML page with a 3x3 grid of 3x3 sub-grids (81 cells total)
- CSS grid layout for the board
- Style rules:
  - Active macro cell: colored border highlight
  - Won macro cell: large X/O overlay, sub-cells dimmed and unclickable
  - Drawn macro cell: gray, unclickable
  - Valid micro cell: pointer cursor, hover highlight
  - "Thinking..." overlay while awaiting AI response
- Status bar showing current turn and which player the human is
- Controls: New Game button, AI iterations number input

## Step 5: Frontend JavaScript (`static/game.js`)
- On load: prompt human to pick X or O, call `/new_game`, render board
- `renderBoard(state)` — reads state and redraws all 81 cells + macro overlays
- `handleClick(macro, micro)` — validates it's human's turn and cell is legal, calls `/move`
- After human move: if game ongoing and it's AI's turn, call `/ai_move` with "Thinking..." shown
- On terminal state: display win/draw banner with a restart button
- All API calls via `fetch()` with JSON body/response

## Step 6: Integration Testing & Polish
- Play full games end-to-end in the browser
- Verify send-to-any-board rule works when target is won/full
- Verify AI never plays an illegal move
- Tune default iterations (start at 5000, adjust based on response time)
- Confirm draw detection works (rare but must be correct)
