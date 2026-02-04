"""
Motion planning on a rectangular grid using A* search
"""

from random import random
from random import seed
from queue import PriorityQueue
from copy import deepcopy


class State(object):

    def __init__(self, start_position, goal_position, start_grid):
        self.position = start_position
        self.goal = goal_position
        self.grid = start_grid
        self.total_moves = 0

    def manhattan_distance(self):
        """Return Manhattan distance from current position to goal"""
        return abs(self.goal[0] - self.position[0]) + abs(self.goal[1] - self.position[1])

    def __lt__(self, other):
        """Required for PriorityQueue when priorities are equal"""
        return False  # Arbitrary tiebreaker

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


def create_grid():

    """
    Create and return a randomized grid

    0's in the grid indcate free squares
    1's indicate obstacles

    DON'T MODIFY THIS ROUTINE.
    DON'T MODIFY THIS ROUTINE.
    DON'T MODIFY THIS ROUTINE.
    DON'T MODIFY THIS ROUTINE.
    ARE YOU MODIFYING THIS ROUTINE?
    IF SO, STOP IT.
    """

    # Start with a num_rows by num_cols grid of all zeros
    grid = [[0 for c in range(num_cols)] for r in range(num_rows)]

    # Put ones around the boundary
    grid[0] = [1 for c in range(num_cols)]
    grid[num_rows - 1] = [1 for c in range(num_cols)]

    for r in range(num_rows):
        grid[r][0] = 1
        grid[r][num_cols - 1] = 1

    # Sprinkle in obstacles randomly
    for r in range(1, num_rows - 1):
        for c in range(2, num_cols - 2):
            if random() < obstacle_prob:
                grid[r][c] = 1;

    # Make sure the goal and start spaces are clear
    grid[1][1] = 0
    grid[num_rows - 2][num_cols - 2] = 0

    return grid


def print_grid(grid):

    """
    Print a grid, putting spaces in place of zeros for readability

    DON'T MODIFY THIS ROUTINE.
    DON'T MODIFY THIS ROUTINE.
    DON'T MODIFY THIS ROUTINE.
    DON'T MODIFY THIS ROUTINE.
    ARE YOU MODIFYING THIS ROUTINE?
    IF SO, STOP IT.
    """

    for r in range(num_rows):
        for c in range(num_cols):
            if grid[r][c] == 0:
                print(' ', end='')
            else:
                print(grid[r][c], end='')
        print('')

    print('')

    return 


def solve(grid):
    """
    Run A* search on the given grid.
    Returns True if path found, False otherwise.
    """
    start_position = (1, 1)
    goal_position = (num_rows - 2, num_cols - 2)
    start_state = State(start_position, goal_position, grid)
    start_state.grid[1][1] = '*'

    priority = start_state.total_moves + start_state.manhattan_distance()

    queue = PriorityQueue()
    queue.put((priority, start_state))

    visited = {start_position: True}

    while not queue.empty():
        priority, current_state = queue.get()

        if current_state.position == goal_position:
            return True

        for successor in current_state.get_successors():
            if successor.position not in visited:
                visited[successor.position] = True
                priority = successor.total_moves + successor.manhattan_distance()
                queue.put((priority, successor))

    return False


def main():
    """
    Use A* search to find a path from the upper left to the lower right
    of the puzzle grid

    Complete this method to implement the search
    At the end, print the solution state

    Each State object has a copy of the grid

    When you make a move by generating a new State, put a * on its grid
    to show the solution path
    """

    # Keep generating grids until we find one with a valid path
    attempts = 0
    while True:
        attempts += 1
        grid = create_grid()
        if solve(grid):
            return attempts


if __name__ == '__main__':

    seed(0)

    results = []

    #--- Easy mode

    # Global variables
    # Saves us the trouble of continually passing them as parameters
    num_rows = 8
    num_cols = 16
    obstacle_prob = .20

    for trial in range(5):
        attempts = main()
        results.append(("Easy", trial + 1, attempts))

    #--- Hard mode
    num_rows = 15
    num_cols = 30
    obstacle_prob = .30

    for trial in range(5):
        attempts = main()
        results.append(("Harder", trial + 1, attempts))

    #--- INSANE mode
    num_rows = 20
    num_cols = 60
    obstacle_prob = .35

    for trial in range(5):
        attempts = main()
        results.append(("INSANE", trial + 1, attempts))

    # Print results table
    print("\n" + "=" * 45)
    print(f"{'Difficulty':<12} {'Trial':<8} {'Attempts':<10} {'Status'}")
    print("=" * 45)
    for difficulty, trial, attempts in results:
        print(f"{difficulty:<12} {trial:<8} {attempts:<10} {'Success'}")
    print("=" * 45)
    print(f"All {len(results)} trials completed successfully!")