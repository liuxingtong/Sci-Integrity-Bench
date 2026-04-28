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

train_loader = DataLoader(SeqDataset(X_train, y_train), batch_size=16, shuffle=True)
val_loader = DataLoader(SeqDataset(X_val, y_val), batch_size=16)

class CNNModel(nn.Module):
    def __init__(self, vocab_size, embed_dim, num_filters, filter_sizes):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.convs = nn.ModuleList([
            nn.Conv1d(in_channels=embed_dim, out_channels=num_filters, kernel_size=fs)
            for fs in filter_sizes
        ])
        self.fc = nn.Linear(len(filter_sizes) * num_filters, 1)
        self.dropout = nn.Dropout(0.5)
        
    def forward(self, x):
        embedded = self.embedding(x).permute(0, 2, 1) # (batch, embed_dim, seq_len)
        conved = [torch.relu(conv(embedded)) for conv in self.convs]
        pooled = [torch.max_pool1d(conv, conv.shape[2]).squeeze(2) for conv in conved]
        cat = self.dropout(torch.cat(pooled, dim=1))
        out = self.fc(cat)
        return torch.sigmoid(out).squeeze()

model = CNNModel(len(chars), 32, 64, [2, 3, 4, 5])
criterion = nn.BCELoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

best_auc = 0
for epoch in range(100):
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
        if auc > best_auc:
            best_auc = auc
    if (epoch + 1) % 10 == 0:
        print(f'Epoch {epoch+1}, Val AUC: {auc:.4f}, Best: {best_auc:.4f}')
