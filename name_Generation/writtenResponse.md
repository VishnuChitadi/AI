# Name Generation — Written Response

---

## Phase 1: Statistical Heatmap Questions

### Most and Least Likely Starting Letters
Looking at the row for `.` in the transition matrix (which shows what letter begins each name):

- **Three most likely starting letters:** `a`, `k`, `m`
  - Names beginning with 'a' are by far the most common, followed by 'k' and 'm'.
- **Three least likely starting letters:** `x`, `q`, `u`
  - These letters almost never begin a name in the dataset.

### Most and Least Likely Ending Letters
Looking at the `.` column (which shows what letter tends to end each name):

- **Three most likely ending letters:** `n`, `h`, `x` (e.g. ian, noah, alex)
- **Three least likely ending letters:** `p`, `c`, `j`
  - Names rarely end in hard stop consonants like 'p', 'c', or 'j'.

### Letters Following 'q'
In real names, 'q' is followed overwhelmingly by `u` (75.7% of the time), which matches English convention. However, it is **not** exclusively followed by 'u' — small but nonzero probabilities exist for `a`, `i`, `m`, `o`, `s`, and `w`, reflecting names borrowed from Arabic, Hebrew, and other languages (e.g. Qasim, Qi).

### Most Likely Second Letter for Names Starting with 'x'
The most likely second letter after `x` is **`a`** (probability 0.148), reflecting names like Xavier, Xander, Xamara.

---

## Phase 2: Statistical Name Generation

### 25 Generated Names

1. reslaynn
2. jaylon
3. siquxxtal
4. brlyaha
5. alanasleron
6. maa
7. rinlema
8. mbllilicakaisa
9. eendonara
10. ana
11. kanaicie
12. ayriaynige
13. emasorenen
14. jale
15. tien
16. yer
17. kexijahak
18. staman
19. mir
20. kasseyalay
21. akyrlyridona
22. olya
23. ludaryga
24. dan
25. kimarki

### Observations
The statistical model produces names with mixed realism. Some outputs look plausible — `jaylon`, `jale`, `olya`, `dan`, `staman` could pass as real names. Others are clearly artificial: `mbllilicakaisa` and `akyrlyridona` are far too long and contain unusual consonant clusters because the bigram model has no memory beyond the immediately preceding letter. It cannot enforce global constraints like overall name length or phonetic flow. The model correctly avoids rare starting letters and tends to end names in common endings like `-n` and `-a`, but it has no awareness that consonant clusters like `mbl-` don't appear at the start of English names.

---

## Phase 3: Makemore Training

The makemore transformer (4 layers, 4 heads, 64-dim embeddings, ~200k parameters) was trained on `names.txt` for 100,000 steps. Training loss dropped from ~3.5 to ~1.5, and test loss settled around 2.0, indicating the model learned meaningful structure without badly overfitting.

200 novel names not present in the training set were collected by sampling with seeds 1–7. See `makemore_names.txt`.

---

## Phase 4: Heatmap Comparison — Real vs. Makemore Names

### Starting Letters
Both distributions are similar: `a`, `m`, `k` are the top starters in both. Makemore correctly learned that 'a' is the most common initial letter. The rare starters (`q`, `u`, `x`) are also rare in makemore output, showing the model absorbed the overall frequency distribution well.

### Ending Letters
Real names end most often in `n`, `h`, and `x`. Makemore names also end frequently in `n` and `h`, but show a higher probability for `z` as an ending — suggesting the model slightly over-represents rare but learnable endings it encountered in training.

### Letters After 'q'
In real names, 'q' is followed by 'u' ~76% of the time with several rare alternatives. In makemore names, 'q' is followed exclusively by 'u' (100%). With only a handful of 'q'-containing names in 200 samples, the model's output doesn't capture the rare non-'u' cases — it defaults to the overwhelmingly dominant pattern.

### Letters After 'x'
Real names most often have `a` follow `x` (0.148). Makemore names also favor `a` after `x` (0.200), again matching the dominant real-data pattern closely.

### Overall Comparison
The makemore heatmap is noticeably smoother and more concentrated than the real-name heatmap. The real-data matrix has many zero cells (letter pairs that never occur), while makemore's output fills in more of the matrix with low-but-nonzero probabilities — a sign of the model generalizing beyond exact training bigrams. Common transitions (e.g. vowels following consonants) are well-captured in both maps. The transformer produces names that feel more globally coherent — correct length, realistic syllable structure — compared to the statistical model, because it conditions on the full preceding context rather than just one letter.
