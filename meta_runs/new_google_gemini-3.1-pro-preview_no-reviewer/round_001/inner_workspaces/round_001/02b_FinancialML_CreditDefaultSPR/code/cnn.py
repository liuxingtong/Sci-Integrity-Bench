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
        # x: (batch_size, seq_len)
        embedded = self.embedding(x).permute(0, 2, 1) # (batch_size, embed_dim, seq_len)
        
        conved = [torch.relu(conv(embedded)) for conv in self.convs]
        # conved[n]: (batch_size, num_filters, seq_len - filter_sizes[n] + 1)
        
        pooled = [torch.max_pool1d(conv, conv.shape[2]).squeeze(2) for conv in conved]
        # pooled[n]: (batch_size, num_filters)
        
        cat = self.dropout(torch.cat(pooled, dim=1))
        # cat: (batch_size, len(filter_sizes) * num_filters)
        
        return torch.sigmoid(self.fc(cat)).squeeze()

model = CNNModel(vocab_size=len(chars)+1, embed_dim=32, num_filters=64, filter_sizes=[2, 3, 4, 5])
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
