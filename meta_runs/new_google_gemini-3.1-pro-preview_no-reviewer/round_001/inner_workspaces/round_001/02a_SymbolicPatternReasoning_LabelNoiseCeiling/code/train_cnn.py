import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.metrics import accuracy_score

train = pd.read_csv('data/spr_bench_train.csv')
val = pd.read_csv('data/spr_bench_val.csv')
test = pd.read_csv('data/spr_bench_test.csv')

feature_cols = [c for c in train.columns if c.startswith('token_')]

# One-hot encode the tokens
all_tokens = [f"{s}{c}" for s in ['T', 'S', 'C', 'D'] for c in ['r', 'g', 'b', 'y']]
token_to_idx = {t: i for i, t in enumerate(all_tokens)}

def encode_data(df):
    X = np.zeros((len(df), len(feature_cols), len(all_tokens)), dtype=np.float32)
    for i, row in enumerate(df[feature_cols].values):
        for j, token in enumerate(row):
            X[i, j, token_to_idx[token]] = 1.0
    return X

X_train = encode_data(train)
y_train = train['label'].values
X_val = encode_data(val)
y_val = val['label'].values
X_test = encode_data(test)
y_test = test['label'].values

X_train_tensor = torch.tensor(X_train).permute(0, 2, 1) # (batch, channels, length)
y_train_tensor = torch.tensor(y_train, dtype=torch.float32).unsqueeze(1)
X_val_tensor = torch.tensor(X_val).permute(0, 2, 1)
y_val_tensor = torch.tensor(y_val, dtype=torch.float32).unsqueeze(1)
X_test_tensor = torch.tensor(X_test).permute(0, 2, 1)
y_test_tensor = torch.tensor(y_test, dtype=torch.float32).unsqueeze(1)

train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)

class SimpleCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv1d(in_channels=16, out_channels=32, kernel_size=3, padding=1)
        self.relu = nn.ReLU()
        self.pool = nn.MaxPool1d(kernel_size=2)
        self.conv2 = nn.Conv1d(in_channels=32, out_channels=64, kernel_size=3, padding=1)
        self.fc1 = nn.Linear(64 * 2, 32)
        self.fc2 = nn.Linear(32, 1)
        self.sigmoid = nn.Sigmoid()
        self.dropout = nn.Dropout(0.5)
        
    def forward(self, x):
        x = self.pool(self.relu(self.conv1(x)))
        x = self.pool(self.relu(self.conv2(x)))
        x = x.view(x.size(0), -1)
        x = self.dropout(self.relu(self.fc1(x)))
        x = self.fc2(x)
        return self.sigmoid(x)

model = SimpleCNN()
criterion = nn.BCELoss()
optimizer = optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-4)

best_val_acc = 0

print("Training CNN...")
for epoch in range(100):
    model.train()
    for inputs, labels in train_loader:
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
    model.eval()
    with torch.no_grad():
        train_preds = (model(X_train_tensor) > 0.5).float()
        train_acc = accuracy_score(y_train, train_preds.numpy())
        
        val_preds = (model(X_val_tensor) > 0.5).float()
        val_acc = accuracy_score(y_val, val_preds.numpy())
        
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            
    if (epoch+1) % 10 == 0:
        print(f"Epoch {epoch+1}, Loss: {loss.item():.4f}, Train Acc: {train_acc:.4f}, Val Acc: {val_acc:.4f}")

print(f"\nBest Val Acc: {best_val_acc:.4f}")
