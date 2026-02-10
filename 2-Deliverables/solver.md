# Sokoban Solver Design

## Problem Summary

Sokoban is a grid-based puzzle where a player pushes boxes onto designated goal
locations. The player moves in 4 cardinal directions and can push (never pull)
exactly one box at a time. The puzzle is solved when every goal square has a box
on it. We target instances up to ~8x8 with up to 5 boxes.

## Puzzle Format

Standard Sokoban text notation:

| Symbol | Meaning         |
|--------|-----------------|
| `#`    | Wall            |
| ` `    | Floor           |
| `.`    | Goal            |
| `$`    | Box             |
| `@`    | Player          |
| `+`    | Player on goal  |
| `*`    | Box on goal     |

## State Representation

**Static map** (stored once per puzzle):
- Set of wall positions
- Set of goal positions
- Grid dimensions

**Search state** (per node in A*):
- `(normalized_player_pos, frozenset(box_positions))`

This tuple is hashable, so it can live in a `set` for visited-state tracking and
serves as a dictionary key. We do **not** copy the entire grid per state -- walls
and goals never change.

### Player Normalization

Two states with identical box layouts but different player positions *within the
same reachable zone* are equivalent for the purpose of pushing boxes. We
normalize the player position to the **top-left-most reachable cell** (minimum
row, then minimum column) via a flood-fill that treats boxes as walls. This
collapses many equivalent states and shrinks the search space significantly.

## Algorithm: A* Search

```
OPEN  = priority queue ordered by f = g + h
CLOSED = set of visited states

push initial state onto OPEN with g=0

while OPEN is not empty:
    pop state with lowest f
    if state is goal: reconstruct and return solution
    if state in CLOSED: skip
    add state to CLOSED

    for each successor state (push a box one step):
        if successor has a box on a dead square: prune
        if successor triggers a freeze deadlock: prune
        compute h(successor) via Hungarian algorithm
        push successor onto OPEN with g' = g + 1, f' = g' + h
```

Each move in our search corresponds to one **push** (the player walks to the
push position and then pushes the box one cell). The cost `g` counts pushes.
We also record the sequence of player moves (UDLR) so we can output the full
solution path.

## Heuristic: Hungarian Algorithm on BFS Distances

### Step 1 -- Precompute BFS distances

For each goal, run a BFS outward treating only walls as obstacles (ignoring
boxes). This gives the true minimum number of pushes to move a box from any
floor cell to that goal in an otherwise empty map.

Result: a 2D lookup `dist[cell][goal]` available in O(1) per query.

### Step 2 -- Hungarian algorithm

At each state we build a cost matrix where entry `(i, j)` is
`dist[box_i][goal_j]`. The Hungarian algorithm finds the minimum-cost perfect
matching -- each box is assigned a unique goal, and the total cost is minimized.

**Why this is admissible**: Every box must end up on a distinct goal. The BFS
distance for each pair is a lower bound on the pushes needed for that single box
(it ignores other boxes). The Hungarian matching is the cheapest way to achieve
all assignments simultaneously, so the sum is still a lower bound.

**Complexity**: O(n^3) for n boxes via the Hungarian algorithm. For n <= 5 this
is negligible.

### Why not simpler heuristics?

- *Nearest-goal for each box*: Multiple boxes can claim the same goal,
  producing a weaker lower bound and expanding far more states.
- *Manhattan distance*: Ignores walls, making the estimate even looser on maps
  with corridors or obstacles.

## Deadlock Detection

Deadlocks are states from which no solution exists. Detecting them early is the
single most important optimization for Sokoban solvers.

### 1. Dead-square detection (precomputed)

A floor cell is **dead** if a box placed there can never reach any goal by any
sequence of pushes (considering only walls, not other boxes).

**Computation** -- for each goal square, simulate pulling a box away from the
goal in all four directions (reverse push). Flood-fill all squares reachable by
reverse pushes. Any floor cell not reached by any goal's reverse-flood is a dead
square.

At search time: if a push would place a box on a dead square, prune that
successor immediately. This is an O(1) check per push.

### 2. Freeze deadlock detection (runtime)

A box is **frozen on an axis** if it cannot be pushed along that axis:
- Blocked by a wall on either side, OR
- Blocked by another frozen box on either side.

A box is **frozen** if it is frozen on both axes. If any frozen box is not on a
goal, the state is a deadlock.

This requires iterative/recursive evaluation because freeze status propagates
(box A may be frozen because box B is frozen, which is frozen because of box A).
We handle this with a simple iterative fixpoint or recursive DFS with memoization
over the current state's box set.

**Examples of freeze deadlocks**:
- A box in a corner (wall on two perpendicular sides) not on a goal.
- Two boxes adjacent to each other along a wall, with at least one not on a goal.
- A 2x2 block of boxes with at least one not on a goal.

## Solution Output

The solver returns the sequence of moves as a string of characters:
`U` (up), `D` (down), `L` (left), `R` (right).

This includes both the "walking" moves to reach the push position and the push
move itself. The full path can be reconstructed by recording the player's
movement between pushes (via BFS on the player's reachable area).

## Implementation Plan

1. **Parser**: Read a Sokoban level from text into the static map and initial
   state.
2. **Dead-square precomputation**: Reverse-flood from each goal.
3. **BFS distance precomputation**: BFS from each goal, store distances.
4. **Hungarian algorithm**: Implement the O(n^3) assignment solver (or use
   `scipy.optimize.linear_sum_assignment`).
5. **A* search loop**: Priority queue, state expansion, deadlock pruning,
   heuristic evaluation, solution reconstruction.
6. **Move reconstruction**: Convert push sequence into full UDLR move string.
7. **Driver / CLI**: Load a puzzle, run the solver, print the solution.

## Data Structures Summary

| Component               | Structure                                      |
|--------------------------|------------------------------------------------|
| Walls                    | `set` of `(row, col)` tuples                   |
| Goals                    | `set` of `(row, col)` tuples                   |
| State                    | `(player_pos, frozenset(box_positions))`        |
| OPEN list                | `heapq` priority queue of `(f, g, state, path)`|
| CLOSED set               | `set` of states                                 |
| Dead squares             | `set` of `(row, col)` tuples                   |
| BFS distance table       | `dict[(row,col), dict[(row,col), int]]`         |
| Hungarian cost matrix    | 2D list / numpy array, n_boxes x n_goals        |
