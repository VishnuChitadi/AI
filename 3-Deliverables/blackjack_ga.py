"""
Blackjack Genetic Algorithm Solver

Evolves a hit/stand strategy for single-deck blackjack using a genetic
algorithm.  Each individual is a 260-bit chromosome encoding decisions for
every (player_total, dealer_up_card) combination across hard and soft hands.

Produces two figures:
  1. Fitness (win-rate) over generations  (min / max / mean / median)
  2. Heatmap of the final-population consensus strategy (% hit)
"""

import random
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CHROM_LEN = 260          # 170 hard + 90 soft
HARD_BITS = 170          # player 4-20 (17) x dealer A-10 (10)
POP_SIZE = 100
GENERATIONS = 100
HANDS_PER_EVAL = 1000
MUTATION_RATE = 0.01
ELITE_COUNT = 2

# ---------------------------------------------------------------------------
# Card / hand utilities
# ---------------------------------------------------------------------------
BASE_DECK = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11] * 4  # 52 cards


def make_deck():
    deck = BASE_DECK[:]
    random.shuffle(deck)
    return deck


def hand_value(cards):
    """Return (total, is_soft).  Soft means at least one ace counts as 11."""
    total = sum(cards)
    aces = cards.count(11)
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total, aces > 0


def dealer_card_index(card):
    """Map card value to column index 0-9.  Ace(11)->0, 2->1, ..., 10->9."""
    return 0 if card == 11 else card - 1

# ---------------------------------------------------------------------------
# Strategy chromosome interface
# ---------------------------------------------------------------------------

def strategy_hit(chromosome, player_total, is_soft, dealer_up):
    """Return True if the strategy says to hit."""
    d = dealer_card_index(dealer_up)
    if is_soft and 12 <= player_total <= 20:
        return chromosome[HARD_BITS + (player_total - 12) * 10 + d] == 1
    if 4 <= player_total <= 20:
        return chromosome[(player_total - 4) * 10 + d] == 1
    return True  # should not happen in practice

# ---------------------------------------------------------------------------
# Blackjack simulation
# ---------------------------------------------------------------------------

def play_hand(chromosome):
    """Simulate one hand.  Returns 'win', 'loss', or 'push'."""
    deck = make_deck()

    # Deal: player, dealer(up), player, dealer(down)
    player = [deck.pop()]
    dealer_up_card = deck.pop()
    player.append(deck.pop())
    dealer = [dealer_up_card, deck.pop()]

    # --- Player turn ---
    while True:
        total, soft = hand_value(player)
        if total >= 21:
            break
        if strategy_hit(chromosome, total, soft, dealer_up_card):
            player.append(deck.pop())
        else:
            break

    player_total, _ = hand_value(player)
    if player_total > 21:
        return "loss"

    # --- Dealer turn (stand on soft 17) ---
    while True:
        total, soft = hand_value(dealer)
        if total >= 17:
            break
        dealer.append(deck.pop())

    dealer_total, _ = hand_value(dealer)
    if dealer_total > 21:
        return "win"

    if player_total > dealer_total:
        return "win"
    if player_total < dealer_total:
        return "loss"
    return "push"


def evaluate(chromosome, n_hands=HANDS_PER_EVAL):
    """Fitness = (wins + 0.5*ties) / n_hands."""
    wins = 0
    ties = 0
    for _ in range(n_hands):
        result = play_hand(chromosome)
        if result == "win":
            wins += 1
        elif result == "push":
            ties += 1
    return (wins + 0.5 * ties) / n_hands

# ---------------------------------------------------------------------------
# Genetic algorithm operators
# ---------------------------------------------------------------------------

def init_population(size, length):
    return [[random.randint(0, 1) for _ in range(length)] for _ in range(size)]


def roulette_select(population, fitnesses, count):
    """Fitness-proportionate (roulette wheel) selection with windowing.

    Subtracts the population minimum so the worst individual has near-zero
    selection probability.  This dramatically increases selection pressure
    when raw fitness values are clustered (e.g. 0.35-0.50).
    """
    floor = min(fitnesses) - 1e-6  # small epsilon avoids all-zero weights
    weights = [f - floor for f in fitnesses]
    total = sum(weights)
    cumulative = []
    running = 0.0
    for w in weights:
        running += w
        cumulative.append(running)

    selected = []
    for _ in range(count):
        r = random.uniform(0, total)
        for i, c in enumerate(cumulative):
            if c >= r:
                selected.append(population[i][:])
                break
    return selected


def crossover(p1, p2):
    """Single-point crossover returning two children."""
    point = random.randint(1, len(p1) - 1)
    return p1[:point] + p2[point:], p2[:point] + p1[point:]


def mutate(chromosome, rate=MUTATION_RATE):
    """Flip each bit independently with probability `rate`."""
    for i in range(len(chromosome)):
        if random.random() < rate:
            chromosome[i] ^= 1

# ---------------------------------------------------------------------------
# Main evolution loop
# ---------------------------------------------------------------------------

def run_ga():
    population = init_population(POP_SIZE, CHROM_LEN)
    stats = {"min": [], "max": [], "mean": [], "median": []}

    for gen in range(GENERATIONS):
        fitnesses = [evaluate(ind) for ind in population]

        stats["min"].append(min(fitnesses))
        stats["max"].append(max(fitnesses))
        stats["mean"].append(float(np.mean(fitnesses)))
        stats["median"].append(float(np.median(fitnesses)))

        print(
            f"Gen {gen:3d}  |  best {max(fitnesses):.4f}  "
            f"mean {np.mean(fitnesses):.4f}  min {min(fitnesses):.4f}"
        )

        # Elitism
        ranked = sorted(range(POP_SIZE), key=lambda i: fitnesses[i], reverse=True)
        elite = [population[ranked[i]][:] for i in range(ELITE_COUNT)]

        # Selection
        parents = roulette_select(population, fitnesses, POP_SIZE - ELITE_COUNT)

        # Crossover (pair consecutive parents)
        offspring = []
        for i in range(0, len(parents) - 1, 2):
            c1, c2 = crossover(parents[i], parents[i + 1])
            offspring.append(c1)
            offspring.append(c2)
        if len(parents) % 2 == 1:
            offspring.append(parents[-1][:])

        # Mutation
        for ind in offspring:
            mutate(ind)

        population = elite + offspring

    # Final evaluation
    fitnesses = [evaluate(ind) for ind in population]
    return population, fitnesses, stats

# ---------------------------------------------------------------------------
# Visualization
# ---------------------------------------------------------------------------

def plot_fitness(stats):
    fig, ax = plt.subplots(figsize=(10, 6))
    gens = range(len(stats["max"]))
    ax.plot(gens, stats["max"], label="Max", color="green")
    ax.plot(gens, stats["mean"], label="Mean", color="blue")
    ax.plot(gens, stats["median"], label="Median", color="orange")
    ax.plot(gens, stats["min"], label="Min", color="red")
    ax.set_xlabel("Generation")
    ax.set_ylabel("Fitness (Win Rate)")
    ax.set_title("Blackjack GA: Fitness Over Generations")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig("3-Deliverables/fitness_plot.png", dpi=150)
    print("Saved fitness_plot.png")
    plt.close(fig)


def plot_strategy_heatmap(population):
    n = len(population)

    # Tally how many individuals hit in each cell
    hard = np.zeros((17, 10))
    soft = np.zeros((9, 10))
    for chrom in population:
        for t in range(17):
            for d in range(10):
                hard[t, d] += chrom[t * 10 + d]
        for t in range(9):
            for d in range(10):
                soft[t, d] += chrom[HARD_BITS + t * 10 + d]
    hard = hard / n * 100
    soft = soft / n * 100

    # Row labels: high totals at top
    hard_rows = [str(i) for i in range(20, 3, -1)]
    soft_rows = [str(i) for i in range(20, 11, -1)]
    col_labels = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10"]

    hard_disp = hard[::-1]
    soft_disp = soft[::-1]

    fig = plt.figure(figsize=(20, 10))
    gs = fig.add_gridspec(1, 3, width_ratios=[17, 9, 0.8], wspace=0.35)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    cax = fig.add_subplot(gs[0, 2])

    # Hard hands
    im1 = ax1.imshow(hard_disp, cmap="RdBu_r", vmin=0, vmax=100, aspect="auto")
    ax1.set_xticks(range(10))
    ax1.set_xticklabels(col_labels)
    ax1.set_yticks(range(17))
    ax1.set_yticklabels(hard_rows)
    ax1.set_xlabel("Dealer Up Card")
    ax1.set_ylabel("Player Total")
    ax1.set_title("Hard Hands (% Hit)")
    for i in range(17):
        for j in range(10):
            v = hard_disp[i, j]
            color = "white" if 20 < v < 80 else "black"
            ax1.text(j, i, f"{v:.0f}", ha="center", va="center",
                     fontsize=8, fontweight="bold", color=color)

    # Soft hands
    ax2.imshow(soft_disp, cmap="RdBu_r", vmin=0, vmax=100, aspect="auto")
    ax2.set_xticks(range(10))
    ax2.set_xticklabels(col_labels)
    ax2.set_yticks(range(9))
    ax2.set_yticklabels(soft_rows)
    ax2.set_xlabel("Dealer Up Card")
    ax2.set_ylabel("Player Total (Soft)")
    ax2.set_title("Soft Hands (% Hit)")
    for i in range(9):
        for j in range(10):
            v = soft_disp[i, j]
            color = "white" if 20 < v < 80 else "black"
            ax2.text(j, i, f"{v:.0f}", ha="center", va="center",
                     fontsize=8, fontweight="bold", color=color)

    fig.colorbar(im1, cax=cax, label="% Hit")
    fig.suptitle("Evolved Blackjack Strategy (Final Generation)", fontsize=14, y=0.98)
    fig.savefig("3-Deliverables/strategy_heatmap.png", dpi=150, bbox_inches="tight")
    print("Saved strategy_heatmap.png")
    plt.close(fig)

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    random.seed(42)
    np.random.seed(42)

    population, fitnesses, stats = run_ga()

    best_idx = max(range(len(fitnesses)), key=lambda i: fitnesses[i])
    print(f"\nBest final fitness: {fitnesses[best_idx]:.4f}")

    plot_fitness(stats)
    plot_strategy_heatmap(population)
