"""Sokoban solver using A* search with Hungarian-matching heuristic."""

import heapq
import sys
from collections import deque

import numpy as np
from scipy.optimize import linear_sum_assignment

# Directions: (dr, dc) and their labels
DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]
DIR_NAMES = ["U", "D", "L", "R"]
DIR_MAP = dict(zip(DIRS, DIR_NAMES))


# ── Parsing ──────────────────────────────────────────────────────────────────

def parse_level(text):
    """Parse a Sokoban level string into its components.

    Returns (walls, goals, boxes, player, nrows, ncols).
    """
    lines = text.splitlines()
    walls = set()
    goals = set()
    boxes = set()
    player = None

    for r, line in enumerate(lines):
        for c, ch in enumerate(line):
            pos = (r, c)
            if ch == "#":
                walls.add(pos)
            elif ch == ".":
                goals.add(pos)
            elif ch == "$":
                boxes.add(pos)
            elif ch == "@":
                player = pos
            elif ch == "+":  # player on goal
                player = pos
                goals.add(pos)
            elif ch == "*":  # box on goal
                boxes.add(pos)
                goals.add(pos)

    if player is None:
        raise ValueError("No player (@/+) found in level")
    if len(boxes) != len(goals):
        raise ValueError(f"Mismatch: {len(boxes)} boxes vs {len(goals)} goals")

    nrows = len(lines)
    ncols = max(len(line) for line in lines) if lines else 0
    return walls, goals, frozenset(boxes), player, nrows, ncols


# ── Flood fill / reachability ────────────────────────────────────────────────

def flood_fill(start, walls, boxes):
    """BFS flood fill from start, treating walls and boxes as obstacles.

    Returns the set of reachable cells and the canonical (top-left) position.
    """
    obstacles = walls | boxes
    visited = set()
    queue = deque([start])
    visited.add(start)
    canon = start  # track min (row, col)

    while queue:
        pos = queue.popleft()
        if pos < canon:
            canon = pos
        for dr, dc in DIRS:
            npos = (pos[0] + dr, pos[1] + dc)
            if npos not in obstacles and npos not in visited:
                visited.add(npos)
                queue.append(npos)

    return visited, canon


def normalize_player(player, walls, boxes):
    """Return the canonical player position for this reachable zone."""
    _, canon = flood_fill(player, walls, boxes)
    return canon


# ── Dead-square precomputation ───────────────────────────────────────────────

def compute_dead_squares(walls, goals, nrows, ncols):
    """Compute cells where a box can never reach any goal (via reverse pushes).

    For each goal, simulate pulling boxes outward (reverse push). A cell is
    alive if it can be reached by at least one goal's reverse flood. Everything
    else that is floor is dead.
    """
    alive = set()

    for goal in goals:
        # BFS reverse-push from this goal
        visited = set()
        visited.add(goal)
        queue = deque([goal])

        while queue:
            pos = queue.popleft()
            for dr, dc in DIRS:
                # Reverse-push: if a box was pushed in direction d to land
                # at pos, it came from (pos - d) and the player stood at
                # (pos - 2d) (behind the box).
                box_from = (pos[0] - dr, pos[1] - dc)
                player_was_at = (pos[0] - 2 * dr, pos[1] - 2 * dc)
                if box_from not in walls and player_was_at not in walls:
                    if box_from not in visited:
                        visited.add(box_from)
                        queue.append(box_from)

        alive |= visited

    # Dead = all floor cells not in alive
    all_floor = set()
    for r in range(nrows):
        for c in range(ncols):
            if (r, c) not in walls:
                all_floor.add((r, c))

    return all_floor - alive


# ── BFS distance precomputation ──────────────────────────────────────────────

def compute_bfs_distances(goals, walls):
    """For each goal, BFS over floor cells (walls-only obstacles).

    Returns dist_to_goal: dict mapping goal -> dict mapping cell -> push distance.
    """
    dist_to_goal = {}

    for goal in goals:
        dist = {goal: 0}
        queue = deque([goal])
        while queue:
            pos = queue.popleft()
            d = dist[pos]
            for dr, dc in DIRS:
                npos = (pos[0] + dr, pos[1] + dc)
                if npos not in walls and npos not in dist:
                    dist[npos] = d + 1
                    queue.append(npos)
        dist_to_goal[goal] = dist

    return dist_to_goal


# ── Hungarian heuristic ──────────────────────────────────────────────────────

def hungarian_heuristic(boxes, goals_list, dist_to_goal):
    """Minimum-cost matching of boxes to goals using Hungarian algorithm.

    Returns the heuristic value (lower bound on total pushes).
    """
    n = len(goals_list)
    cost = np.empty((n, n), dtype=np.int64)
    INF = 10**9

    boxes_list = list(boxes)
    for i, box in enumerate(boxes_list):
        for j, goal in enumerate(goals_list):
            gd = dist_to_goal[goal]
            cost[i, j] = gd.get(box, INF)

    row_ind, col_ind = linear_sum_assignment(cost)
    total = cost[row_ind, col_ind].sum()
    return int(total) if total < INF else INF


# ── Freeze deadlock detection ────────────────────────────────────────────────

def is_freeze_deadlock(boxes, walls, goals):
    """Check whether any box is frozen and not on a goal (deadlock).

    A box is frozen on an axis if both cells along that axis are blocked
    (wall or another frozen box). A box frozen on both axes is fully frozen.
    Uses iterative fixpoint computation.
    """
    box_set = set(boxes)
    # frozen_h[pos] = True means frozen on horizontal axis (can't push left/right)
    # frozen_v[pos] = True means frozen on vertical axis (can't push up/down)
    frozen_h = {}
    frozen_v = {}

    for b in box_set:
        frozen_h[b] = False
        frozen_v[b] = False

    changed = True
    while changed:
        changed = False
        for b in box_set:
            # Horizontal axis: frozen if BOTH left and right are blocked
            if not frozen_h[b]:
                left = (b[0], b[1] - 1)
                right = (b[0], b[1] + 1)
                left_blocked = left in walls or (left in box_set and frozen_h[left])
                right_blocked = right in walls or (right in box_set and frozen_h[right])
                if left_blocked and right_blocked:
                    frozen_h[b] = True
                    changed = True

            # Vertical axis: frozen if BOTH up and down are blocked
            if not frozen_v[b]:
                up = (b[0] - 1, b[1])
                down = (b[0] + 1, b[1])
                up_blocked = up in walls or (up in box_set and frozen_v[up])
                down_blocked = down in walls or (down in box_set and frozen_v[down])
                if up_blocked and down_blocked:
                    frozen_v[b] = True
                    changed = True

    # A box frozen on both axes and not on a goal => deadlock
    for b in box_set:
        if frozen_h[b] and frozen_v[b] and b not in goals:
            return True
    return False


# ── Path reconstruction (player movement between pushes) ─────────────────────

def bfs_player_path(start, target, walls, boxes):
    """BFS for shortest player path from start to target, avoiding walls & boxes."""
    if start == target:
        return ""
    obstacles = walls | boxes
    visited = {start: None}  # cell -> (parent, direction_name)
    queue = deque([start])

    while queue:
        pos = queue.popleft()
        for (dr, dc), name in zip(DIRS, DIR_NAMES):
            npos = (pos[0] + dr, pos[1] + dc)
            if npos not in obstacles and npos not in visited:
                visited[npos] = (pos, name)
                if npos == target:
                    # reconstruct
                    path = []
                    cur = npos
                    while visited[cur] is not None:
                        parent, move = visited[cur]
                        path.append(move)
                        cur = parent
                    return "".join(reversed(path))
                queue.append(npos)

    return None  # unreachable


# ── A* Solver ────────────────────────────────────────────────────────────────

def solve(level_text):
    """Full solver that returns the UDLR move string."""
    walls, goals, boxes, player, nrows, ncols = parse_level(level_text)
    goals_list = list(goals)
    goals_fs = frozenset(goals)

    dead_squares = compute_dead_squares(walls, goals, nrows, ncols)
    dist_to_goal = compute_bfs_distances(goals, walls)

    canon_player = normalize_player(player, walls, boxes)
    init_state = (canon_player, boxes)

    h0 = hungarian_heuristic(boxes, goals_list, dist_to_goal)
    counter = 0
    open_heap = []
    # Store: (f, tiebreak, g, state, actual_player, current_boxes_set, push_history)
    heapq.heappush(open_heap, (h0, counter, 0, init_state, player, boxes, []))
    counter += 1

    closed = set()

    while open_heap:
        _f, _, g, state, actual_player, cur_boxes_fs, history = heapq.heappop(open_heap)

        if cur_boxes_fs == goals_fs:
            return _build_move_string(walls, player, boxes, history)

        if state in closed:
            continue
        closed.add(state)

        reachable, _ = flood_fill(actual_player, walls, cur_boxes_fs)
        box_set = set(cur_boxes_fs)

        for box in cur_boxes_fs:
            for dr, dc in DIRS:
                push_from = (box[0] - dr, box[1] - dc)
                push_to = (box[0] + dr, box[1] + dc)

                if push_from not in reachable:
                    continue
                if push_to in walls or push_to in box_set:
                    continue
                if push_to in dead_squares:
                    continue

                new_boxes = frozenset(cur_boxes_fs - {box} | {push_to})

                if is_freeze_deadlock(new_boxes, walls, goals):
                    continue

                new_player = box
                new_canon = normalize_player(new_player, walls, new_boxes)
                new_state = (new_canon, new_boxes)

                if new_state in closed:
                    continue

                new_g = g + 1
                new_h = hungarian_heuristic(new_boxes, goals_list, dist_to_goal)
                new_f = new_g + new_h

                new_history = history + [(actual_player, box, (dr, dc))]
                heapq.heappush(open_heap, (new_f, counter, new_g, new_state, new_player, new_boxes, new_history))
                counter += 1

    return None


def _build_move_string(walls, initial_player, initial_boxes, push_history):
    """Build the full UDLR string from push history and initial state."""
    moves = []
    current_player = initial_player
    current_boxes = set(initial_boxes)

    for _player_before, box_pos, (dr, dc) in push_history:
        # Walk from current_player to push_from position
        push_from = (box_pos[0] - dr, box_pos[1] - dc)
        walk = bfs_player_path(current_player, push_from, walls, frozenset(current_boxes))
        if walk is None:
            raise RuntimeError(f"Cannot walk from {current_player} to {push_from}")
        moves.append(walk)

        # Execute the push
        moves.append(DIR_MAP[(dr, dc)])
        current_boxes.discard(box_pos)
        push_to = (box_pos[0] + dr, box_pos[1] + dc)
        current_boxes.add(push_to)
        current_player = box_pos  # player steps into where box was

    return "".join(moves)


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python Sokobot.py <level_file>")
        print("       python Sokobot.py --text '<level_string>'")
        sys.exit(1)

    if sys.argv[1] == "--text":
        level_text = " ".join(sys.argv[2:]).replace("\\n", "\n")
    else:
        with open(sys.argv[1]) as f:
            level_text = f.read()

    _, goals, boxes, _, nrows, ncols = parse_level(level_text)
    print(f"Level: {nrows}x{ncols}, {len(boxes)} boxes, {len(goals)} goals")
    print("Solving...")
    solution = solve(level_text)

    if solution is None:
        print("No solution found.")
        sys.exit(1)
    else:
        print(f"Solution ({len(solution)} moves):")
        print(solution)


if __name__ == "__main__":
    main()
