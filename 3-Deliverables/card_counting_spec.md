# Blackjack Card Counting GA — Design Specification

## Overview

Extend the basic blackjack GA (`blackjack_ga.py`) to evolve a card-counting
system alongside the hit/stand strategy. The player now tracks cards dealt
from a 6-deck shoe, maintains a running count, and adjusts bet sizes based
on the true count. The GA simultaneously evolves the counting system, bet
multipliers, and playing strategy.

## Changes from Basic Version

| Aspect | Basic | Card Counting |
|--------|-------|---------------|
| Deck | Single 52-card deck, reshuffled every hand | 6-deck shoe (312 cards), reshuffled at 75% penetration |
| Scoring | Win-rate (wins + 0.5×ties) / hands | Final bankroll after 1000 hands |
| Bets | Implicit $1 flat bet | $1–$8 variable bet based on true count |
| Blackjack payout | Counted as regular win | Pays 3:2 (bet of $2 wins $3) |
| Bankroll | Not tracked | Starts at $1000; bust at $0 ends session |
| Chromosome | 260 bits (play strategy) | 294 bits (play + count values + bet multipliers) |

---

## Simulation Engine

### Shoe and Dealing

- **Shoe**: 6 standard decks shuffled together = 312 cards.
- Represented as a flat list of 312 integer card values, shuffled with
  `random.shuffle`.
- Cards are drawn from the end (`shoe.pop()`).
- **Penetration**: deal until 234 cards have been dealt (75% of 312).
  When the shoe has ≤ 78 cards remaining at the *start* of a hand, complete
  the current hand, then reshuffle a fresh 6-deck shoe and reset the
  running count to 0.

```python
DECKS = 6
SHOE_SIZE = 52 * DECKS          # 312
PENETRATION = int(SHOE_SIZE * 0.75)  # 234
```

### Bankroll and Bets

- Starting bankroll: **$1000**.
- Minimum bet: **$1**. Maximum bet: **$8**.
- Bet is determined before each hand using the true count (see below).
- Bet is capped at the player's current bankroll.
- If bankroll reaches **$0**, the session ends immediately (fitness = 0).

### Hand Outcomes and Payouts

| Outcome | Payout |
|---------|--------|
| Player natural blackjack (2-card 21), dealer does not | +1.5 × bet |
| Player wins (non-blackjack) | +1 × bet |
| Push (tie) | 0 (bet returned) |
| Player loses | −1 × bet |
| Both player and dealer have natural blackjack | 0 (push) |

A "natural blackjack" is exactly two cards totaling 21 (an Ace + a
ten-valued card).

### Dealer Rules

Identical to basic version: dealer hits below 17, stands on soft 17.

### Card Visibility

All of the following cards are visible and contribute to the running count:
- Both player cards
- Dealer's face-up card (dealt second, as before)
- All hit cards (player and dealer)
- Dealer's hole card (revealed after player stands)

Cards are counted as they become visible during play.

---

## Chromosome Encoding (294 bits)

### Component 1: Play Strategy — bits 0–259 (260 bits)

Identical to the basic version.

| Region | Bits | Rows × Cols |
|--------|------|-------------|
| Hard hands (4–20 × A–10) | 0–169 | 17 × 10 |
| Soft hands (12–20 × A–10) | 170–259 | 9 × 10 |

Bit = 1 → hit, 0 → stand.

### Component 2: Card Count Values — bits 260–281 (22 bits)

Encode a count value for each of 11 card ranks using 2 bits per rank:

| Encoding | Count Value |
|----------|-------------|
| 00 | −1 |
| 01 | 0 |
| 10 | +1 |
| 11 | 0 (unused, treated as 0) |

Card rank order (11 ranks × 2 bits = 22 bits):

| Rank | Bit offset (from 260) |
|------|----------------------|
| Ace | 0–1 |
| 2 | 2–3 |
| 3 | 4–5 |
| 4 | 6–7 |
| 5 | 8–9 |
| 6 | 10–11 |
| 7 | 12–13 |
| 8 | 14–15 |
| 9 | 16–17 |
| 10 (includes J/Q/K) | 18–19 |

Wait — that's only 10 ranks × 2 bits = 20 bits. The assignment says 22 bits
for 11 values. Re-reading: "Ace, 2, 3, 4, 5, 6, 7, 8, 9, and 10" — that's
10 distinct values, but the assignment specifies 22 bits. We'll use 11 slots
(10 values + 1 padding) to match the 22-bit requirement. The 11th slot
(bits 20–21) is unused padding, always decoded as 0.

**Correction**: The assignment lists 11 card values explicitly: "Ace, 2, 3,
4, 5, 6, 7, 8, 9, and 10." That is 10 values. 10 × 2 = 20 bits. However,
the assignment states 22 bits. To be safe, we use 11 × 2 = 22 bits. The
extra 2-bit slot (index 10) is a second encoding for 10-valued cards or
simply padding decoded as 0. This does not affect correctness.

```python
COUNT_OFFSET = 260
COUNT_BITS = 22       # 11 slots × 2 bits
```

**Decoding a 2-bit pair**:
```python
def decode_count_value(b1, b0):
    code = b1 * 2 + b0
    if code == 0: return -1   # 00
    if code == 2: return +1   # 10
    return 0                  # 01 or 11
```

**Card rank to slot index**:
```python
def card_rank_index(card_value):
    # card_value: 11=Ace, 2-10
    if card_value == 11: return 0   # Ace
    return card_value - 1           # 2→1, 3→2, ..., 10→9
```

### Component 3: Bet Multipliers — bits 282–293 (12 bits)

Four 3-bit multipliers, one per true-count range. The 3-bit value (0–7)
maps to multiplier 1–8: `multiplier = bits_value + 1`.

| True Count Range | Bit offset (from 282) | Bits |
|------------------|----------------------|------|
| ≤ −2 | 0–2 | 3 |
| −1 to +1 | 3–5 | 3 |
| +2 to +4 | 6–8 | 3 |
| ≥ +5 | 9–11 | 3 |

```python
BET_OFFSET = 282
BET_BITS = 12         # 4 ranges × 3 bits
```

**Decoding a 3-bit multiplier**:
```python
def decode_bet_multiplier(b2, b1, b0):
    return b2 * 4 + b1 * 2 + b0 + 1   # 0-7 → 1-8
```

### Total Chromosome

```
[0 ............... 259 | 260 ........ 281 | 282 ...... 293]
 play strategy (260)    count values (22)   bet mults (12)

Total: 294 bits
```

---

## Card Counting Mechanics

### Running Count

Maintained as an integer, initialized to 0 at the start of each shoe.
Updated whenever a card becomes visible:

```python
running_count += count_value_for[card_rank]
```

The count persists across hands within the same shoe.

### True Count

Calculated at the start of each hand to determine the bet:

```python
remaining_cards = len(shoe)
decks_remaining = remaining_cards / 52
if decks_remaining < 0.5:
    decks_remaining = 0.5  # avoid division by tiny number
true_count = round(running_count / decks_remaining)
```

### Bet Determination

1. Compute true count.
2. Map to one of four ranges: `≤−2`, `−1 to +1`, `+2 to +4`, `≥+5`.
3. Look up the corresponding 3-bit multiplier.
4. `bet = multiplier × $1`.
5. `bet = min(bet, bankroll)`.

---

## Fitness Function

```
fitness = final_bankroll after up to 1000 hands
```

- Start with $1000.
- Play up to 1000 hands from 6-deck shoes (reshuffling at 75% penetration).
- If bankroll hits $0, stop immediately; fitness = 0.
- Fitness is the dollar amount remaining (higher is better).

Note: unlike the basic version where fitness was a 0–1 win rate, fitness
here can range from 0 to several thousand dollars depending on bet sizing
and luck. This affects selection pressure in the GA.

---

## Genetic Algorithm

### Parameters

| Parameter | Value |
|-----------|-------|
| Population size | 100 |
| Chromosome length | 294 bits |
| Generations | 100 |
| Hands per fitness eval | 1,000 |
| Selection | Roulette wheel with windowing |
| Crossover | Single-point |
| Mutation rate | 0.01 per bit |
| Elitism | Top 2 |

All GA operators (selection, crossover, mutation, elitism) work identically
to the basic version — they operate on the full 294-bit chromosome without
distinguishing between play-strategy bits, count-value bits, and bet bits.

---

## Implementation Plan

### Step 1 — Shoe utilities

- `make_shoe(n_decks=6)` → shuffled list of 312 card values.
- Reuse `hand_value()` and `dealer_card_index()` from basic version.

### Step 2 — Count and bet decoding

- `decode_count_table(chromosome)` → dict mapping card value → count value
  (−1, 0, or +1). Reads bits 260–281.
- `decode_bet_table(chromosome)` → list of 4 multipliers (1–8). Reads bits
  282–293.
- `get_true_count(running_count, remaining_cards)` → int.
- `get_bet(true_count, bet_table, bankroll)` → int ($1–$8, capped at
  bankroll).

### Step 3 — Simulate one hand (extended)

- `play_hand_counting(chromosome, shoe, running_count, bankroll,
  count_table, bet_table)` →
  `(bankroll_delta, new_running_count, cards_used)`
- Draws cards from the shared shoe (not a fresh deck).
- Updates running count as cards are revealed.
- Returns the bankroll change (+bet, −bet, +1.5×bet, or 0) and the updated
  running count.

### Step 4 — Simulate full session

- `evaluate_counting(chromosome, n_hands=1000)` → int (final bankroll).
- Manages shoe lifecycle: shuffle at start, reshuffle when penetration
  reached.
- Tracks bankroll, stops if it reaches 0.

### Step 5 — GA loop

- Same structure as basic version but using `evaluate_counting` as fitness.
- Stats tracking: min, max, mean, median final bankroll per generation.

### Step 6 — Visualization (4 outputs)

1. **Fitness plot**: min/max/mean/median bankroll vs. generation.
2. **Strategy heatmap**: same as basic version (hard + soft % hit).
3. **Count values table**: evolved count values vs. Hi-Lo reference.
4. **Bet multipliers table**: evolved multiplier per true-count range.
5. **Bankroll plot**: bankroll over 1000 hands for best individual.

---

## Output Details

### Figure 1 — Fitness Over Generations

Same format as basic version, but Y-axis is "Final Bankroll ($)" instead of
win rate.

### Figure 2 — Strategy Heatmap

Identical to basic version.

### Table 1 — Evolved Count Values

```
Card Rank | Evolved Count | Hi-Lo Reference
----------|---------------|----------------
    Ace   |      ?        |       -1
     2    |      ?        |       +1
     3    |      ?        |       +1
     4    |      ?        |       +1
     5    |      ?        |       +1
     6    |      ?        |       +1
     7    |      ?        |        0
     8    |      ?        |        0
     9    |      ?        |        0
    10    |      ?        |       -1
```

Derived from the best individual in the final generation.

### Table 2 — Evolved Bet Multipliers

```
True Count Range | Multiplier ($)
-----------------|---------------
     <= -2       |      ?
   -1 to +1      |      ?
   +2 to +4      |      ?
     >= +5       |      ?
```

Expected pattern: low multiplier for negative counts, increasing as count
rises.

### Figure 3 — Bankroll Over Time

- **X-axis**: Hand number (1 to 1000)
- **Y-axis**: Bankroll ($)
- Single line showing bankroll trajectory for the best individual in the
  final generation playing a sample 1000-hand session.
- Horizontal dashed line at $1000 (starting bankroll) for reference.

---

## Data Structures Summary

| Component | Structure |
|-----------|-----------|
| Shoe | `list[int]` — 312 card values, shuffled |
| Chromosome | `list[int]` — 294 elements, each 0 or 1 |
| Count table | `dict[int, int]` — card value → {−1, 0, +1} |
| Bet table | `list[int]` — 4 multipliers, each 1–8 |
| Running count | `int` — cumulative across hands within a shoe |
| Bankroll | `int` — current dollar amount |

## Dependencies

Same as basic version: `random`, `numpy`, `matplotlib`.

---

## Expected Results

- **Counting system**: the GA should evolve count values similar to Hi-Lo
  (small cards +1, tens/aces −1, middle cards 0).
- **Bet multipliers**: low bets on negative/neutral counts, higher bets on
  positive counts.
- **Bankroll**: with effective counting and bet-spreading, the best
  individuals should maintain or slightly grow their bankroll over 1000
  hands (final bankroll near or above $1000).
- **Strategy heatmap**: should resemble the basic strategy, possibly with
  minor deviations reflecting count-adjusted play.
