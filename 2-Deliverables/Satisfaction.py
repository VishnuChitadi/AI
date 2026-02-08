"""
3-CNF-SAT Phase Transition Experiment

Investigates the phase transition behavior of randomized 3-CNF-SAT
as a function of the clause-to-variable ratio.
"""

import random
import matplotlib.pyplot as plt


def generate(n, m):
    """
    Generate a random 3-CNF instance.

    Args:
        n: Number of variables (numbered 1 to n)
        m: Clause-to-variable ratio

    Returns:
        List of clauses, where each clause is a list of 3 literals.
        Positive integers represent variables, negative integers represent negations.
        Example: [1, -2, 3] means (x1 OR NOT x2 OR x3)
    """
    num_clauses = int(n * m)
    clauses = []

    for _ in range(num_clauses):
        clause = []
        for _ in range(3):
            # Pick a random variable (1 to n)
            var = random.randint(1, n)
            # Randomly negate it
            if random.random() < 0.5:
                var = -var
            clause.append(var)
        clauses.append(clause)

    return clauses


def unit_propagate(clauses, assignment):
    """
    Apply unit propagation: if a clause has only one unassigned literal,
    that literal must be true.

    Returns updated (clauses, assignment) or (None, None) if conflict detected.
    """
    changed = True
    while changed:
        changed = False
        for clause in clauses:
            unassigned = []
            satisfied = False

            for lit in clause:
                var = abs(lit)
                if var in assignment:
                    # Check if this literal satisfies the clause
                    if (lit > 0 and assignment[var]) or (lit < 0 and not assignment[var]):
                        satisfied = True
                        break
                else:
                    unassigned.append(lit)

            if satisfied:
                continue

            if len(unassigned) == 0:
                # Conflict: clause is false
                return None, None

            if len(unassigned) == 1:
                # Unit clause: must assign this literal to true
                lit = unassigned[0]
                var = abs(lit)
                assignment[var] = (lit > 0)
                changed = True

    return clauses, assignment


def is_satisfied(clauses, assignment):
    """Check if all clauses are satisfied by the current assignment."""
    for clause in clauses:
        clause_satisfied = False
        for lit in clause:
            var = abs(lit)
            if var in assignment:
                if (lit > 0 and assignment[var]) or (lit < 0 and not assignment[var]):
                    clause_satisfied = True
                    break
        if not clause_satisfied:
            return False
    return True


def has_conflict(clauses, assignment):
    """Check if any clause is falsified (all literals assigned false)."""
    for clause in clauses:
        all_false = True
        for lit in clause:
            var = abs(lit)
            if var not in assignment:
                all_false = False
                break
            if (lit > 0 and assignment[var]) or (lit < 0 and not assignment[var]):
                all_false = False
                break
        if all_false:
            return True
    return False


def get_unassigned_var(clauses, assignment, n):
    """Get the next unassigned variable (simple heuristic: first unassigned)."""
    for var in range(1, n + 1):
        if var not in assignment:
            return var
    return None


def solve(clauses, n=None):
    """
    Solve a 3-CNF-SAT instance using DPLL backtracking search.

    Args:
        clauses: List of clauses (each clause is a list of 3 literals)
        n: Number of variables (if None, inferred from clauses)

    Returns:
        True if satisfiable, False otherwise
    """
    if n is None:
        n = max(abs(lit) for clause in clauses for lit in clause)

    def dpll(assignment):
        # Apply unit propagation
        new_assignment = assignment.copy()
        _, new_assignment = unit_propagate(clauses, new_assignment)

        if new_assignment is None:
            return False  # Conflict detected

        # Check if all clauses are satisfied
        if is_satisfied(clauses, new_assignment):
            return True

        # Check for conflicts
        if has_conflict(clauses, new_assignment):
            return False

        # Choose an unassigned variable
        var = get_unassigned_var(clauses, new_assignment, n)
        if var is None:
            return is_satisfied(clauses, new_assignment)

        # Try assigning True
        new_assignment[var] = True
        if dpll(new_assignment):
            return True

        # Try assigning False
        new_assignment = assignment.copy()
        _, new_assignment = unit_propagate(clauses, new_assignment)
        if new_assignment is None:
            return False
        new_assignment[var] = False
        if dpll(new_assignment):
            return True

        return False

    return dpll({})


def run_experiment(n=100, m_values=None, trials=25):
    """
    Run the phase transition experiment.

    Args:
        n: Number of variables
        m_values: List of clause-to-variable ratios to test
        trials: Number of trials per m value

    Returns:
        Dictionary mapping m values to fraction of satisfiable instances
    """
    if m_values is None:
        m_values = [1.0 + 0.25 * i for i in range(29)]  # 1.0 to 8.0 in 0.25 steps

    results = {}

    for m in m_values:
        satisfiable_count = 0
        for trial in range(trials):
            instance = generate(n, m)
            if solve(instance, n):
                satisfiable_count += 1

        fraction = satisfiable_count / trials
        results[m] = fraction
        print(f"m = {m:.2f}: {satisfiable_count}/{trials} satisfiable ({fraction:.2%})")

    return results


def plot_results(results):
    """Plot the phase transition graph."""
    m_values = sorted(results.keys())
    fractions = [results[m] for m in m_values]

    plt.figure(figsize=(10, 6))
    plt.plot(m_values, fractions, 'b-o', linewidth=2, markersize=6)
    plt.xlabel('Clause-to-Variable Ratio (m)', fontsize=12)
    plt.ylabel('Fraction Satisfiable', fontsize=12)
    plt.title('3-CNF-SAT Phase Transition (n=100 variables)', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.axhline(y=0.5, color='r', linestyle='--', alpha=0.5, label='50% threshold')
    plt.legend()
    plt.tight_layout()
    plt.savefig('phase_transition.png', dpi=150)
    plt.show()
    print("\nPlot saved as 'phase_transition.png'")


def test_generator():
    """Test the generator with small instances."""
    print("=" * 50)
    print("Testing Generator")
    print("=" * 50)

    # Test 1: Check clause count
    instance = generate(10, 3)
    assert len(instance) == 30, f"Expected 30 clauses, got {len(instance)}"
    print("✓ Correct number of clauses generated")

    # Test 2: Check each clause has 3 literals
    for clause in instance:
        assert len(clause) == 3, f"Expected 3 literals, got {len(clause)}"
    print("✓ Each clause has exactly 3 literals")

    # Test 3: Check variables are in valid range
    for clause in instance:
        for lit in clause:
            assert 1 <= abs(lit) <= 10, f"Variable {abs(lit)} out of range"
    print("✓ All variables in valid range")

    print("\nSample instance (n=5, m=2):")
    sample = generate(5, 2)
    for i, clause in enumerate(sample):
        literals = []
        for lit in clause:
            if lit > 0:
                literals.append(f"x{lit}")
            else:
                literals.append(f"¬x{abs(lit)}")
        print(f"  Clause {i+1}: ({' ∨ '.join(literals)})")


def test_solver():
    """Test the solver with known instances."""
    print("\n" + "=" * 50)
    print("Testing Solver")
    print("=" * 50)

    # Test 1: Simple satisfiable instance
    # (x1 OR x2 OR x3) - satisfiable with x1=True
    clauses = [[1, 2, 3]]
    assert solve(clauses, 3) == True, "Should be satisfiable"
    print("✓ Simple satisfiable instance")

    # Test 2: Unsatisfiable instance
    # (x1) AND (¬x1) - requires x1=True AND x1=False
    clauses = [[1, 1, 1], [-1, -1, -1]]
    assert solve(clauses, 1) == False, "Should be unsatisfiable"
    print("✓ Simple unsatisfiable instance")

    # Test 3: More complex satisfiable
    # (x1 OR x2 OR x3) AND (¬x1 OR x2 OR x3) - satisfiable with x2=True
    clauses = [[1, 2, 3], [-1, 2, 3]]
    assert solve(clauses, 3) == True, "Should be satisfiable"
    print("✓ Complex satisfiable instance")

    # Test 4: Random small instances (smoke test)
    for _ in range(10):
        instance = generate(10, 2)
        result = solve(instance, 10)
        assert result in [True, False], "Solver should return boolean"
    print("✓ Random instances complete without error")


if __name__ == '__main__':
    # Run tests first
    test_generator()
    test_solver()

    print("\n" + "=" * 50)
    print("Running Phase Transition Experiment")
    print("=" * 50)
    print("n = 100 variables")
    print("m = 1.0 to 8.0 (step 0.25)")
    print("25 trials per m value")
    print("=" * 50 + "\n")

    results = run_experiment(n=100, trials=25)
    plot_results(results)
