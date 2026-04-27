import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score

train = pd.read_csv('data/spr_bench_train.csv')
feature_cols = [c for c in train.columns if c.startswith('token_')]

# Still nothing above 54%.
# Let's reconsider the task description: "binary classification of symbolic sequences (shape+color tokens; hidden rule—see protocol.md). Use Train/Val/Test CSVs: train, tune, report test accuracy vs 70% SOTA."
# The task is "LabelNoiseCeiling".
# This means the labels are noisy. The SOTA is 70%.
# If the labels are noisy, and the SOTA is 70%, it means the BEST possible model can only achieve 70% accuracy because 30% of the labels are random noise.
# BUT, if 30% of the labels are random noise, the true rule should still have ~70% accuracy on the training set.
# Why can't we find any rule with ~70% accuracy?
# Maybe the rule is a combination of features.

# Let's try to train a Random Forest with very few trees and low depth, and see if any tree achieves ~70% accuracy.
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder

encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
X_train = encoder.fit_transform(train[feature_cols])
y_train = train['label']

rf = RandomForestClassifier(n_estimators=1000, max_depth=3, random_state=42)
rf.fit(X_train, y_train)

best_tree_acc = 0
for tree in rf.estimators_:
    acc = accuracy_score(y_train, tree.predict(X_train))
    if acc > best_tree_acc:
        best_tree_acc = acc

print(f"Best single tree accuracy: {best_tree_acc:.4f}")

# Even the best single tree in a random forest only gets ~55% accuracy.
# This means the rule is NOT a simple combination of 1-3 features.

# Let's try to use a neural network with a very specific architecture.
# Maybe the rule is based on counting, so we need an architecture that can count.
# Or maybe the rule is based on sequence patterns, so we need an RNN or CNN.

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

# Convert data to tensors
# Map shapes and colors to integers
shape_map = {'T': 0, 'S': 1, 'C': 2, 'D': 3}
color_map = {'r': 0, 'g': 1, 'b': 2, 'y': 3}

def encode_sequence(row):
    seq = []
    for t in row:
        seq.append([shape_map[t[0]], color_map[t[1]]])
    return seq

X_train_seq = np.array([encode_sequence(row) for row in train[feature_cols].values])
y_train_seq = train['label'].values

X_train_tensor = torch.tensor(X_train_seq, dtype=torch.float32)
y_train_tensor = torch.tensor(y_train_seq, dtype=torch.float32).unsqueeze(1)

dataset = TensorDataset(X_train_tensor, y_train_tensor)
dataloader = DataLoader(dataset, batch_size=32, shuffle=True)

class SimpleRNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.rnn = nn.RNN(input_size=2, hidden_size=16, batch_first=True)
        self.fc = nn.Linear(16, 1)
        self.sigmoid = nn.Sigmoid()
        
    def forward(self, x):
        out, _ = self.rnn(x)
        out = self.fc(out[:, -1, :])
        return self.sigmoid(out)

model = SimpleRNN()
criterion = nn.BCELoss()
optimizer = optim.Adam(model.parameters(), lr=0.01)

print("\nTraining RNN...")
for epoch in range(50):
    for inputs, labels in dataloader:
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
    if (epoch+1) % 10 == 0:
        with torch.no_grad():
            preds = (model(X_train_tensor) > 0.5).float()
            acc = accuracy_score(y_train_seq, preds.numpy())
            print(f"Epoch {epoch+1}, Loss: {loss.item():.4f}, Train Acc: {acc:.4f}")
