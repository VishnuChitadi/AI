# A* Motion Planning Implementation Plan

## Overview
Complete the A* search implementation in `/workspaces/AI/2-Motion_Planning/motion.py` to find a path from `(1,1)` to `(R-2, C-2)` on a grid with obstacles.

---

## Part 1: Complete the `State` Class

### 1.1 Add `manhattan_distance()` method
```python
def manhattan_distance(self):
    """Return Manhattan distance from current position to goal"""
    return abs(self.goal[0] - self.position[0]) + abs(self.goal[1] - self.position[1])
```

### 1.2 Add `__lt__()` method for PriorityQueue comparison
```python
def __lt__(self, other):
    """Required for PriorityQueue when priorities are equal"""
    return False  # Arbitrary tiebreaker
```

### 1.3 Add `get_successors()` method
```python
def get_successors(self):
    """Generate valid successor states for up, down, left, right moves"""
    successors = []
    row, col = self.position

    # Four possible moves: (row_delta, col_delta)
    moves = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # up, down, left, right

    for dr, dc in moves:
        new_row, new_col = row + dr, col + dc

        # Check if move is valid (not an obstacle)
        if self.grid[new_row][new_col] != 1:
            # Create new state with deep copy of grid
            new_grid = deepcopy(self.grid)
            new_grid[new_row][new_col] = '*'  # Mark path

            new_state = State((new_row, new_col), self.goal, new_grid)
            new_state.total_moves = self.total_moves + 1
            successors.append(new_state)

    return successors
```

---

## Part 2: Complete the A* Search in `main()`

### 2.1 Add visited dictionary
```python
visited = {start_position: True}
```

### 2.2 Implement the search loop
```python
while not queue.empty():
    # Get state with lowest f(n) = g(n) + h(n)
    priority, current_state = queue.get()

    # Check if goal reached
    if current_state.position == goal_position:
        print("Goal reached!")
        print_grid(current_state.grid)
        return

    # Generate and process successors
    for successor in current_state.get_successors():
        if successor.position not in visited:
            visited[successor.position] = True
            priority = successor.total_moves + successor.manhattan_distance()
            queue.put((priority, successor))

# If we get here, no path was found
print("No path found!")
```

---

## Files to Modify
- `/workspaces/AI/2-Motion_Planning/motion.py`

---

## Verification
Run the program and verify:
```bash
cd /workspaces/AI/2-Motion_Planning
python motion.py
```

**Expected output:**
- For each trial, the original grid prints first
- Then "Goal reached!" with the solution grid showing `*` marks along the path
- The path should go from `(1,1)` to the bottom-right corner
- All 5 easy trials should find solutions (with seed(0))
