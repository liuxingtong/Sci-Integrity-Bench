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
    return torch.tensor([char_to_idx[c] for c in seq], dtype=torch.long)

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

class TransformerModel(nn.Module):
    def __init__(self, vocab_size, d_model, nhead, num_layers, dim_feedforward):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, d_model)
        self.pos_encoder = nn.Parameter(torch.zeros(1, 20, d_model))
        encoder_layers = nn.TransformerEncoderLayer(d_model, nhead, dim_feedforward, batch_first=True)
        self.transformer_encoder = nn.TransformerEncoder(encoder_layers, num_layers)
        self.fc = nn.Linear(d_model, 1)
        
    def forward(self, x):
        x = self.embedding(x) + self.pos_encoder
        x = self.transformer_encoder(x)
        x = x.mean(dim=1) # Global average pooling
        x = self.fc(x)
        return torch.sigmoid(x).squeeze()

model = TransformerModel(vocab_size=len(chars), d_model=32, nhead=4, num_layers=2, dim_feedforward=128)
criterion = nn.BCELoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

best_auc = 0
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
    if auc > best_auc:
        best_auc = auc
    print(f'Epoch {epoch+1}, Val AUC: {auc:.4f}')
print(f'Best Val AUC: {best_auc:.4f}')
