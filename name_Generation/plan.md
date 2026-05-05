# Name Generation Project Plan

**Due:** 2026-05-05 (last day of exams)

---

## Overview

Train a statistical model and a neural network (makemore) on a list of 32,000 names. Analyze letter-transition statistics, generate names with both approaches, and compare the results.

---

## Phase 1 — Statistical Heatmap

**Goal:** Build a letter-transition matrix from `names.txt` and visualize it as a heatmap.

### Steps

1. Read `names.txt` line by line.
2. Wrap each name with `.` delimiters (e.g. `chelsea` → `.chelsea.`).
3. Count every bigram (consecutive letter pair) into a 27×27 matrix (26 letters + `.`).
4. Normalize each row into a probability distribution.
5. Render the matrix as a heatmap (matplotlib `imshow` or seaborn `heatmap`).
   - Label axes with the 27 characters.
   - Use a color scale so high-frequency pairs stand out.

### Questions to Answer

- **Three most likely starting letters:** Look at row `.` — the highest probability columns (excluding `.` itself).
- **Three least likely starting letters:** Lowest nonzero columns in row `.`.
- **Likely ending letters:** Look at column `.` — which rows have the highest probability of transitioning to `.`?
- **Letters after 'q':** Check row `q` — are there any columns other than `u` with nonzero values?
- **Most likely second letter for names starting with 'x':** Check row `x` for the highest-probability column.

### Deliverable

- `stats.py` — script that reads names, builds the matrix, produces the heatmap.
- `heatmap_real.png` — saved heatmap image.
- Written answers to the five questions above.

---

## Phase 2 — Statistical Name Generation

**Goal:** Use the row distributions from Phase 1 to generate 25 novel names via sampling.

### Steps

1. Start with `letter = '.'`.
2. Sample the next letter from `distribution[letter]` (use `numpy.random.choice` with `p=row_probabilities`).
3. If the sampled letter is `.`, stop; otherwise append it to the name.
4. Reject and retry any name with fewer than 3 non-dot characters.
5. Repeat until 25 valid names are collected. Print them.

### Questions to Answer

- Do the generated names seem realistic?
- What qualities do you observe (length distribution, common endings, phonetic feel)?

### Deliverable

- Generation logic added to `stats.py` (or a separate `generate_stats.py`).
- Printed list of 25 generated names included in the written response.

---

## Phase 3 — Train makemore

**Goal:** Train the makemore transformer on `names.txt` and sample at least 200 novel names.

### Steps

1. Clone the repo:
   ```
   git clone https://github.com/karpathy/makemore
   ```
2. Install dependencies:
   ```
   pip install torch tensorboard
   ```
3. Train (run for at least 100,000 steps):
   ```
   python makemore.py -i names.txt -o names
   ```
4. Once training is stopped, sample names (repeat with different seeds):
   ```
   python makemore.py -i names.txt -o names --sample-only --seed 1
   python makemore.py -i names.txt -o names --sample-only --seed 2
   ...
   ```
5. Filter out any names already in `names.txt`.
6. Collect at least 200 unique novel names.

### Deliverable

- `makemore_names.txt` — list of ≥200 novel names produced by the model.

---

## Phase 4 — Statistical Heatmap for makemore Names

**Goal:** Repeat the Phase 1 analysis on the makemore-generated names and compare.

### Steps

1. Run the same bigram-counting and normalization pipeline on `makemore_names.txt`.
2. Produce a second heatmap with identical axis labels and color scale so the two maps are directly comparable.
3. Compare the two heatmaps:
   - Which bigrams are more/less common in makemore output vs. real names?
   - Does makemore capture rare letter combinations? Does it over- or under-represent any transitions?
   - How do the starting/ending letter distributions compare?

### Deliverable

- `heatmap_makemore.png` — saved heatmap of makemore names.
- Written comparison paragraph.

---

## Submission Checklist

- [ ] `heatmap_real.png` — transition heatmap for `names.txt`
- [ ] `heatmap_makemore.png` — transition heatmap for makemore names
- [ ] `makemore_names.txt` — list of ≥200 novel names from makemore
- [ ] Written answers to all questions (starting/ending letters, q→u, x second letter, statistical name quality, heatmap comparison)
- [ ] Source scripts (`stats.py`, etc.)

---

## File Layout

```
name_Generation/
├── plan.md                  ← this file
├── stats.py                 ← bigram matrix, heatmap, and statistical generator
├── makemore_names.txt       ← ≥200 novel names from makemore
├── heatmap_real.png
├── heatmap_makemore.png
└── writtenResponse.md       ← answers to all questions
```
