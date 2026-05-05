import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import random

NAMES_FILE = "makemore/names.txt"
CHARS = ['.'] + list('abcdefghijklmnopqrstuvwxyz')
CHAR_TO_IDX = {c: i for i, c in enumerate(CHARS)}
N = len(CHARS)  # 27


def load_names(path):
    with open(path) as f:
        return [line.strip().lower() for line in f if line.strip()]


def build_matrix(names):
    counts = np.zeros((N, N), dtype=np.float64)
    for name in names:
        padded = '.' + name + '.'
        for a, b in zip(padded, padded[1:]):
            if a in CHAR_TO_IDX and b in CHAR_TO_IDX:
                counts[CHAR_TO_IDX[a]][CHAR_TO_IDX[b]] += 1
    # Normalize rows to probabilities
    row_sums = counts.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1  # avoid division by zero
    probs = counts / row_sums
    return counts, probs


def plot_heatmap(probs, title, outfile):
    fig, ax = plt.subplots(figsize=(14, 12))
    im = ax.imshow(probs, cmap='Blues', norm=mcolors.PowerNorm(gamma=0.5))
    ax.set_xticks(range(N))
    ax.set_yticks(range(N))
    ax.set_xticklabels(CHARS, fontsize=9)
    ax.set_yticklabels(CHARS, fontsize=9)
    ax.set_xlabel("Second Letter", fontsize=12)
    ax.set_ylabel("First Letter", fontsize=12)
    ax.set_title(title, fontsize=14)
    plt.colorbar(im, ax=ax, label="Transition Probability")
    plt.tight_layout()
    plt.savefig(outfile, dpi=150)
    plt.close()
    print(f"Saved {outfile}")


def answer_questions(probs, label):
    print(f"\n=== Questions: {label} ===")

    # Starting letters: row '.' excluding '.' itself
    dot_idx = CHAR_TO_IDX['.']
    start_probs = probs[dot_idx].copy()
    start_probs[dot_idx] = 0  # exclude '.' -> '.'
    order = np.argsort(start_probs)[::-1]
    nonzero = [i for i in order if start_probs[i] > 0]
    print("Three most likely starting letters:",
          [CHARS[i] for i in nonzero[:3]])
    print("Three least likely starting letters:",
          [CHARS[i] for i in nonzero[-3:]])

    # Ending letters: column '.' excluding '.' row
    end_probs = probs[:, dot_idx].copy()
    end_probs[dot_idx] = 0
    order_end = np.argsort(end_probs)[::-1]
    nonzero_end = [i for i in order_end if end_probs[i] > 0]
    print("Three most likely ending letters:",
          [CHARS[i] for i in nonzero_end[:3]])
    print("Three least likely ending letters:",
          [CHARS[i] for i in nonzero_end[-3:]])

    # Letters after 'q'
    q_idx = CHAR_TO_IDX['q']
    q_row = probs[q_idx]
    q_followers = [(CHARS[i], q_row[i]) for i in range(N) if q_row[i] > 0 and CHARS[i] != '.']
    print("Letters following 'q':", q_followers)

    # Most likely second letter for names starting with 'x'
    x_idx = CHAR_TO_IDX['x']
    x_row = probs[x_idx].copy()
    x_row[dot_idx] = 0
    best_after_x = CHARS[np.argmax(x_row)]
    print(f"Most likely second letter after 'x': {best_after_x} ({x_row[np.argmax(x_row)]:.3f})")


def generate_names(probs, n=25, min_len=3, seed=42):
    rng = np.random.default_rng(seed)
    names = []
    dot_idx = CHAR_TO_IDX['.']
    while len(names) < n:
        name = ''
        idx = dot_idx
        for _ in range(50):  # safety cap
            idx = rng.choice(N, p=probs[idx])
            if idx == dot_idx:
                break
            name += CHARS[idx]
        if len(name) >= min_len:
            names.append(name)
    return names


if __name__ == '__main__':
    # --- Phase 1 & 2: real names ---
    names = load_names(NAMES_FILE)
    counts, probs = build_matrix(names)
    plot_heatmap(probs, "Bigram Transition Probabilities — Real Names", "heatmap_real.png")
    answer_questions(probs, "Real Names")

    print("\n=== 25 Statistically Generated Names ===")
    gen_names = generate_names(probs)
    for i, name in enumerate(gen_names, 1):
        print(f"{i:2d}. {name}")

    # --- Phase 4: makemore names (if file exists) ---
    import os
    if os.path.exists("makemore_names.txt"):
        makemore_names = load_names("makemore_names.txt")
        _, mm_probs = build_matrix(makemore_names)
        plot_heatmap(mm_probs, "Bigram Transition Probabilities — Makemore Names", "heatmap_makemore.png")
        answer_questions(mm_probs, "Makemore Names")
    else:
        print("\nmakemore_names.txt not found — skipping Phase 4 heatmap.")
