import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import balanced_accuracy_score

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

class LSTMModel(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, num_layers):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.lstm = nn.LSTM(embed_dim, hidden_dim, num_layers, batch_first=True, bidirectional=True)
        self.fc = nn.Linear(hidden_dim * 2, 1)
        self.sigmoid = nn.Sigmoid()
        
    def forward(self, x):
        x = self.embedding(x)
        out, _ = self.lstm(x)
        out = out[:, -1, :] # Take last hidden state
        out = self.fc(out)
        return self.sigmoid(out).squeeze()

model = LSTMModel(vocab_size=len(chars), embed_dim=16, hidden_dim=32, num_layers=2)
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
