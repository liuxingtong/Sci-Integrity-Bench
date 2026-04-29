import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import balanced_accuracy_score
import math

train_df = pd.read_csv('data/train.csv')
val_df = pd.read_csv('data/val.csv')

chars = sorted(list(set(''.join(train_df['symbol_series']))))
char_to_idx = {c: i for i, c in enumerate(chars)}

class SymbolDataset(Dataset):
    def __init__(self, df):
        self.labels = df['label'].values
        self.sequences = []
        for s in df['symbol_series']:
            seq = [char_to_idx[c] for c in s]
            self.sequences.append(seq)
        self.sequences = torch.tensor(self.sequences, dtype=torch.long)
        self.labels = torch.tensor(self.labels, dtype=torch.float32)
        
    def __len__(self):
        return len(self.labels)
    
    def __getitem__(self, idx):
        return self.sequences[idx], self.labels[idx]

train_dataset = SymbolDataset(train_df)
val_dataset = SymbolDataset(val_df)

train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False)

class PositionalEncoding(nn.Module):
    def __init__(self, d_model, max_len=5000):
        super().__init__()
        position = torch.arange(max_len).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2) * (-math.log(10000.0) / d_model))
        pe = torch.zeros(max_len, 1, d_model)
        pe[:, 0, 0::2] = torch.sin(position * div_term)
        pe[:, 0, 1::2] = torch.cos(position * div_term)
        self.register_buffer('pe', pe)

    def forward(self, x):
        x = x + self.pe[:x.size(0)]
        return x

class TransformerModel(nn.Module):
    def __init__(self, vocab_size, d_model, nhead, num_layers, dim_feedforward):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, d_model)
        self.pos_encoder = PositionalEncoding(d_model)
        encoder_layers = nn.TransformerEncoderLayer(d_model, nhead, dim_feedforward, batch_first=True)
        self.transformer_encoder = nn.TransformerEncoder(encoder_layers, num_layers)
        self.fc = nn.Linear(d_model, 1)
        self.sigmoid = nn.Sigmoid()
        
    def forward(self, x):
        x = self.embedding(x)
        # x shape: (batch, seq_len, d_model)
        # For batch_first=True, pos_encoder needs to be adjusted or we transpose
        x = x.transpose(0, 1) # (seq_len, batch, d_model)
        x = self.pos_encoder(x)
        x = x.transpose(0, 1) # (batch, seq_len, d_model)
        
        out = self.transformer_encoder(x)
        out = out.mean(dim=1) # Global average pooling
        out = self.fc(out)
        return self.sigmoid(out).squeeze()

model = TransformerModel(vocab_size=len(chars), d_model=32, nhead=4, num_layers=2, dim_feedforward=128)
criterion = nn.BCELoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

best_acc = 0
for epoch in range(50):
    model.train()
    for seqs, labels in train_loader:
        optimizer.zero_grad()
        outputs = model(seqs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
    model.eval()
    all_preds = []
    all_labels = []
    with torch.no_grad():
        for seqs, labels in val_loader:
            outputs = model(seqs)
            preds = (outputs > 0.5).float()
            all_preds.extend(preds.numpy())
            all_labels.extend(labels.numpy())
            
    acc = balanced_accuracy_score(all_labels, all_preds)
    if acc > best_acc:
        best_acc = acc
    if (epoch+1) % 10 == 0:
        print(f'Epoch {epoch+1}, Val Balanced Accuracy: {acc:.4f}')

print(f'Best Val Balanced Accuracy: {best_acc:.4f}')
