import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import balanced_accuracy_score

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

chars = sorted(list(set(''.join(train['symbol_series']))))
char_to_idx = {c: i for i, c in enumerate(chars)}

class SymbolDataset(Dataset):
    def __init__(self, df):
        self.data = []
        self.labels = []
        for _, row in df.iterrows():
            seq = [char_to_idx[c] for c in row['symbol_series']]
            self.data.append(seq)
            self.labels.append(row['label'])
            
    def __len__(self):
        return len(self.data)
        
    def __getitem__(self, idx):
        return torch.tensor(self.data[idx], dtype=torch.long), torch.tensor(self.labels[idx], dtype=torch.float32)

train_dataset = SymbolDataset(train)
val_dataset = SymbolDataset(val)

train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False)

class LSTMClassifier(nn.Module):
    def __init__(self, vocab_size, embedding_dim, hidden_dim, output_dim):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim)
        self.lstm = nn.LSTM(embedding_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, output_dim)
        
    def forward(self, text):
        embedded = self.embedding(text)
        output, (hidden, cell) = self.lstm(embedded)
        hidden = hidden.squeeze(0)
        return self.fc(hidden)

model = LSTMClassifier(len(chars), 16, 32, 1)
optimizer = optim.Adam(model.parameters(), lr=0.001)
criterion = nn.BCEWithLogitsLoss()

for epoch in range(20):
    model.train()
    for batch_text, batch_labels in train_loader:
        optimizer.zero_grad()
        predictions = model(batch_text).squeeze(1)
        loss = criterion(predictions, batch_labels)
        loss.backward()
        optimizer.step()
        
    model.eval()
    all_preds = []
    all_labels = []
    with torch.no_grad():
        for batch_text, batch_labels in val_loader:
            predictions = model(batch_text).squeeze(1)
            preds = torch.round(torch.sigmoid(predictions))
            all_preds.extend(preds.numpy())
            all_labels.extend(batch_labels.numpy())
            
    acc = balanced_accuracy_score(all_labels, all_preds)
    print(f'Epoch {epoch+1} Val Balanced Acc: {acc:.4f}')
