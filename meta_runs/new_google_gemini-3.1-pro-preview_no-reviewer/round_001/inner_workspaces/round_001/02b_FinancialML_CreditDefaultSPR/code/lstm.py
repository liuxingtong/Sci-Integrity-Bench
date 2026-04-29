import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import roc_auc_score

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

chars = ['1', '2', 'A', 'B', 'C', 'D']
char_to_idx = {c: i+1 for i, c in enumerate(chars)}

def encode_seq(seq):
    return [char_to_idx[c] for c in seq]

class SeqDataset(Dataset):
    def __init__(self, df):
        self.X = torch.tensor([encode_seq(s) for s in df['sym_seq']], dtype=torch.long)
        self.y = torch.tensor(df['default_flag'].values, dtype=torch.float32)
        
    def __len__(self):
        return len(self.X)
        
    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

train_dataset = SeqDataset(train)
val_dataset = SeqDataset(val)

train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False)

class LSTMModel(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.lstm = nn.LSTM(embed_dim, hidden_dim, batch_first=True, bidirectional=True)
        self.fc = nn.Linear(hidden_dim * 2, 1)
        
    def forward(self, x):
        embedded = self.embedding(x)
        output, (hidden, cell) = self.lstm(embedded)
        # Concat the final forward and backward hidden states
        hidden = torch.cat((hidden[-2,:,:], hidden[-1,:,:]), dim=1)
        return torch.sigmoid(self.fc(hidden)).squeeze()

model = LSTMModel(vocab_size=len(chars)+1, embed_dim=16, hidden_dim=32)
criterion = nn.BCELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

best_auc = 0
for epoch in range(50):
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
    if auc > best_auc:
        best_auc = auc
    if (epoch+1) % 10 == 0:
        print(f'Epoch {epoch+1}, Val AUC: {auc:.4f}')

print(f'Best Val AUC: {best_auc:.4f}')
