import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import load_iris

from backPropogation import init_weights, epoch, evaluate


# --- Load & preprocess ---
iris = load_iris()
X = iris.data.astype(float)
y = iris.target

# Normalize features to [0, 1]
X = (X - X.min(axis=0)) / (X.max(axis=0) - X.min(axis=0))

# One-hot encode labels
labels = np.zeros((len(y), 3))
labels[np.arange(len(y)), y] = 1.0

# --- Train/test split: 30 test, 120 train ---
rng = np.random.default_rng(42)
indices = rng.permutation(150)
test_idx = indices[:30]
train_idx = indices[30:]

X_train, y_train = X[train_idx], labels[train_idx]
X_test, y_test = X[test_idx], labels[test_idx]

# --- Network setup ---
n_inputs = 4
n_hidden = 8
n_outputs = 3
learning_rate = 0.1
n_epochs = 1000
activation = "relu"

hidden_weights, output_weights = init_weights(n_inputs, n_hidden, n_outputs)

# --- Training loop ---
epoch_errors = []
for e in range(n_epochs):
    hidden_weights, output_weights, avg_err = epoch(
        hidden_weights, output_weights, X_train, y_train, learning_rate, activation
    )
    epoch_errors.append(avg_err)
    if (e + 1) % 100 == 0:
        acc = evaluate(hidden_weights, output_weights, X_train, y_train, activation)
        print(f"Epoch {e+1:5d} | Avg MSE: {avg_err:.6f} | Train Acc: {acc:.2%}")

# --- Final test evaluation ---
test_acc = evaluate(hidden_weights, output_weights, X_test, y_test, activation)
print(f"\nTest set accuracy (30 samples): {test_acc:.2%}")

# --- Plot training error ---
plt.figure(figsize=(8, 4))
plt.plot(epoch_errors)
plt.xlabel("Epoch")
plt.ylabel("Average MSE")
plt.title("Training Error over Epochs — Iris Classification (ReLU)")
plt.tight_layout()
plt.savefig("iris_training_error_relu.png", dpi=150)
plt.show()
print("Plot saved to iris_training_error_relu.png")
