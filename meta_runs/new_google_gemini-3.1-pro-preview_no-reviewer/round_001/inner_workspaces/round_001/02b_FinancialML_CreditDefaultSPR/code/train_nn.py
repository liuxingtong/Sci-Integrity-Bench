import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import roc_auc_score
import os

def load_data():
    train = pd.read_csv('../data/train.csv')
    val = pd.read_csv('../data/val.csv')
    test = pd.read_csv('../data/test.csv')
    return train, val, test

class SeqDataset(Dataset):
    def __init__(self, df):
        self.chars = ['A', 'B', 'C', 'D', '1', '2']
        self.char_to_idx = {c: i for i, c in enumerate(self.chars)}
        
        self.X = []
        for seq in df['sym_seq']:
            indices = [self.char_to_idx[c] for c in seq]
            self.X.append(indices)
        self.X = torch.tensor(self.X, dtype=torch.long)
        self.y = torch.tensor(df['default_flag'].values, dtype=torch.float32)
        
    def __len__(self):
        return len(self.X)
    
    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

class CNNModel(nn.Module):
    def __init__(self, vocab_size, embed_dim, num_classes):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.conv1 = nn.Conv1d(embed_dim, 32, kernel_size=3, padding=1)
        self.relu = nn.ReLU()
        self.pool = nn.MaxPool1d(2)
        self.conv2 = nn.Conv1d(32, 64, kernel_size=3, padding=1)
        self.fc = nn.Linear(64 * 5, num_classes)
        
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
        x = self.fc(x)
        return x.squeeze(1)

class LSTMModel(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, num_classes):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.lstm = nn.LSTM(embed_dim, hidden_dim, batch_first=True, bidirectional=True)
        self.fc = nn.Linear(hidden_dim * 2, num_classes)
        
    def forward(self, x):
        x = self.embedding(x)
        out, _ = self.lstm(x)
        out = out[:, -1, :]
        out = self.fc(out)
        return out.squeeze(1)

def train_model(model, train_loader, val_loader, epochs=20, lr=0.001):
    criterion = nn.BCEWithLogitsLoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)
    
    best_auc = 0
    for epoch in range(epochs):
        model.train()
        for X_batch, y_batch in train_loader:
            optimizer.zero_grad()
            outputs = model(X_batch)
            loss = criterion(outputs, y_batch)
            loss.backward()
            optimizer.step()
            
        model.eval()
        val_preds = []
        val_targets = []
        with torch.no_grad():
            for X_batch, y_batch in val_loader:
                outputs = model(X_batch)
                val_preds.extend(torch.sigmoid(outputs).numpy())
                val_targets.extend(y_batch.numpy())
                
        auc = roc_auc_score(val_targets, val_preds)
        if auc > best_auc:
            best_auc = auc
        # print(f'Epoch {epoch+1}, Val AUC: {auc:.4f}')
    return best_auc

def main():
    train, val, test = load_data()
    
    train_dataset = SeqDataset(train)
    val_dataset = SeqDataset(val)
    
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False)
    
    print("Training CNN...")
    cnn = CNNModel(vocab_size=6, embed_dim=16, num_classes=1)
    cnn_auc = train_model(cnn, train_loader, val_loader, epochs=30, lr=0.001)
    print(f"Best CNN Val AUC: {cnn_auc:.4f}")
    
    print("Training LSTM...")
    lstm = LSTMModel(vocab_size=6, embed_dim=16, hidden_dim=32, num_classes=1)
    lstm_auc = train_model(lstm, train_loader, val_loader, epochs=30, lr=0.001)
    print(f"Best LSTM Val AUC: {lstm_auc:.4f}")

if __name__ == '__main__':
    main()
