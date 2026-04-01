# Clustering Homework — Implementation Plan

## Folder Structure

```
/workspaces/AI/5-Deliverables/
├── clustering.py              # Single main script, all tasks in order
├── plan.md                    # This file
├── requirements.txt
├── venv/
│
├── plot_01_pca_scatter.png
├── plot_02_kmeans_scatter.png
├── plot_03_petal_scatter.png
├── plot_04_silhouette.png
├── plot_05_dendrogram.png
└── plot_06_gmm_scatter.png
```

## Required Libraries

- `scikit-learn` — iris dataset, KMeans, PCA, silhouette_score, GaussianMixture
- `matplotlib` — all plotting
- `scipy` — linkage, dendrogram (scipy.cluster.hierarchy)
- `numpy` — array manipulation

## Implementation Order

### Step 1 — Boilerplate and Data Loading
Load the iris dataset once at module scope. Extract `X` (150×4 feature matrix) and `y` (150-element label array 0/1/2). Set `matplotlib.use('Agg')` at the top so the script runs headlessly. Define a shared 3-color palette reused across every plot. Use `random_state=42` for all stochastic algorithms.

### Step 2 — PCA Scatter Plot (`plot_01_pca_scatter.png`)
Fit `PCA(n_components=2)` on full 4D `X`. Plot points colored by true labels. Label axes with `PC1 (XX.X% variance)` and `PC2 (XX.X% variance)` using `pca.explained_variance_ratio_`. This should show setosa clearly separated from versicolor and virginica.

### Step 3 — K-Means Scatter Plot (`plot_02_kmeans_scatter.png`)
Fit `KMeans(n_clusters=3)` on full 4D `X` (not the PCA projection). Project centroids through PCA for plotting. Align cluster label indices to true species via majority-vote remapping. Draw centroids as large X markers.

### Step 4 — Petal Scatter Plot (`plot_03_petal_scatter.png`)
1×2 subplot using only petal length (col 2) and petal width (col 3).
- Left panel: true labels
- Right panel: k-means labels

Shows whether petal measurements alone can separate the classes.

### Step 5 — Silhouette Plot (`plot_04_silhouette.png`)
Loop `k` from 2 to 10. For each `k`, fit a new KMeans and compute `silhouette_score(X, labels)`. Plot a line chart of scores vs. k. Annotate the peak. Add a vertical dashed line at k=3.

### Step 6 — Hierarchical Clustering Dendrogram (`plot_05_dendrogram.png`)
Use `scipy.cluster.hierarchy.linkage(X, method='ward')`. Call `dendrogram()` with `truncate_mode='level', p=4` to keep it readable at 150 samples. Draw a horizontal dashed cut line at the height that yields 3 clusters.

### Step 7 — Gaussian Mixture Model (`plot_06_gmm_scatter.png`)
Fit `GaussianMixture(n_components=3, covariance_type='full')` on full 4D `X`. 1×2 subplot on PCA projection:
- Left panel: true labels
- Right panel: GMM labels with 1σ and 2σ covariance ellipses projected through PCA

Print a confusion matrix and accuracy score to stdout comparing GMM assignments to true labels.

## Key Design Decisions

- **Cluster in 4D, visualize in 2D** — PCA is used only for plotting; all algorithms see all 4 features
- **Consistent palette** across all plots so colors map to the same species/cluster everywhere
- **`plt.close()` after every `savefig`** to prevent figure state leakage between plots
- **Label alignment** — remap cluster 0/1/2 to true species via majority-vote before coloring
- **Covariance ellipses on GMM plot** — the key visual differentiating GMM from k-means
- **`figsize` conventions**: single plots (8,6), side-by-side (12,5), dendrogram (12,6)
- **`dpi=150`, `bbox_inches='tight'`** for all saved figures

## Written Questions to Answer

The assignment asks several written questions. These will be answered in `answers.md`.

### Q1 — Petal scatter (Step 4)
"Is it possible to separate one class from the other two using only petal measurements?"

**Answer:** Yes — setosa is cleanly separable from versicolor and virginica using petal length and petal width alone. There is a clear gap with no overlap. However, versicolor and virginica overlap somewhat in petal space, so they cannot be perfectly separated using only these two features.

### Q2 — Silhouette plot (Step 5)
"What is the best number of clusters according to the silhouette plot? What does that suggest about the challenges of cluster analysis?"

**Answer:** The silhouette score peaks at k=2, not k=3. This is because setosa is so distinct that it forms one tight cluster, while versicolor and virginica blur together into a second. The fact that the "correct" answer (k=3, matching the 3 species) scores lower than k=2 illustrates the core challenge of unsupervised clustering: the algorithm has no knowledge of the ground truth, and the natural geometric structure of the data doesn't always match the real-world categories we care about.

### Q3 — GMM vs. k-means (Step 7)
"Did either algorithm work well? What makes separating versicolor and virginica difficult?"

**Answer:** Both algorithms cleanly separate setosa but struggle with versicolor vs. virginica. GMM performs slightly better because its elliptical covariance shapes better capture the elongated, overlapping distributions of those two species. The fundamental difficulty is that versicolor and virginica genuinely overlap in feature space — there is no clean boundary. This is a data problem, not an algorithm problem; no clustering method can perfectly recover three classes when two of them are not geometrically distinct.

## Setup and Execution

```bash
cd /workspaces/AI/5-Deliverables
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python clustering.py
```
