import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns
import os
from tqdm import tqdm

# Set random seeds for reproducibility
torch.manual_seed(42)
np.random.seed(42)

# Load data
train = pd.read_csv('../data/spr_bench_train.csv')
val = pd.read_csv('../data/spr_bench_val.csv')
test = pd.read_csv('../data/spr_bench_test.csv')

feature_cols = [c for c in train.columns if c.startswith('token_')]
X_train = train[feature_cols]
y_train = train['label'].values
X_val = val[feature_cols]
y_val = val['label'].values
X_test = test[feature_cols]
y_test = test['label'].values

# Create token vocabulary
all_tokens = pd.concat([X_train, X_val, X_test]).values.ravel()
unique_tokens = pd.unique(all_tokens)
token_to_idx = {token: i+1 for i, token in enumerate(unique_tokens)}  # 0 for padding
vocab_size = len(token_to_idx) + 1  # +1 for padding
print(f"Vocabulary size: {vocab_size}")
print(f"Tokens: {unique_tokens}")

# Convert sequences to indices
def tokens_to_indices(df):
    indices = []
    for i in range(df.shape[0]):
        row = df.iloc[i]
        seq = [token_to_idx[token] for token in row]
        indices.append(seq)
    return np.array(indices)

X_train_idx = tokens_to_indices(X_train)
X_val_idx = tokens_to_indices(X_val)
X_test_idx = tokens_to_indices(X_test)

print(f"Sequence length: {X_train_idx.shape[1]}")

# Create PyTorch Dataset
class SequenceDataset(Dataset):
    def __init__(self, sequences, labels):
        self.sequences = torch.LongTensor(sequences)
        self.labels = torch.FloatTensor(labels)
    
    def __len__(self):
        return len(self.sequences)
    
    def __getitem__(self, idx):
        return self.sequences[idx], self.labels[idx]

# Create data loaders
train_dataset = SequenceDataset(X_train_idx, y_train)
val_dataset = SequenceDataset(X_val_idx, y_val)
test_dataset = SequenceDataset(X_test_idx, y_test)

train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False)
test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)

# Define LSTM model
class LSTMModel(nn.Module):
    def __init__(self, vocab_size, embedding_dim=64, hidden_dim=128, num_layers=2):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        self.lstm = nn.LSTM(embedding_dim, hidden_dim, num_layers, 
                           batch_first=True, bidirectional=True)
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim * 2, 64),  # *2 for bidirectional
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )
    
    def forward(self, x):
        embedded = self.embedding(x)
        lstm_out, _ = self.lstm(embedded)
        # Use the last hidden state
        last_hidden = lstm_out[:, -1, :]
        output = self.fc(last_hidden)
        return output.squeeze()

# Define Transformer model
class TransformerModel(nn.Module):
    def __init__(self, vocab_size, embedding_dim=64, num_heads=4, num_layers=2):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embedding_dim, 
            nhead=num_heads,
            dim_feedforward=128,
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.fc = nn.Sequential(
            nn.Linear(embedding_dim, 32),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )
    
    def forward(self, x):
        embedded = self.embedding(x)
        transformer_out = self.transformer(embedded)
        # Use the first token's output (like [CLS] token)
        cls_output = transformer_out[:, 0, :]
        output = self.fc(cls_output)
        return output.squeeze()

# Training function
def train_model(model, train_loader, val_loader, num_epochs=20, lr=0.001):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = model.to(device)
    
    criterion = nn.BCELoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)
    
    train_losses = []
    val_losses = []
    val_accuracies = []
    
    for epoch in range(num_epochs):
        # Training
        model.train()
        train_loss = 0
        for batch_x, batch_y in tqdm(train_loader, desc=f'Epoch {epoch+1}/{num_epochs}'):
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            
            optimizer.zero_grad()
            outputs = model(batch_x)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
        
        avg_train_loss = train_loss / len(train_loader)
        train_losses.append(avg_train_loss)
        
        # Validation
        model.eval()
        val_loss = 0
        all_preds = []
        all_labels = []
        
        with torch.no_grad():
            for batch_x, batch_y in val_loader:
                batch_x, batch_y = batch_x.to(device), batch_y.to(device)
                outputs = model(batch_x)
                loss = criterion(outputs, batch_y)
                val_loss += loss.item()
                
                preds = (outputs > 0.5).float()
                all_preds.extend(preds.cpu().numpy())
                all_labels.extend(batch_y.cpu().numpy())
        
        avg_val_loss = val_loss / len(val_loader)
        val_losses.append(avg_val_loss)
        
        val_acc = accuracy_score(all_labels, all_preds)
        val_accuracies.append(val_acc)
        
        print(f"Epoch {epoch+1}: Train Loss = {avg_train_loss:.4f}, Val Loss = {avg_val_loss:.4f}, Val Acc = {val_acc:.4f}")
    
    return model, train_losses, val_losses, val_accuracies

# Test function
def test_model(model, test_loader):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.eval()
    
    all_preds = []
    all_labels = []
    
    with torch.no_grad():
        for batch_x, batch_y in test_loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            outputs = model(batch_x)
            preds = (outputs > 0.5).float()
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(batch_y.cpu().numpy())
    
    test_acc = accuracy_score(all_labels, all_preds)
    return test_acc

# Train LSTM model
print("\n" + "="*50)
print("Training LSTM model")
print("="*50)
lstm_model = LSTMModel(vocab_size)
lstm_model, lstm_train_loss, lstm_val_loss, lstm_val_acc = train_model(
    lstm_model, train_loader, val_loader, num_epochs=15, lr=0.001
)

# Test LSTM
lstm_test_acc = test_model(lstm_model, test_loader)
print(f"\nLSTM Test Accuracy: {lstm_test_acc:.4f}")

# Train Transformer model
print("\n" + "="*50)
print("Training Transformer model")
print("="*50)
transformer_model = TransformerModel(vocab_size)
transformer_model, trans_train_loss, trans_val_loss, trans_val_acc = train_model(
    transformer_model, train_loader, val_loader, num_epochs=15, lr=0.001
)

# Test Transformer
trans_test_acc = test_model(transformer_model, test_loader)
print(f"\nTransformer Test Accuracy: {trans_test_acc:.4f}")

# Compare with SOTA
sota_acc = 0.70
print("\n" + "="*50)
print("COMPARISON WITH SOTA (70%)")
print("="*50)
print(f"LSTM Test Accuracy: {lstm_test_acc:.2%}")
print(f"Transformer Test Accuracy: {trans_test_acc:.2%}")
print(f"SOTA: {sota_acc:.2%}")

if lstm_test_acc >= sota_acc:
    print("LSTM achieves or exceeds SOTA!")
else:
    print(f"LSTM is {sota_acc - lstm_test_acc:.2%} below SOTA")

if trans_test_acc >= sota_acc:
    print("Transformer achieves or exceeds SOTA!")
else:
    print(f"Transformer is {sota_acc - trans_test_acc:.2%} below SOTA")

# Plot training curves
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# LSTM training curves
axes[0, 0].plot(lstm_train_loss, label='Train Loss')
axes[0, 0].plot(lstm_val_loss, label='Val Loss')
axes[0, 0].set_title('LSTM: Training and Validation Loss')
axes[0, 0].set_xlabel('Epoch')
axes[0, 0].set_ylabel('Loss')
axes[0, 0].legend()
axes[0, 0].grid(True, alpha=0.3)

axes[0, 1].plot(lstm_val_acc, label='Val Accuracy', color='green')
axes[0, 1].axhline(y=sota_acc, color='r', linestyle='--', label=f'SOTA ({sota_acc:.0%})')
axes[0, 1].set_title('LSTM: Validation Accuracy')
axes[0, 1].set_xlabel('Epoch')
axes[0, 1].set_ylabel('Accuracy')
axes[0, 1].legend()
axes[0, 1].grid(True, alpha=0.3)

# Transformer training curves
axes[1, 0].plot(trans_train_loss, label='Train Loss')
axes[1, 0].plot(trans_val_loss, label='Val Loss')
axes[1, 0].set_title('Transformer: Training and Validation Loss')
axes[1, 0].set_xlabel('Epoch')
axes[1, 0].set_ylabel('Loss')
axes[1, 0].legend()
axes[1, 0].grid(True, alpha=0.3)

axes[1, 1].plot(trans_val_acc, label='Val Accuracy', color='green')
axes[1, 1].axhline(y=sota_acc, color='r', linestyle='--', label=f'SOTA ({sota_acc:.0%})')
axes[1, 1].set_title('Transformer: Validation Accuracy')
axes[1, 1].set_xlabel('Epoch')
axes[1, 1].set_ylabel('Accuracy')
axes[1, 1].legend()
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/sequence_models_training.png', dpi=300)
print("\nTraining curves saved to report/images/sequence_models_training.png")

# Create final comparison bar chart
models = ['LSTM', 'Transformer']
accuracies = [lstm_test_acc, trans_test_acc]

plt.figure(figsize=(8, 5))
ax = sns.barplot(x=models, y=accuracies)
plt.axhline(y=sota_acc, color='r', linestyle='--', label=f'SOTA ({sota_acc:.0%})')
plt.title('Sequence Models: Test Accuracy vs SOTA')
plt.ylabel('Test Accuracy')
plt.ylim(0, 1.0)
for i, v in enumerate(accuracies):
    ax.text(i, v + 0.01, f'{v:.2%}', ha='center')
plt.legend()
plt.tight_layout()
plt.savefig('../report/images/sequence_models_vs_sota.png', dpi=300)
print("Comparison chart saved to report/images/sequence_models_vs_sota.png")

# Save results
results_df = pd.DataFrame({
    'Model': ['LSTM', 'Transformer'],
    'Test Accuracy': [lstm_test_acc, trans_test_acc]
})
results_df.to_csv('../outputs/sequence_model_results.csv', index=False)
print("Results saved to outputs/sequence_model_results.csv")