import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score
import xgboost as xgb

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

# The protocol says: "Classify variable vs non-variable sources using symbol_series features."
# So the signal must be in symbol_series.
# Let's try to use a pre-trained language model or a simple character-level RNN.
# We already tried LSTM and CNN, and they got ~0.55.
# Maybe we need to train them longer or with different hyperparameters.
# Let's try a simple 1D CNN again, but with more filters and a global max pooling.

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader

char_map = {'*': 0, '.': 1, 'u': 2, 'v': 3, 'w': 4, 'x': 5, 'y': 6, 'z': 7}

class SymbolDataset(Dataset):
    def __init__(self, df):
        self.data = []
        self.labels = []
        for _, row in df.iterrows():
            seq = [char_map[c] for c in row['symbol_series']]
            self.data.append(seq)
            self.labels.append(row['label'])
            
    def __len__(self):
        return len(self.data)
        
    def __getitem__(self, idx):
        return torch.tensor(self.data[idx], dtype=torch.long), torch.tensor(self.labels[idx], dtype=torch.float32)

train_dataset = SymbolDataset(train)
val_dataset = SymbolDataset(val)

train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=16, shuffle=False)

class CNN1D(nn.Module):
    def __init__(self):
        super().__init__()
        self.embedding = nn.Embedding(8, 16)
        self.conv1 = nn.Conv1d(16, 64, kernel_size=3, padding=1)
        self.conv2 = nn.Conv1d(64, 128, kernel_size=5, padding=2)
        self.conv3 = nn.Conv1d(128, 256, kernel_size=7, padding=3)
        self.relu = nn.ReLU()
        self.pool = nn.AdaptiveMaxPool1d(1)
        self.fc1 = nn.Linear(256, 64)
        self.dropout = nn.Dropout(0.5)
        self.fc2 = nn.Linear(64, 1)
        
    def forward(self, x):
        x = self.embedding(x).permute(0, 2, 1)
        x = self.relu(self.conv1(x))
        x = self.relu(self.conv2(x))
        x = self.relu(self.conv3(x))
        x = self.pool(x).squeeze(2)
        x = self.dropout(self.relu(self.fc1(x)))
        x = self.fc2(x)
        return x

model = CNN1D()
optimizer = optim.Adam(model.parameters(), lr=0.0005)
criterion = nn.BCEWithLogitsLoss()

best_acc = 0
for epoch in range(50):
    model.train()
    for batch_x, batch_y in train_loader:
        optimizer.zero_grad()
        predictions = model(batch_x).squeeze(1)
        loss = criterion(predictions, batch_y)
        loss.backward()
        optimizer.step()
        
    model.eval()
    all_preds = []
    all_labels = []
    with torch.no_grad():
        for batch_x, batch_y in val_loader:
            predictions = model(batch_x).squeeze(1)
            preds = torch.round(torch.sigmoid(predictions))
            all_preds.extend(preds.numpy())
            all_labels.extend(batch_y.numpy())
            
    acc = balanced_accuracy_score(all_labels, all_preds)
    if acc > best_acc:
        best_acc = acc
    if (epoch + 1) % 10 == 0:
        print(f'Epoch {epoch+1} Val Balanced Acc: {acc:.4f}')
print(f'Best Val Balanced Acc: {best_acc:.4f}')
