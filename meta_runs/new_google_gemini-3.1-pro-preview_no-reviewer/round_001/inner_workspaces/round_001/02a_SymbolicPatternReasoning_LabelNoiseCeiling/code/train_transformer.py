import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.metrics import accuracy_score

train = pd.read_csv('data/spr_bench_train.csv')
val = pd.read_csv('data/spr_bench_val.csv')
test = pd.read_csv('data/spr_bench_test.csv')

feature_cols = [c for c in train.columns if c.startswith('token_')]

all_tokens = [f"{s}{c}" for s in ['T', 'S', 'C', 'D'] for c in ['r', 'g', 'b', 'y']]
token_to_idx = {t: i for i, t in enumerate(all_tokens)}

def encode_data(df):
    X = np.zeros((len(df), len(feature_cols)), dtype=np.int64)
    for i, row in enumerate(df[feature_cols].values):
        for j, token in enumerate(row):
            X[i, j] = token_to_idx[token]
    return X

X_train = encode_data(train)
y_train = train['label'].values
X_val = encode_data(val)
y_val = val['label'].values
X_test = encode_data(test)
y_test = test['label'].values

X_train_tensor = torch.tensor(X_train)
y_train_tensor = torch.tensor(y_train, dtype=torch.float32).unsqueeze(1)
X_val_tensor = torch.tensor(X_val)
y_val_tensor = torch.tensor(y_val, dtype=torch.float32).unsqueeze(1)
X_test_tensor = torch.tensor(X_test)
y_test_tensor = torch.tensor(y_test, dtype=torch.float32).unsqueeze(1)

train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)

class SimpleTransformer(nn.Module):
    def __init__(self, vocab_size=16, d_model=32, nhead=4, num_layers=2):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, d_model)
        self.pos_encoder = nn.Parameter(torch.zeros(1, 8, d_model))
        encoder_layer = nn.TransformerEncoderLayer(d_model=d_model, nhead=nhead, batch_first=True)
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.fc = nn.Linear(d_model, 1)
        self.sigmoid = nn.Sigmoid()
        
    def forward(self, x):
        x = self.embedding(x) + self.pos_encoder
        x = self.transformer_encoder(x)
        x = x.mean(dim=1) # Global average pooling
        x = self.fc(x)
        return self.sigmoid(x)

model = SimpleTransformer()
criterion = nn.BCELoss()
optimizer = optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-4)

best_val_acc = 0

print("Training Transformer...")
for epoch in range(50):
    model.train()
    for inputs, labels in train_loader:
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
    model.eval()
    with torch.no_grad():
        train_preds = (model(X_train_tensor) > 0.5).float()
        train_acc = accuracy_score(y_train, train_preds.numpy())
        
        val_preds = (model(X_val_tensor) > 0.5).float()
        val_acc = accuracy_score(y_val, val_preds.numpy())
        
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            
    if (epoch+1) % 10 == 0:
        print(f"Epoch {epoch+1}, Loss: {loss.item():.4f}, Train Acc: {train_acc:.4f}, Val Acc: {val_acc:.4f}")

print(f"\nBest Val Acc: {best_val_acc:.4f}")
