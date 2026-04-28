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

chars = sorted(list(set(''.join(train['sym_seq']))))
char_to_idx = {c: i for i, c in enumerate(chars)}

def seq_to_tensor(seqs):
    tensor = torch.zeros(len(seqs), len(seqs[0]), dtype=torch.long)
    for i, seq in enumerate(seqs):
        for j, char in enumerate(seq):
            tensor[i, j] = char_to_idx[char]
    return tensor

X_train = seq_to_tensor(train['sym_seq'].values)
y_train = torch.tensor(train['default_flag'].values, dtype=torch.float32)

X_val = seq_to_tensor(val['sym_seq'].values)
y_val = torch.tensor(val['default_flag'].values, dtype=torch.float32)

class SeqDataset(Dataset):
    def __init__(self, X, y):
        self.X = X
        self.y = y
    def __len__(self):
        return len(self.X)
    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

train_loader = DataLoader(SeqDataset(X_train, y_train), batch_size=32, shuffle=True)
val_loader = DataLoader(SeqDataset(X_val, y_val), batch_size=32)

class LSTMModel(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.lstm = nn.LSTM(embed_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, 1)
        
    def forward(self, x):
        embedded = self.embedding(x)
        _, (hidden, _) = self.lstm(embedded)
        out = self.fc(hidden[-1])
        return torch.sigmoid(out).squeeze()

model = LSTMModel(len(chars), 16, 32)
criterion = nn.BCELoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

for epoch in range(50):
    model.train()
    for X_batch, y_batch in train_loader:
        optimizer.zero_grad()
        y_pred = model(X_batch)
        loss = criterion(y_pred, y_batch)
        loss.backward()
        optimizer.step()
        
    model.eval()
    with torch.no_grad():
        val_preds = []
        for X_batch, _ in val_loader:
            val_preds.extend(model(X_batch).numpy())
        auc = roc_auc_score(y_val.numpy(), val_preds)
    if (epoch + 1) % 10 == 0:
        print(f'Epoch {epoch+1}, Val AUC: {auc:.4f}')
