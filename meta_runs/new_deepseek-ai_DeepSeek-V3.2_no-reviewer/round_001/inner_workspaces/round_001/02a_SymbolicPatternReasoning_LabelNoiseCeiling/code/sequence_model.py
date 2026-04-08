import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import accuracy_score
import warnings
warnings.filterwarnings('ignore')

# Check if GPU is available
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")

# Load data
train = pd.read_csv('../data/spr_bench_train.csv')
val = pd.read_csv('../data/spr_bench_val.csv')
test = pd.read_csv('../data/spr_bench_test.csv')

# Extract features and labels
feature_cols = [f"token_{i}" for i in range(8)]
X_train_raw = train[feature_cols]
y_train = train['label'].values
X_val_raw = val[feature_cols]
y_val = val['label'].values
X_test_raw = test[feature_cols]
y_test = test['label'].values

print(f"Data shapes: Train {X_train_raw.shape}, Val {X_val_raw.shape}, Test {X_test_raw.shape}")
print()

# Create vocabulary
all_tokens = pd.concat([X_train_raw, X_val_raw, X_test_raw]).values.ravel()
unique_tokens = sorted(set(all_tokens))
token_to_idx = {token: i+1 for i, token in enumerate(unique_tokens)}  # 0 for padding
idx_to_token = {i+1: token for i, token in enumerate(unique_tokens)}
vocab_size = len(unique_tokens) + 1  # +1 for padding

print(f"Vocabulary size: {vocab_size} (including padding)")
print(f"Unique tokens: {unique_tokens}")
print()

# Convert sequences to indices
def sequences_to_indices(X):
    indices = []
    for _, row in X.iterrows():
        seq_indices = [token_to_idx[token] for token in row]
        indices.append(seq_indices)
    return np.array(indices)

X_train_idx = sequences_to_indices(X_train_raw)
X_val_idx = sequences_to_indices(X_val_raw)
X_test_idx = sequences_to_indices(X_test_raw)

print(f"Example sequence: {X_train_raw.iloc[0].tolist()}")
print(f"As indices: {X_train_idx[0]}")
print()

# Create Dataset
class SPRDataset(Dataset):
    def __init__(self, sequences, labels):
        self.sequences = torch.LongTensor(sequences)
        self.labels = torch.FloatTensor(labels)
        
    def __len__(self):
        return len(self.sequences)
    
    def __getitem__(self, idx):
        return self.sequences[idx], self.labels[idx]

# Create data loaders
train_dataset = SPRDataset(X_train_idx, y_train)
val_dataset = SPRDataset(X_val_idx, y_val)
test_dataset = SPRDataset(X_test_idx, y_test)

train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False)
test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)

# Define model
class SPRTransformer(nn.Module):
    def __init__(self, vocab_size, embed_dim=64, num_heads=4, num_layers=2, hidden_dim=128):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.positional_encoding = nn.Parameter(torch.zeros(1, 8, embed_dim))
        
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embed_dim,
            nhead=num_heads,
            dim_feedforward=hidden_dim,
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        self.fc = nn.Sequential(
            nn.Linear(embed_dim * 8, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )
        
    def forward(self, x):
        # x shape: (batch, seq_len)
        embedded = self.embedding(x)  # (batch, seq_len, embed_dim)
        embedded = embedded + self.positional_encoding[:, :embedded.size(1), :]
        
        # Transformer expects (seq_len, batch, embed_dim) for attention mask
        # But we're using batch_first=True
        transformer_out = self.transformer(embedded)  # (batch, seq_len, embed_dim)
        
        # Flatten
        flattened = transformer_out.reshape(transformer_out.size(0), -1)  # (batch, seq_len*embed_dim)
        
        output = self.fc(flattened).squeeze()  # (batch,)
        return output

# Also try a simpler LSTM model
class SPRLSTM(nn.Module):
    def __init__(self, vocab_size, embed_dim=64, hidden_dim=128, num_layers=2):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.lstm = nn.LSTM(
            input_size=embed_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=0.3 if num_layers > 1 else 0
        )
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim * 2, 64),  # *2 for bidirectional
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )
        
    def forward(self, x):
        embedded = self.embedding(x)  # (batch, seq_len, embed_dim)
        lstm_out, (hidden, cell) = self.lstm(embedded)  # lstm_out: (batch, seq_len, hidden_dim*2)
        
        # Use the last hidden state
        last_hidden = torch.cat((hidden[-2], hidden[-1]), dim=1)  # (batch, hidden_dim*2)
        output = self.fc(last_hidden).squeeze()  # (batch,)
        return output

# Training function
def train_model(model, train_loader, val_loader, num_epochs=20, lr=0.001):
    model = model.to(device)
    criterion = nn.BCELoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)
    
    train_losses = []
    val_accuracies = []
    
    for epoch in range(num_epochs):
        # Training
        model.train()
        epoch_loss = 0
        
        for batch_idx, (sequences, labels) in enumerate(train_loader):
            sequences, labels = sequences.to(device), labels.to(device)
            
            optimizer.zero_grad()
            outputs = model(sequences)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item()
        
        avg_train_loss = epoch_loss / len(train_loader)
        train_losses.append(avg_train_loss)
        
        # Validation
        model.eval()
        val_preds = []
        val_true = []
        
        with torch.no_grad():
            for sequences, labels in val_loader:
                sequences, labels = sequences.to(device), labels.to(device)
                outputs = model(sequences)
                preds = (outputs > 0.5).float().cpu().numpy()
                val_preds.extend(preds)
                val_true.extend(labels.cpu().numpy())
        
        val_acc = accuracy_score(val_true, val_preds)
        val_accuracies.append(val_acc)
        
        if (epoch + 1) % 5 == 0:
            print(f"Epoch {epoch+1}/{num_epochs}, Train Loss: {avg_train_loss:.4f}, Val Acc: {val_acc:.4f}")
    
    return model, train_losses, val_accuracies

# Test function
def test_model(model, test_loader):
    model.eval()
    test_preds = []
    test_true = []
    
    with torch.no_grad():
        for sequences, labels in test_loader:
            sequences, labels = sequences.to(device), labels.to(device)
            outputs = model(sequences)
            preds = (outputs > 0.5).float().cpu().numpy()
            test_preds.extend(preds)
            test_true.extend(labels.cpu().numpy())
    
    test_acc = accuracy_score(test_true, test_preds)
    return test_acc, test_preds, test_true

# Try Transformer
print("Training Transformer model...")
transformer_model = SPRTransformer(vocab_size)
transformer_model, t_losses, t_val_accs = train_model(transformer_model, train_loader, val_loader, num_epochs=30)
transformer_test_acc, t_preds, t_true = test_model(transformer_model, test_loader)
print(f"Transformer Test Accuracy: {transformer_test_acc:.4f}")
print()

# Try LSTM
print("Training LSTM model...")
lstm_model = SPRLSTM(vocab_size)
lstm_model, l_losses, l_val_accs = train_model(lstm_model, train_loader, val_loader, num_epochs=30)
lstm_test_acc, l_preds, l_true = test_model(lstm_model, test_loader)
print(f"LSTM Test Accuracy: {lstm_test_acc:.4f}")
print()

# Compare with baseline
baseline_acc = max(y_test.mean(), 1 - y_test.mean())
print(f"Baseline (majority class) accuracy: {baseline_acc:.4f}")
print(f"Transformer improvement over baseline: {transformer_test_acc - baseline_acc:.4f}")
print(f"LSTM improvement over baseline: {lstm_test_acc - baseline_acc:.4f}")
print()

# Plot training curves
import matplotlib.pyplot as plt

plt.figure(figsize=(12, 4))

plt.subplot(1, 2, 1)
plt.plot(t_losses, label='Transformer')
plt.plot(l_losses, label='LSTM')
plt.xlabel('Epoch')
plt.ylabel('Training Loss')
plt.title('Training Loss Curves')
plt.legend()
plt.grid(True, alpha=0.3)

plt.subplot(1, 2, 2)
plt.plot(t_val_accs, label='Transformer')
plt.plot(l_val_accs, label='LSTM')
plt.axhline(y=baseline_acc, color='r', linestyle='--', label='Baseline')
plt.axhline(y=0.70, color='g', linestyle='--', label='SOTA (70%)')
plt.xlabel('Epoch')
plt.ylabel('Validation Accuracy')
plt.title('Validation Accuracy Curves')
plt.legend()
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/sequence_model_training.png', dpi=300, bbox_inches='tight')
print("Training curves saved to '../report/images/sequence_model_training.png'")

# Save results
results = pd.DataFrame({
    'Model': ['Baseline', 'Transformer', 'LSTM'],
    'Test Accuracy': [baseline_acc, transformer_test_acc, lstm_test_acc]
})

print("\nFinal Results:")
print(results.to_string(index=False))

# Check if we're close to SOTA
sota = 0.70
print(f"\nSOTA: {sota:.2%}")
print(f"Best model (LSTM) is {((lstm_test_acc - sota)/sota)*100:.1f}% below SOTA")
