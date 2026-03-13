/* ===== Ultimate Tic-Tac-Toe — Frontend ===== */

let gameState   = null;
let humanPlayer = null;

// ---- DOM refs ----
const metaBoard      = document.getElementById("meta-board");
const statusBar      = document.getElementById("status-bar");
const thinking       = document.getElementById("thinking");
const overlay        = document.getElementById("overlay");
const overlayMsg     = document.getElementById("overlay-message");
const picker         = document.getElementById("picker");
const overlayRestart = document.getElementById("overlay-restart");
const iterInput      = document.getElementById("iter-input");

// ---- Bindings ----
document.getElementById("pick-x").addEventListener("click", () => startGame("X"));
document.getElementById("pick-o").addEventListener("click", () => startGame("O"));
document.getElementById("new-game-btn").addEventListener("click", showPicker);
overlayRestart.addEventListener("click", showPicker);

// ---- Show picker ----
function showPicker() {
  overlayMsg.textContent = "Pick your side";
  picker.style.display = "flex";
  overlayRestart.style.display = "none";
  overlay.classList.add("visible");
}

// ---- Start game ----
async function startGame(human) {
  humanPlayer = human;
  overlay.classList.remove("visible");

  const res = await fetch("/new_game", {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify({ human_player: human }),
  });
  const data = await res.json();
  gameState = data.state;
  render();

  if (gameState.turn !== humanPlayer) {
    await doAiMove();
  }
}

// ---- Human move ----
async function handleCellClick(macroIdx, row, col) {
  if (!gameState || gameState.status !== "ongoing") return;
  if (gameState.turn !== humanPlayer) return;

  const res = await fetch("/move", {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify({ state: gameState, macro_idx: macroIdx, row, col }),
  });

  if (!res.ok) {
    const err = await res.json();
    console.warn("Illegal move:", err.error);
    return;
  }

  const data = await res.json();
  gameState = data.state;
  render();

  if (gameState.status !== "ongoing") { showGameOver(); return; }
  await doAiMove();
}

// ---- AI move ----
async function doAiMove() {
  if (!gameState || gameState.status !== "ongoing") return;

  thinking.classList.add("visible");
  metaBoard.style.pointerEvents = "none";

  const iterations = Math.max(100, Math.min(50000, parseInt(iterInput.value, 10) || 5000));

  const res = await fetch("/ai_move", {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify({ state: gameState, iterations }),
  });

  thinking.classList.remove("visible");
  metaBoard.style.pointerEvents = "";

  if (!res.ok) { console.warn("AI move failed:", await res.json()); return; }

  const data = await res.json();
  gameState = data.state;
  render();

  if (gameState.status !== "ongoing") showGameOver();
}

// ---- Render ----
function render() {
  if (!gameState) return;
  const { board, macro, next_macro, turn, status } = gameState;

  // Status bar
  if (status === "ongoing") {
    const whose = turn === humanPlayer ? "Your" : "AI's";
    statusBar.innerHTML = `${whose} turn &nbsp;|&nbsp; You are <span>${humanPlayer}</span>`;
  }

  metaBoard.innerHTML = "";

  for (let m = 0; m < 9; m++) {
    const subDiv = document.createElement("div");
    subDiv.className = "sub-board";

    const macroStatus = macro[m];
    const isActive = status === "ongoing" &&
                     turn === humanPlayer &&
                     macroStatus === null &&
                     (next_macro === null || next_macro === m);

    if      (macroStatus === "X")    subDiv.classList.add("won-X");
    else if (macroStatus === "O")    subDiv.classList.add("won-O");
    else if (macroStatus === "draw") subDiv.classList.add("drawn");
    else if (isActive)               subDiv.classList.add("active");

    // Large symbol overlay for resolved sub-boards
    if (macroStatus !== null) {
      const ov = document.createElement("div");
      ov.className = `macro-overlay ${macroStatus}`;
      ov.textContent = macroStatus === "draw" ? "—"
                     : macroStatus === "X"    ? "✕" : "○";
      subDiv.appendChild(ov);
    }

    // Cells
    for (let r = 0; r < 3; r++) {
      for (let c = 0; c < 3; c++) {
        const cell = document.createElement("div");
        cell.className = "cell";
        const val = board[m][r][c];

        if (val) {
          cell.textContent = val === "X" ? "✕" : "○";
          cell.classList.add(val);
        } else if (isActive) {
          cell.classList.add("legal");
          const mi = m, ri = r, ci = c;
          cell.addEventListener("click", () => handleCellClick(mi, ri, ci));
        }

        subDiv.appendChild(cell);
      }
    }

    metaBoard.appendChild(subDiv);
  }
}

// ---- Game over ----
function showGameOver() {
  const s = gameState.status;
  if (s === "draw") {
    overlayMsg.textContent = "It's a draw!";
  } else if (s === humanPlayer) {
    overlayMsg.textContent = "You win! 🎉";
  } else {
    overlayMsg.textContent = "AI wins!";
  }
  statusBar.innerHTML = `Game over — <span>${s === "draw" ? "Draw" : s + " wins"}</span>`;
  picker.style.display = "none";
  overlayRestart.style.display = "inline-block";
  overlay.classList.add("visible");
}
