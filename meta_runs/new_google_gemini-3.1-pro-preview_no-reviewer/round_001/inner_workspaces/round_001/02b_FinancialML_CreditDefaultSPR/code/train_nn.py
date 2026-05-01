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
    tensor = torch.zeros(len(seq), len(chars))
    for i, c in enumerate(seq):
        tensor[i, char_to_idx[c]] = 1
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

class LSTMModel(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, 1)
        
    def forward(self, x):
        out, _ = self.lstm(x)
        out = self.fc(out[:, -1, :])
        return torch.sigmoid(out).squeeze()

model = LSTMModel(input_size=len(chars), hidden_size=32, num_layers=1)
criterion = nn.BCELoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

for epoch in range(20):
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
