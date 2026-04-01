import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Ellipse
import numpy as np
from sklearn.datasets import load_iris
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.mixture import GaussianMixture
from sklearn.metrics import silhouette_score, confusion_matrix, accuracy_score
from scipy.cluster.hierarchy import linkage, dendrogram

# ── Data ──────────────────────────────────────────────────────────────────────
iris = load_iris()
X = iris.data          # (150, 4)
y = iris.target        # 0=setosa, 1=versicolor, 2=virginica
species = iris.target_names

PALETTE = ['#E41A1C', '#377EB8', '#4DAF4A']   # red, blue, green


# ── Helpers ───────────────────────────────────────────────────────────────────

def align_labels(pred, true):
    """Remap predicted cluster indices to best-matching true labels."""
    mapping = {}
    for cluster in np.unique(pred):
        mask = pred == cluster
        mapping[cluster] = np.bincount(true[mask]).argmax()
    return np.array([mapping[p] for p in pred])


def make_legend(ax, names, palette):
    handles = [mpatches.Patch(color=palette[i], label=names[i]) for i in range(len(names))]
    ax.legend(handles=handles, loc='best')


def draw_ellipse(ax, mean, cov, color, n_std=2.0, alpha=0.15):
    """Draw a covariance ellipse on ax."""
    vals, vecs = np.linalg.eigh(cov)
    order = vals.argsort()[::-1]
    vals, vecs = vals[order], vecs[:, order]
    angle = np.degrees(np.arctan2(*vecs[:, 0][::-1]))
    for ns in [1.0, n_std]:
        w, h = 2 * ns * np.sqrt(vals)
        ell = Ellipse(xy=mean, width=w, height=h, angle=angle,
                      color=color, alpha=alpha, lw=1.5,
                      fill=(ns == n_std))
        ax.add_patch(ell)


# ── Step 2: PCA scatter (true labels) ─────────────────────────────────────────
pca = PCA(n_components=2, random_state=42)
X2 = pca.fit_transform(X)
var = pca.explained_variance_ratio_ * 100

fig, ax = plt.subplots(figsize=(8, 6))
for i, name in enumerate(species):
    mask = y == i
    ax.scatter(X2[mask, 0], X2[mask, 1], c=PALETTE[i], label=name,
               edgecolors='k', linewidths=0.4, s=60, alpha=0.85)
ax.set_xlabel(f'PC1 ({var[0]:.1f}% variance)')
ax.set_ylabel(f'PC2 ({var[1]:.1f}% variance)')
ax.set_title('Iris Dataset — PCA Projection (True Labels)')
ax.legend(loc='best')
plt.tight_layout()
plt.savefig('plot_01_pca_scatter.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved plot_01_pca_scatter.png')


# ── Step 3: K-Means scatter ───────────────────────────────────────────────────
km = KMeans(n_clusters=3, random_state=42, n_init=10)
km_labels = align_labels(km.fit_predict(X), y)
centroids_2d = pca.transform(km.cluster_centers_)

fig, ax = plt.subplots(figsize=(8, 6))
for i, name in enumerate(species):
    mask = km_labels == i
    ax.scatter(X2[mask, 0], X2[mask, 1], c=PALETTE[i], label=f'Cluster → {name}',
               edgecolors='k', linewidths=0.4, s=60, alpha=0.85)
ax.scatter(centroids_2d[:, 0], centroids_2d[:, 1],
           marker='X', s=220, c='white', edgecolors='black', linewidths=1.5,
           zorder=5, label='Centroids')
ax.set_xlabel(f'PC1 ({var[0]:.1f}% variance)')
ax.set_ylabel(f'PC2 ({var[1]:.1f}% variance)')
ax.set_title('K-Means Clustering (k=3) — PCA Projection')
ax.legend(loc='best')
plt.tight_layout()
plt.savefig('plot_02_kmeans_scatter.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved plot_02_kmeans_scatter.png')


# ── Step 4: Petal scatter ─────────────────────────────────────────────────────
petal_len = X[:, 2]
petal_wid = X[:, 3]

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
for ax, labels, title in zip(axes, [y, km_labels], ['True Labels', 'K-Means (k=3)']):
    for i, name in enumerate(species):
        mask = labels == i
        ax.scatter(petal_len[mask], petal_wid[mask], c=PALETTE[i], label=name,
                   edgecolors='k', linewidths=0.4, s=60, alpha=0.85)
    ax.set_xlabel('Petal Length (cm)')
    ax.set_ylabel('Petal Width (cm)')
    ax.set_title(title)
    ax.legend(loc='best')
fig.suptitle('Petal Length vs. Petal Width', fontsize=13)
plt.tight_layout()
plt.savefig('plot_03_petal_scatter.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved plot_03_petal_scatter.png')


# ── Step 5: Silhouette plot ───────────────────────────────────────────────────
ks = range(2, 11)
scores = []
for k in ks:
    lbl = KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(X)
    scores.append(silhouette_score(X, lbl))

best_k = list(ks)[np.argmax(scores)]
best_score = max(scores)

fig, ax = plt.subplots(figsize=(8, 6))
ax.plot(list(ks), scores, marker='o', color='steelblue', linewidth=2)
ax.axvline(x=3, color='gray', linestyle='--', linewidth=1, label='k=3 (assignment)')
ax.annotate(f'Best: k={best_k}\n({best_score:.3f})',
            xy=(best_k, best_score),
            xytext=(best_k + 0.4, best_score - 0.02),
            arrowprops=dict(arrowstyle='->', color='black'),
            fontsize=10)
ax.set_xlabel('Number of Clusters (k)')
ax.set_ylabel('Mean Silhouette Score')
ax.set_title('Silhouette Score vs. Number of Clusters')
ax.set_xticks(list(ks))
ax.legend()
plt.tight_layout()
plt.savefig('plot_04_silhouette.png', dpi=150, bbox_inches='tight')
plt.close()
print(f'Saved plot_04_silhouette.png  (best k={best_k}, score={best_score:.3f})')


# ── Step 6: Dendrogram ────────────────────────────────────────────────────────
Z = linkage(X, method='ward')
cut_height = (Z[-3, 2] + Z[-2, 2]) / 2  # midpoint → 3 clusters

fig, ax = plt.subplots(figsize=(12, 6))
dendrogram(Z, ax=ax, truncate_mode='level', p=4,
           color_threshold=Z[-3, 2], above_threshold_color='gray',
           no_labels=True)
ax.axhline(y=cut_height, color='red', linestyle='--', linewidth=1.5,
           label=f'Cut for 3 clusters (h={cut_height:.1f})')
ax.set_xlabel('Samples')
ax.set_ylabel('Ward Distance')
ax.set_title('Hierarchical Clustering Dendrogram (Ward Linkage)')
ax.legend()
plt.tight_layout()
plt.savefig('plot_05_dendrogram.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved plot_05_dendrogram.png')


# ── Step 7: GMM ───────────────────────────────────────────────────────────────
gmm = GaussianMixture(n_components=3, covariance_type='full', random_state=42)
gmm_labels = align_labels(gmm.fit_predict(X), y)

# Project GMM means and covariances into PCA 2D space
V = pca.components_   # (2, 4)
gmm_means_2d = pca.transform(gmm.means_)
gmm_covs_2d = [V @ cov @ V.T for cov in gmm.covariances_]

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Left: true labels
ax = axes[0]
for i, name in enumerate(species):
    mask = y == i
    ax.scatter(X2[mask, 0], X2[mask, 1], c=PALETTE[i], label=name,
               edgecolors='k', linewidths=0.4, s=60, alpha=0.85)
ax.set_xlabel(f'PC1 ({var[0]:.1f}% variance)')
ax.set_ylabel(f'PC2 ({var[1]:.1f}% variance)')
ax.set_title('True Labels')
ax.legend(loc='best')

# Right: GMM with ellipses
ax = axes[1]
for i, name in enumerate(species):
    mask = gmm_labels == i
    ax.scatter(X2[mask, 0], X2[mask, 1], c=PALETTE[i], label=f'GMM → {name}',
               edgecolors='k', linewidths=0.4, s=60, alpha=0.85)

# Draw ellipses — match ellipse to the cluster whose center is closest to each species center
for i in range(3):
    draw_ellipse(ax, gmm_means_2d[i], gmm_covs_2d[i], color=PALETTE[i])

ax.set_xlabel(f'PC1 ({var[0]:.1f}% variance)')
ax.set_ylabel(f'PC2 ({var[1]:.1f}% variance)')
ax.set_title('GMM Clustering (k=3) with Covariance Ellipses')
ax.legend(loc='best')

fig.suptitle('GMM vs. True Labels — PCA Projection', fontsize=13)
plt.tight_layout()
plt.savefig('plot_06_gmm_scatter.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved plot_06_gmm_scatter.png')

# GMM accuracy report
print('\n── GMM vs. True Labels ──────────────────────────────')
print(f'Accuracy: {accuracy_score(y, gmm_labels):.3f}')
print('Confusion matrix (rows=true, cols=predicted):')
print(confusion_matrix(y, gmm_labels))
print('─────────────────────────────────────────────────────')
