"""
Lights Out experiment: BFS vs IDS
Counts nodes CREATED and EXPANDED for increasing board sizes
"""

from collections import deque
from typing import Tuple, Set, List

Board = Tuple[Tuple[int, ...], ...]


# ---------- Board Utilities ----------

def create_initial_board(n: int) -> Board:
    """Create an n x n board with all lights ON."""
    return tuple(tuple(1 for _ in range(n)) for _ in range(n))


def is_goal(board: Board) -> bool:
    """Check if all lights are OFF."""
    return all(cell == 0 for row in board for cell in row)


def toggle(board: Board, row: int, col: int) -> Board:
    """Toggle a button and its neighbors."""
    n = len(board)
    new_board = [list(r) for r in board]

    for dr, dc in [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)]:
        r, c = row + dr, col + dc
        if 0 <= r < n and 0 <= c < n:
            new_board[r][c] ^= 1

    return tuple(tuple(r) for r in new_board)


def get_successors(board: Board) -> List[Board]:
    """Generate all successor boards."""
    n = len(board)
    return [toggle(board, r, c) for r in range(n) for c in range(n)]


# ---------- BFS ----------

def bfs_lights_out(n: int, max_nodes: int):
    """Breadth-First Search with node limit."""
    initial = create_initial_board(n)
    frontier = deque([initial])
    visited: Set[Board] = {initial}

    nodes_created = 1
    nodes_expanded = 0

    while frontier:
        board = frontier.popleft()
        nodes_expanded += 1

        if is_goal(board):
            return nodes_created, nodes_expanded

        if nodes_expanded >= max_nodes:
            return nodes_created, nodes_expanded

        for child in get_successors(board):
            if child not in visited:
                visited.add(child)
                frontier.append(child)
                nodes_created += 1

    return nodes_created, nodes_expanded


# ---------- IDS ----------

class FoundSolution(Exception):
    pass


def depth_limited_search(board, depth, visited, counters):
    """Depth-limited DFS used by IDS."""
    counters["expanded"] += 1

    if is_goal(board):
        raise FoundSolution

    if depth == 0:
        visited.add(board)
        return

    for child in get_successors(board):
        counters["created"] += 1
        if child not in visited:
            depth_limited_search(child, depth - 1, visited, counters)


def ids_lights_out(n: int, max_depth: int):
    """Iterative Deepening Search."""
    initial = create_initial_board(n)

    for depth in range(max_depth + 1):
        visited = set()
        counters = {"created": 1, "expanded": 0}

        try:
            depth_limited_search(initial, depth, visited, counters)
        except FoundSolution:
            return counters["created"], counters["expanded"]

    return counters["created"], counters["expanded"]


# ---------- MAIN EXPERIMENT ----------

if __name__ == "__main__":
    MAX_N = 6

    print("N, BFS_created, BFS_expanded, IDS_created, IDS_expanded")

    for n in range(2, MAX_N + 1):
        bfs_created, bfs_expanded = bfs_lights_out(n, max_nodes=200_000)
        ids_created, ids_expanded = ids_lights_out(n, max_depth=10)

        print(f"{n}, {bfs_created}, {bfs_expanded}, "
              f"{ids_created}, {ids_expanded}")
