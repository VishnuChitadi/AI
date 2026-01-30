# -----------------------------------
# Helper functions (used by both BFS and IDS)
# -----------------------------------

def is_safe(state, row, col):
    for r, c in enumerate(state):
        if c == col:
            return False
        if abs(r - row) == abs(c - col):
            return False
    return True


def get_successors(state, n):
    successors = []
    row = len(state)
    for col in range(n):
        if is_safe(state, row, col):
            successors.append(state + (col,))
    return successors


def is_goal(state, n):
    return len(state) == n


# -----------------------------------
# Breadth-First Search (BFS)
# -----------------------------------

def solve_n_queens_bfs(n):
    frontier = [()]
    nodes_created = 1
    nodes_expanded = 0

    while frontier:
        state = frontier.pop(0)
        nodes_expanded += 1

        if is_goal(state, n):
            return state, nodes_created, nodes_expanded

        successors = get_successors(state, n)
        nodes_created += len(successors)
        frontier.extend(successors)

    return None, nodes_created, nodes_expanded


# -----------------------------------
# Iterative Deepening Search (IDS)
# -----------------------------------

def depth_limited_dfs(state, n, depth_limit, counters):
    counters["expanded"] += 1

    if is_goal(state, n):
        return state

    if len(state) == depth_limit:
        return None

    for successor in get_successors(state, n):
        counters["created"] += 1
        result = depth_limited_dfs(successor, n, depth_limit, counters)
        if result is not None:
            return result

    return None


def solve_n_queens_ids(n):
    total_created = 1
    total_expanded = 0

    for depth_limit in range(n + 1):
        print(f"IDS: N={n}, depth limit={depth_limit}")  # progress output
        counters = {"created": 0, "expanded": 0}

        result = depth_limited_dfs((), n, depth_limit, counters)

        total_created += counters["created"]
        total_expanded += counters["expanded"]

        if result is not None:
            return result, total_created, total_expanded

    return None, total_created, total_expanded


# -----------------------------------
# Run experiments and print results
# -----------------------------------

if __name__ == "__main__":

    print("N-Queens Results (BFS)")
    print("N | Nodes Created | Nodes Expanded")
    print("---------------------------------")

    for n in range(3, 12):  # limit BFS so it finishes
        solution, created, expanded = solve_n_queens_bfs(n)
        print(f"{n} | {created:<13} | {expanded}")

    print("\nN-Queens Results (IDS)")
    print("N | Nodes Created | Nodes Expanded")
    print("---------------------------------")

    for n in range(3, 12):
        solution, created, expanded = solve_n_queens_ids(n)
        print(f"{n} | {created:<13} | {expanded}")








