# Blackjack Genetic Algorithm Solver — Design Specification

## Problem Summary

Evolve a blackjack playing strategy using a genetic algorithm. The strategy
encodes hit/stand decisions for every combination of player hand and dealer
up-card. Fitness is measured by simulating thousands of hands. Over many
generations the population should converge toward a strategy that approaches
the theoretical optimum (~49.5% win rate) and closely matches known basic
strategy tables.

## Output Deliverables

1. **`blackjack_ga.py`** — single self-contained Python file producing both
   figures when run.
2. **Figure 1** — Line plot of min/max/mean/median fitness vs. generation.
3. **Figure 2** — Heatmap of the final-population consensus strategy (% hit)
   for hard and soft hands, colored red (hit) to blue (stand).

---

## Blackjack Simulation Engine

### Deck and Cards

- Standard 52-card deck, freshly shuffled before every hand.
- Card values: 2–9 face value; 10/J/Q/K = 10; Ace = 1 or 11.
- Represent a deck as a list of integer values
  `[2,3,...,10,10,10,10,11] × 4`, shuffled with `random.shuffle`.
- Draw from the end of the list (`deck.pop()`).

### Hand Scoring

```
def hand_value(cards):
    total = sum(cards)
    aces = cards.count(11)
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total, (aces > 0)        # (score, is_soft)
```

`is_soft` is True when at least one ace is still counted as 11. This flag
determines which section of the strategy chromosome to consult.

### Dealing

1. Shuffle a fresh 52-card deck.
2. Deal: player card, dealer card (face-up), player card, dealer card
   (face-down).

### Player Turn

Loop until the player stands or busts:

1. Compute `(total, is_soft)` for the player hand.
2. If `total >= 21`: stop (21 = stand; >21 = bust).
3. Look up the strategy bit for `(total, is_soft, dealer_up_card)`.
   - `1` → Hit: draw a card, repeat.
   - `0` → Stand: stop.

### Dealer Turn

Dealer plays by fixed house rules (no strategy lookup):

1. Compute `(total, is_soft)`.
2. If `total < 17`: hit.
3. If `total == 17` and `is_soft`: **stand** (dealer stands on soft 17).
4. If `total >= 17`: stand.
5. If `total > 21`: bust.

### Outcome

| Condition | Result |
|-----------|--------|
| Player busts | Loss |
| Dealer busts (player didn't) | Win |
| Player total > Dealer total | Win |
| Player total < Dealer total | Loss |
| Player total == Dealer total | Push (tie) |

Natural blackjack (two-card 21) is treated as a normal win — no 3:2 payout
distinction is needed since we only track win/loss/push.

---

## Strategy Encoding (Chromosome)

A strategy is a **260-bit binary vector** stored as a Python `list[int]` of
0s and 1s.

### Hard-hand region — bits 0–169 (170 bits)

| Parameter | Range | Count |
|-----------|-------|-------|
| Player total | 4 – 20 | 17 |
| Dealer up-card | A, 2–10 | 10 |

**Bit index** for a hard hand:

```
idx = (player_total - 4) * 10 + dealer_index
```

### Soft-hand region — bits 170–259 (90 bits)

| Parameter | Range | Count |
|-----------|-------|-------|
| Player total | 12 – 20 (soft) | 9 |
| Dealer up-card | A, 2–10 | 10 |

**Bit index** for a soft hand:

```
idx = 170 + (player_total - 12) * 10 + dealer_index
```

### Dealer card indexing

| Card | Index |
|------|-------|
| Ace | 0 |
| 2 | 1 |
| 3 | 2 |
| ... | ... |
| 10 | 9 |

### Bit values

- `1` = Hit
- `0` = Stand

### Edge cases

- Player total ≤ 11 (hard): always hit regardless of strategy bit, since
  hitting cannot bust. We still store these bits in the chromosome (they are
  part of the evolvable genome) but the simulation can short-circuit hitting
  for totals ≤ 11 for efficiency. **Design decision**: let the GA discover
  this on its own — don't hard-code the short-circuit. This keeps the
  chromosome fully general and lets us verify the GA learns to always hit
  low totals.
- Player total = 21: always stand (loop exits before consulting strategy).

---

## Fitness Function

```
fitness(strategy) = (wins + 0.5 × ties) / total_hands
```

- Simulate **1,000 hands** per individual per generation.
- Each hand uses a freshly shuffled single deck.
- Returns a float in [0, 1].

---

## Genetic Algorithm

### Parameters

| Parameter | Value |
|-----------|-------|
| Population size | 100 |
| Chromosome length | 260 bits |
| Generations | 100 |
| Hands per fitness eval | 1,000 |
| Selection method | Roulette wheel (fitness-proportionate) |
| Crossover | Single-point |
| Crossover rate | 1.0 (always cross selected pairs) |
| Mutation rate | 0.01 per bit |
| Elitism | Top 2 individuals pass unchanged |

### Initialization

Generate 100 random chromosomes. Each bit is independently set to 0 or 1
with equal probability using `random.randint(0, 1)`.

### Selection — Roulette Wheel

1. Compute cumulative fitness distribution:
   `cumulative[i] = sum(fitness[0..i])`.
2. To select one parent: generate `r = random.uniform(0, total_fitness)`,
   binary-search (or linear scan) for the first index where `cumulative[i] >= r`.
3. Select **98 parents** (to fill population minus 2 elites), paired
   sequentially for crossover → 49 pairs → 98 offspring.

### Crossover — Single-Point

For each pair of parents (P1, P2):

1. Choose crossover point `c = random.randint(1, 259)`.
2. Child 1 = `P1[:c] + P2[c:]`
3. Child 2 = `P2[:c] + P1[c:]`

### Mutation

For each offspring chromosome, flip each bit independently with probability
0.01:

```
for i in range(260):
    if random.random() < 0.01:
        chromosome[i] ^= 1
```

Expected mutations per chromosome: 2.6 bits.

### Elitism

Sort population by fitness. The top 2 individuals are copied unchanged into
the next generation.

### Generation Loop

```
for gen in range(num_generations):
    fitnesses = [evaluate(individual) for individual in population]
    record_stats(gen, fitnesses)
    elite = top_2(population, fitnesses)
    parents = roulette_select(population, fitnesses, count=98)
    offspring = crossover_pairs(parents)
    mutate(offspring)
    population = elite + offspring
```

---

## Visualization

### Figure 1 — Fitness Over Generations

- **X-axis**: Generation (0 to N-1)
- **Y-axis**: Fitness (win rate)
- **Lines**: min, max, mean, median — four lines, each labeled in a legend.
- **Library**: `matplotlib.pyplot`
- Expected behavior: max fitness rises toward ~0.49–0.50; min rises and
  variance shrinks as the population converges.

### Figure 2 — Strategy Consensus Heatmap

For the **final generation's population**, compute the percentage of
individuals that recommend hitting for each (player_total, dealer_card)
combination.

Two sub-heatmaps side by side or stacked:

**Hard hands** (17 rows × 10 columns):
- Rows: player total 4–20 (top to bottom: 20 → 4, matching standard tables)
- Columns: dealer up-card A, 2–10

**Soft hands** (9 rows × 10 columns):
- Rows: player total soft 12–20
- Columns: dealer up-card A, 2–10

**Color scale**:
- 100% hit → pure red
- 100% stand → pure blue
- 50% → purple (midpoint blend)
- Use `matplotlib` colormap `RdBu_r` (red = high, blue = low) or build a
  custom `LinearSegmentedColormap` from blue→red.

**Annotations**: Print the hit-percentage value in each cell (rounded to
nearest integer).

**Library**: `matplotlib.pyplot.imshow` or `seaborn.heatmap`.

---

## Implementation Plan

### Step 1 — Card utilities
- `make_deck()` → shuffled list of 52 card values
- `hand_value(cards)` → `(total, is_soft)`

### Step 2 — Strategy lookup
- `strategy_lookup(chromosome, player_total, is_soft, dealer_up)` → bool
  (True = hit)

### Step 3 — Simulate one hand
- `play_hand(chromosome)` → `'win' | 'loss' | 'push'`
- Deals from fresh deck, plays player turn using strategy, plays dealer
  turn by house rules, returns outcome.

### Step 4 — Fitness evaluation
- `evaluate(chromosome, n_hands=1000)` → float
- Plays `n_hands` hands, returns win-rate.

### Step 5 — GA operators
- `init_population(pop_size, chrom_len)` → list of chromosomes
- `roulette_select(population, fitnesses, count)` → list of parents
- `crossover(p1, p2)` → (child1, child2)
- `mutate(chromosome, rate)` → mutated chromosome (in-place)

### Step 6 — Main evolution loop
- Track per-generation stats: min, max, mean, median fitness.
- Apply elitism, selection, crossover, mutation each generation.
- Print progress (generation number, best fitness) to stdout.

### Step 7 — Visualization
- Plot fitness curves (Figure 1).
- Compute consensus matrix from final population, render heatmaps (Figure 2).

---

## Data Structures Summary

| Component | Structure |
|-----------|-----------|
| Deck | `list[int]` — 52 card values, shuffled |
| Hand | `list[int]` — variable-length list of card values |
| Chromosome | `list[int]` — 260 elements, each 0 or 1 |
| Population | `list[list[int]]` — 100 chromosomes |
| Fitness array | `list[float]` — 100 values per generation |
| Stats history | `dict[str, list[float]]` — keys: min, max, mean, median |
| Consensus matrix (hard) | `numpy.ndarray` shape (17, 10) — percent hit |
| Consensus matrix (soft) | `numpy.ndarray` shape (9, 10) — percent hit |

## Dependencies

- `random` (stdlib) — shuffling, selection, mutation
- `numpy` — consensus matrix computation
- `matplotlib` — both figures

No external packages beyond the Python standard library + numpy + matplotlib.

---

## Expected Results

- **Fitness convergence**: Best individual should reach ~0.48–0.50 win rate
  within 50–100 generations. Mean fitness should climb from ~0.40 (random
  strategy) toward ~0.46–0.48.
- **Strategy consensus**: The final heatmap should broadly match the Wizard
  of Odds basic strategy table — stand on 17+, hit on low totals, stand
  against weak dealer cards (4–6) with mid-range totals (12–16), hit soft
  hands more aggressively.
- **Runtime**: 100 individuals × 1,000 hands × 100 generations =
  10,000,000 simulated hands. Each hand is lightweight (~microseconds), so
  total runtime should be on the order of 1-3 minutes in pure Python. Can
  be optimized with numpy vectorization if needed, but likely unnecessary.
