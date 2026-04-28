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

class CNNClassifier(nn.Module):
    def __init__(self, vocab_size, embedding_dim, num_filters, filter_sizes, output_dim):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim)
        self.convs = nn.ModuleList([
            nn.Conv1d(in_channels=embedding_dim, out_channels=num_filters, kernel_size=fs)
            for fs in filter_sizes
        ])
        self.fc = nn.Linear(len(filter_sizes) * num_filters, output_dim)
        self.dropout = nn.Dropout(0.5)
        
    def forward(self, text):
        # text: [batch size, sent len]
        embedded = self.embedding(text)
        # embedded: [batch size, sent len, emb dim]
        embedded = embedded.permute(0, 2, 1)
        # embedded: [batch size, emb dim, sent len]
        
        conved = [torch.relu(conv(embedded)) for conv in self.convs]
        # conved_n: [batch size, num_filters, sent len - filter_sizes[n] + 1]
        
        pooled = [torch.max_pool1d(conv, conv.shape[2]).squeeze(2) for conv in conved]
        # pooled_n: [batch size, num_filters]
        
        cat = self.dropout(torch.cat(pooled, dim=1))
        # cat: [batch size, num_filters * len(filter_sizes)]
        
        return self.fc(cat)

model = CNNClassifier(len(chars), 32, 100, [2, 3, 4, 5], 1)
optimizer = optim.Adam(model.parameters(), lr=0.001)
criterion = nn.BCEWithLogitsLoss()

best_acc = 0
for epoch in range(30):
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
    if acc > best_acc:
        best_acc = acc
    print(f'Epoch {epoch+1} Val Balanced Acc: {acc:.4f}')
print(f'Best Val Balanced Acc: {best_acc:.4f}')
