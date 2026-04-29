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

class CNN1D(nn.Module):
    def __init__(self, vocab_size, embed_dim, num_classes):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.conv1 = nn.Conv1d(embed_dim, 64, kernel_size=3, padding=1)
        self.relu = nn.ReLU()
        self.pool = nn.MaxPool1d(2)
        self.conv2 = nn.Conv1d(64, 128, kernel_size=3, padding=1)
        self.fc1 = nn.Linear(128 * 10, 64)
        self.fc2 = nn.Linear(64, 1)
        self.sigmoid = nn.Sigmoid()
        
    def forward(self, x):
        x = self.embedding(x) # (batch, seq_len, embed_dim)
        x = x.permute(0, 2, 1) # (batch, embed_dim, seq_len)
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
        return self.sigmoid(x).squeeze()

model = CNN1D(vocab_size=len(chars), embed_dim=16, num_classes=1)
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
