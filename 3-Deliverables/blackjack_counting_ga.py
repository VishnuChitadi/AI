"""
Blackjack Card Counting GA Solver

Extends the basic blackjack GA to evolve a card counting system and
variable-bet strategy.  Hands are dealt from a 6-deck shoe with 75%
penetration.  The chromosome encodes hit/stand decisions (260 bits),
card count values (22 bits), and bet multipliers (12 bits) = 294 bits.

Produces:
  1. Fitness (final bankroll) over generations  (min / max / mean / median)
  2. Strategy consensus heatmap  (hard + soft hands, % hit)
  3. Evolved count values vs. Hi-Lo reference
  4. Evolved bet multipliers table
  5. Bankroll trajectory for the best individual
"""

import random
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
# Chromosome layout
PLAY_BITS = 260          # bits 0-259: play strategy (same as basic)
HARD_BITS = 170          # bits 0-169: hard hands
COUNT_OFFSET = 260       # bits 260-281: card count values (11 slots × 2 bits)
COUNT_BITS = 22
BET_OFFSET = 282         # bits 282-293: bet multipliers (4 ranges × 3 bits)
BET_BITS = 12
CHROM_LEN = PLAY_BITS + COUNT_BITS + BET_BITS  # 294

# Shoe
NUM_DECKS = 6
SHOE_SIZE = 52 * NUM_DECKS                     # 312
PENETRATION = int(SHOE_SIZE * 0.75)            # 234

# Bankroll / betting
STARTING_BANKROLL = 1000
MIN_BET = 1
MAX_BET = 8

# GA
POP_SIZE = 100
GENERATIONS = 100
HANDS_PER_EVAL = 1000
MUTATION_RATE = 0.01
ELITE_COUNT = 2

# Hi-Lo reference (for display)
HILO = {11: -1, 2: +1, 3: +1, 4: +1, 5: +1, 6: +1, 7: 0, 8: 0, 9: 0, 10: -1}

# True count range boundaries
TC_RANGES = ["<= -2", "-1 to +1", "+2 to +4", ">= +5"]

BASE_DECK = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11] * 4  # single deck

# ---------------------------------------------------------------------------
# Card / hand utilities
# ---------------------------------------------------------------------------

def make_shoe():
    shoe = BASE_DECK * NUM_DECKS
    random.shuffle(shoe)
    return shoe


def hand_value(cards):
    """Return (total, is_soft)."""
    total = sum(cards)
    aces = cards.count(11)
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total, aces > 0


def dealer_card_index(card):
    """Ace(11)->0, 2->1, ..., 10->9."""
    return 0 if card == 11 else card - 1

# ---------------------------------------------------------------------------
# Chromosome decoding
# ---------------------------------------------------------------------------

def strategy_hit(chromosome, player_total, is_soft, dealer_up):
    """Return True if strategy says hit (same indexing as basic version)."""
    d = dealer_card_index(dealer_up)
    if is_soft and 12 <= player_total <= 20:
        return chromosome[HARD_BITS + (player_total - 12) * 10 + d] == 1
    if 4 <= player_total <= 20:
        return chromosome[(player_total - 4) * 10 + d] == 1
    return True


def decode_count_table(chromosome):
    """Return dict mapping card value -> count value (-1, 0, or +1)."""
    table = {}
    # 11 slots: Ace, 2, 3, ..., 10  (index 0-9 used, index 10 is padding)
    card_values = [11, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    for i, cv in enumerate(card_values):
        b1 = chromosome[COUNT_OFFSET + i * 2]
        b0 = chromosome[COUNT_OFFSET + i * 2 + 1]
        code = b1 * 2 + b0
        if code == 0:    # 00
            table[cv] = -1
        elif code == 2:  # 10
            table[cv] = +1
        else:            # 01 or 11
            table[cv] = 0
    return table


def decode_bet_table(chromosome):
    """Return list of 4 multipliers (1-8), one per true-count range."""
    mults = []
    for i in range(4):
        base = BET_OFFSET + i * 3
        b2 = chromosome[base]
        b1 = chromosome[base + 1]
        b0 = chromosome[base + 2]
        mults.append(b2 * 4 + b1 * 2 + b0 + 1)
    return mults


def get_true_count(running_count, remaining_cards):
    decks_remaining = remaining_cards / 52.0
    if decks_remaining < 0.5:
        decks_remaining = 0.5
    return round(running_count / decks_remaining)


def get_bet(true_count, bet_table, bankroll):
    if true_count <= -2:
        mult = bet_table[0]
    elif true_count <= 1:
        mult = bet_table[1]
    elif true_count <= 4:
        mult = bet_table[2]
    else:
        mult = bet_table[3]
    bet = max(MIN_BET, min(MAX_BET, mult))
    return min(bet, bankroll)

# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def is_natural(cards):
    """True if hand is a two-card 21 (natural blackjack)."""
    return len(cards) == 2 and sum(cards) == 21


def simulate_session(chromosome, n_hands=HANDS_PER_EVAL, track_bankroll=False):
    """Play up to n_hands from 6-deck shoes.

    Returns final bankroll.  If track_bankroll is True, also returns a list
    of bankroll values after each hand (for plotting).
    """
    count_table = decode_count_table(chromosome)
    bet_table = decode_bet_table(chromosome)

    bankroll = STARTING_BANKROLL
    running_count = 0
    shoe = make_shoe()
    history = [bankroll] if track_bankroll else None

    for _ in range(n_hands):
        if bankroll <= 0:
            break

        # Reshuffle if penetration reached
        if SHOE_SIZE - len(shoe) >= PENETRATION:
            shoe = make_shoe()
            running_count = 0

        # Need at least ~10 cards for a hand to be safe
        if len(shoe) < 10:
            shoe = make_shoe()
            running_count = 0

        # Determine bet
        tc = get_true_count(running_count, len(shoe))
        bet = get_bet(tc, bet_table, bankroll)

        # Deal: player, dealer(up), player, dealer(down)
        p1 = shoe.pop()
        d_up = shoe.pop()
        p2 = shoe.pop()
        d_down = shoe.pop()

        player = [p1, p2]
        dealer = [d_up, d_down]

        # Count visible cards (player cards + dealer up card)
        running_count += count_table.get(p1, 0)
        running_count += count_table.get(d_up, 0)
        running_count += count_table.get(p2, 0)
        # Dealer hole card not yet visible

        # --- Player turn ---
        while True:
            total, soft = hand_value(player)
            if total >= 21:
                break
            if strategy_hit(chromosome, total, soft, d_up):
                card = shoe.pop()
                player.append(card)
                running_count += count_table.get(card, 0)
            else:
                break

        player_total, _ = hand_value(player)

        # Reveal dealer hole card
        running_count += count_table.get(d_down, 0)

        if player_total > 21:
            # Player busts
            bankroll -= bet
        else:
            # --- Dealer turn ---
            while True:
                total, soft = hand_value(dealer)
                if total >= 17:
                    break
                card = shoe.pop()
                dealer.append(card)
                running_count += count_table.get(card, 0)

            dealer_total, _ = hand_value(dealer)

            # Determine outcome
            if dealer_total > 21:
                # Dealer busts
                if is_natural(player):
                    bankroll += int(bet * 1.5)
                else:
                    bankroll += bet
            elif player_total > dealer_total:
                if is_natural(player):
                    bankroll += int(bet * 1.5)
                else:
                    bankroll += bet
            elif player_total < dealer_total:
                bankroll -= bet
            # else: push, no change

        if track_bankroll:
            history.append(bankroll)

    if track_bankroll:
        return bankroll, history
    return bankroll


def evaluate(chromosome, n_hands=HANDS_PER_EVAL):
    return simulate_session(chromosome, n_hands)

# ---------------------------------------------------------------------------
# Genetic algorithm operators
# ---------------------------------------------------------------------------

def init_population(size, length):
    return [[random.randint(0, 1) for _ in range(length)] for _ in range(size)]


def roulette_select(population, fitnesses, count):
    """Fitness-proportionate selection with windowing."""
    floor = min(fitnesses) - 1e-6
    weights = [f - floor for f in fitnesses]
    total = sum(weights)
    if total == 0:
        return [random.choice(population)[:] for _ in range(count)]
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
    point = random.randint(1, len(p1) - 1)
    return p1[:point] + p2[point:], p2[:point] + p1[point:]


def mutate(chromosome, rate=MUTATION_RATE):
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
            f"Gen {gen:3d}  |  best ${max(fitnesses):>6.0f}  "
            f"mean ${np.mean(fitnesses):>7.1f}  min ${min(fitnesses):>6.0f}"
        )

        # Elitism
        ranked = sorted(range(POP_SIZE), key=lambda i: fitnesses[i], reverse=True)
        elite = [population[ranked[i]][:] for i in range(ELITE_COUNT)]

        # Selection
        parents = roulette_select(population, fitnesses, POP_SIZE - ELITE_COUNT)

        # Crossover
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
    ax.set_ylabel("Final Bankroll ($)")
    ax.set_title("Card Counting GA: Fitness Over Generations")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig("3-Deliverables/counting_fitness_plot.png", dpi=150)
    print("Saved counting_fitness_plot.png")
    plt.close(fig)


def plot_strategy_heatmap(population):
    n = len(population)
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
    fig.suptitle("Evolved Blackjack Strategy — Card Counting (Final Generation)",
                 fontsize=14, y=0.98)
    fig.savefig("3-Deliverables/counting_strategy_heatmap.png", dpi=150,
                bbox_inches="tight")
    print("Saved counting_strategy_heatmap.png")
    plt.close(fig)


def print_count_table(chromosome):
    """Print evolved count values vs Hi-Lo reference."""
    count_table = decode_count_table(chromosome)
    card_names = ["Ace", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
    card_values = [11, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    print("\n--- Evolved Count Values vs. Hi-Lo ---")
    print(f"{'Card':>6}  {'Evolved':>8}  {'Hi-Lo':>6}")
    print("-" * 26)
    for name, cv in zip(card_names, card_values):
        evolved = count_table[cv]
        hilo = HILO[cv]
        marker = "  *" if evolved == hilo else ""
        sign_e = "+" if evolved > 0 else ""
        sign_h = "+" if hilo > 0 else ""
        print(f"{name:>6}  {sign_e}{evolved:>7}  {sign_h}{hilo:>5}{marker}")


def print_bet_table(chromosome):
    """Print evolved bet multipliers."""
    bet_table = decode_bet_table(chromosome)
    print("\n--- Evolved Bet Multipliers ---")
    print(f"{'True Count Range':>16}  {'Multiplier ($)':>14}")
    print("-" * 34)
    for label, mult in zip(TC_RANGES, bet_table):
        print(f"{label:>16}  {'$' + str(mult):>14}")


def plot_bankroll_trajectory(chromosome):
    """Plot bankroll over a sample 1000-hand session for one individual."""
    _, history = simulate_session(chromosome, HANDS_PER_EVAL, track_bankroll=True)
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(range(len(history)), history, color="steelblue", linewidth=1)
    ax.axhline(y=STARTING_BANKROLL, color="gray", linestyle="--", alpha=0.7,
               label=f"Starting (${STARTING_BANKROLL})")
    ax.set_xlabel("Hand Number")
    ax.set_ylabel("Bankroll ($)")
    ax.set_title("Bankroll Over 1,000 Hands (Best Individual)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig("3-Deliverables/counting_bankroll_trajectory.png", dpi=150)
    print("Saved counting_bankroll_trajectory.png")
    plt.close(fig)

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    random.seed(42)
    np.random.seed(42)

    population, fitnesses, stats = run_ga()

    best_idx = max(range(len(fitnesses)), key=lambda i: fitnesses[i])
    best = population[best_idx]
    print(f"\nBest final bankroll: ${fitnesses[best_idx]:.0f}")

    # Outputs
    plot_fitness(stats)
    plot_strategy_heatmap(population)
    print_count_table(best)
    print_bet_table(best)
    plot_bankroll_trajectory(best)
