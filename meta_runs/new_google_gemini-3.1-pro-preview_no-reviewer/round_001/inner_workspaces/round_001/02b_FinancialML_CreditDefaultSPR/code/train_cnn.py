import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import roc_auc_score

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

chars = ['1', '2', 'A', 'B', 'C', 'D']
char_to_idx = {c: i for i, c in enumerate(chars)}

def seq_to_tensor(seq):
    tensor = torch.zeros(len(chars), len(seq))
    for i, c in enumerate(seq):
        tensor[char_to_idx[c], i] = 1
    return tensor

class SeqDataset(Dataset):
    def __init__(self, df):
        self.X = torch.stack([seq_to_tensor(seq) for seq in df['sym_seq']])
        self.y = torch.tensor(df['default_flag'].values, dtype=torch.float32)
        
    def __len__(self):
        return len(self.y)
        
    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

train_dataset = SeqDataset(train)
val_dataset = SeqDataset(val)

train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=32)

class CNNModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv1d(in_channels=len(chars), out_channels=32, kernel_size=3, padding=1)
        self.relu = nn.ReLU()
        self.pool = nn.MaxPool1d(kernel_size=2)
        self.conv2 = nn.Conv1d(in_channels=32, out_channels=64, kernel_size=3, padding=1)
        self.fc1 = nn.Linear(64 * 5, 32)
        self.fc2 = nn.Linear(32, 1)
        
    def forward(self, x):
        x = self.conv1(x)
        x = self.relu(x)
        x = self.pool(x)
        x = self.conv2(x)
        x = self.relu(x)
        x = self.pool(x)
        x = x.view(x.size(0), -1)
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        return torch.sigmoid(x).squeeze()

model = CNNModel()
criterion = nn.BCELoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

for epoch in range(30):
    model.train()
    for X_batch, y_batch in train_loader:
        optimizer.zero_grad()
        y_pred = model(X_batch)
        loss = criterion(y_pred, y_batch)
        loss.backward()
        optimizer.step()
        
    model.eval()
    val_preds = []
    val_targets = []
    with torch.no_grad():
        for X_batch, y_batch in val_loader:
            y_pred = model(X_batch)
            val_preds.extend(y_pred.numpy())
            val_targets.extend(y_batch.numpy())
            
    auc = roc_auc_score(val_targets, val_preds)
    print(f'Epoch {epoch+1}, Val AUC: {auc:.4f}')
