import pandas as pd
import numpy as np
import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.metrics import accuracy_score
import warnings
warnings.filterwarnings('ignore')

# Load registry
with open('../data/benchmark_registry.json') as f:
    registry = json.load(f)

selected = ['FDLOT', 'RHHQD', 'ILULR', 'ZOBKB']

results = []

def load_benchmark(code):
    train = pd.read_csv(f'../data/{code}_train.csv')
    val = pd.read_csv(f'../data/{code}_val.csv')
    test = pd.read_csv(f'../data/{code}_test.csv')
    return train, val, test

class TokenEncoder:
    def __init__(self):
        self.token_to_idx = {}
        self.idx_to_token = {}
    def fit(self, tokens_series):
        unique = pd.unique(tokens_series)
        for i, token in enumerate(unique):
            self.token_to_idx[token] = i
            self.idx_to_token[i] = token
    def transform(self, tokens_series):
        return tokens_series.map(self.token_to_idx).values
    def vocab_size(self):
        return len(self.token_to_idx)

class LSTMModel(nn.Module):
    def __init__(self, vocab_size, embedding_dim=16, hidden_dim=32, num_layers=1, dropout=0.2):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        self.lstm = nn.LSTM(embedding_dim, hidden_dim, num_layers, batch_first=True, dropout=dropout if num_layers>1 else 0)
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_dim, 1)
        self.sigmoid = nn.Sigmoid()
    def forward(self, x):
        emb = self.embedding(x)
        lstm_out, _ = self.lstm(emb)
        # Take last time step
        last = lstm_out[:, -1, :]
        last = self.dropout(last)
        out = self.fc(last)
        return self.sigmoid(out).squeeze()

def train_model(model, train_loader, val_loader, epochs=50, lr=0.001):
    criterion = nn.BCELoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)
    best_val_acc = 0
    best_model_state = None
    for epoch in range(epochs):
        model.train()
        train_loss = 0
        for batch_x, batch_y in train_loader:
            optimizer.zero_grad()
            outputs = model(batch_x)
            loss = criterion(outputs, batch_y.float())
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
        # Validation
        model.eval()
        val_preds = []
        val_true = []
        with torch.no_grad():
            for batch_x, batch_y in val_loader:
                outputs = model(batch_x)
                preds = (outputs > 0.5).int()
                val_preds.extend(preds.cpu().numpy())
                val_true.extend(batch_y.cpu().numpy())
        val_acc = accuracy_score(val_true, val_preds)
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_model_state = model.state_dict().copy()
        if (epoch+1) % 20 == 0:
            print(f'  Epoch {epoch+1}, loss: {train_loss/len(train_loader):.4f}, val acc: {val_acc:.4f}')
    # Load best model
    model.load_state_dict(best_model_state)
    return model, best_val_acc

for code in selected:
    print(f'\n=== {code} ===')
    train, val, test = load_benchmark(code)
    token_cols = [c for c in train.columns if c.startswith('token_')]
    seq_len = len(token_cols)
    
    # Encode tokens
    encoder = TokenEncoder()
    # Fit on all tokens from train
    all_tokens = pd.concat([train[col] for col in token_cols])
    encoder.fit(all_tokens)
    vocab_size = encoder.vocab_size()
    print(f'Vocab size: {vocab_size}')
    
    # Convert data to indices
    def df_to_tensor(df):
        indices = np.stack([encoder.transform(df[col]) for col in token_cols], axis=1)
        return torch.tensor(indices, dtype=torch.long), torch.tensor(df['label'].values, dtype=torch.float32)
    
    X_train, y_train = df_to_tensor(train)
    X_val, y_val = df_to_tensor(val)
    X_test, y_test = df_to_tensor(test)
    
    # Create dataloaders
    train_dataset = TensorDataset(X_train, y_train)
    val_dataset = TensorDataset(X_val, y_val)
    test_dataset = TensorDataset(X_test, y_test)
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)
    
    # Model
    model = LSTMModel(vocab_size, embedding_dim=16, hidden_dim=32, num_layers=1, dropout=0.3)
    
    # Train
    model, best_val_acc = train_model(model, train_loader, val_loader, epochs=100, lr=0.001)
    print(f'Best validation accuracy: {best_val_acc:.4f}')
    
    # Evaluate on test
    model.eval()
    test_preds = []
    test_true = []
    with torch.no_grad():
        for batch_x, batch_y in test_loader:
            outputs = model(batch_x)
            preds = (outputs > 0.5).int()
            test_preds.extend(preds.cpu().numpy())
            test_true.extend(batch_y.cpu().numpy())
    test_acc = accuracy_score(test_true, test_preds)
    sota = registry[code]['sota_accuracy']
    print(f'Test accuracy: {test_acc:.4f}')
    print(f'SOTA accuracy: {sota:.1f}%')
    print(f'Difference (ours - SOTA): {(test_acc*100 - sota):.2f}%')
    
    results.append({
        'benchmark': code,
        'test_accuracy': test_acc,
        'sota_accuracy': sota,
        'difference': test_acc*100 - sota,
        'sequence_length': seq_len,
        'vocab_size': vocab_size
    })

# Save results
df_results = pd.DataFrame(results)
df_results.to_csv('../outputs/lstm_results.csv', index=False)
print('\n=== Summary ===')
print(df_results.to_string(index=False))