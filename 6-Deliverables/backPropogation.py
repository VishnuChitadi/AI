import numpy as np

def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))

def sigmoid_derivative(x):
    return x * (1.0 - x)

def relu(x):
    return np.maximum(0.0, x)

def relu_derivative(x):
    return (x > 0).astype(float)


def init_weights(n_inputs, n_hidden, n_outputs):
    rng = np.random.default_rng()                              # FIX 1: typo defautl -> default
    hidden_weights = rng.uniform(-1, 1, (n_hidden, n_inputs + 1))
    output_weights = rng.uniform(-1, 1, (n_outputs, n_hidden + 1))  # FIX 2: was a bare tuple, not a call
    return hidden_weights, output_weights


def predict(hidden_weights, output_weights, point, activation="sigmoid"):  # FIX 3: outputs_weights -> output_weights
    act_fn = relu if activation == "relu" else sigmoid

    inputs_with_bias = np.concatenate(([1.0], point))
    hidden_raw = hidden_weights @ inputs_with_bias
    hidden_outputs = act_fn(hidden_raw)

    hidden_with_bias = np.concatenate(([1.0], hidden_outputs))
    output_raw = output_weights @ hidden_with_bias             # FIX 3: outputs_weights -> output_weights
    final_outputs = sigmoid(output_raw)

    return hidden_outputs, final_outputs


def train(hidden_weights, output_weights, point, target_label, learning_rate, activation="sigmoid"):
    act_deriv = relu_derivative if activation == "relu" else sigmoid_derivative

    target = np.atleast_1d(np.array(target_label, dtype=float))

    inputs_with_bias = np.concatenate(([1.0], point))
    hidden_outputs, final_outputs = predict(
        hidden_weights, output_weights, point, activation
    )
    hidden_with_bias = np.concatenate(([1.0], hidden_outputs))

    output_errors = target - final_outputs
    output_deltas = output_errors * sigmoid_derivative(final_outputs)

    hidden_errors = output_weights[:, 1:].T @ output_deltas
    hidden_deltas = hidden_errors * act_deriv(hidden_outputs)

    output_weights += learning_rate * np.outer(output_deltas, hidden_with_bias)
    hidden_weights += learning_rate * np.outer(hidden_deltas, inputs_with_bias)

    mse = np.mean(output_errors ** 2)
    return hidden_weights, output_weights, mse


def epoch(hidden_weights, output_weights, training_set, training_labels,
          learning_rate, activation="sigmoid"):
    indices = np.random.permutation(len(training_set))
    total_error = 0.0
    for i in indices:
        hidden_weights, output_weights, err = train(
            hidden_weights, output_weights,
            training_set[i], training_labels[i],
            learning_rate, activation)
        total_error += err
    avg_error = total_error / len(training_set)
    return hidden_weights, output_weights, avg_error


def evaluate(hidden_weights, output_weights, testing_set, testing_labels, activation="sigmoid"):
    correct = 0
    for point, label in zip(testing_set, testing_labels):
        _, final_outputs = predict(hidden_weights, output_weights, point, activation)
        label = np.atleast_1d(np.array(label))
        if len(final_outputs) == 1:
            predicted = int(final_outputs[0] >= 0.5)
            truth = int(label[0])
        else:
            predicted = int(np.argmax(final_outputs))
            truth = int(np.argmax(label))
        if predicted == truth:
            correct += 1
    return correct / len(testing_set)


training_sset = np.array([
    [0.0, 0.0],
    [0.0, 1.0],
    [1.0,0.0],
    [1.0,1.0]
])
training_labels = np.array([0,1,1,0])

n_inputs=2
n_hidden=4
n_outputs=1

hidden_weights, output_weights = init_weights(n_inputs, n_hidden, n_outputs)

learning_rate=0.1
n_epochs=10000

for e in range(n_epochs):
    hidden_weights, output_weights, avg_err = epoch(
        hidden_weights, output_weights, training_sset, training_labels, learning_rate
    )
    if (e+1)%1000==0:
        acc = evaluate(hidden_weights, output_weights, training_sset, training_labels)
        print(f"Epoch {e+1:6d} | Avg MSE : {avg_err: .6f} | Accuracy: {acc:.2%}")

print("\nFinal predictions:")
print(f"{'x1':>4} {'x2':>4} | {'target':>6} | {'output':>8} | {'pred':>4}")
print("-" * 38)
for point, label in zip(training_sset, training_labels):
    _, final_out = predict(hidden_weights, output_weights, point)
    pred = int(final_out[0] >= 0.5)
    print(f"{int(point[0]):>4} {int(point[1]):>4} | {label:>6} | {final_out[0]:>8.4f} | {pred:>4}")