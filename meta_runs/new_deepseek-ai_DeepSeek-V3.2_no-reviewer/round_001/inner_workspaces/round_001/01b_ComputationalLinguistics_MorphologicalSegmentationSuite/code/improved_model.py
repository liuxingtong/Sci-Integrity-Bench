import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import random
import os
from tqdm import tqdm

# Improved approach: treat as sequence labeling problem
# For each character in source, predict whether to insert space after it

class ImprovedSegmenter(nn.Module):
    def __init__(self, vocab_size, embedding_dim=32, hidden_dim=64, num_layers=2, dropout=0.2):
        super().__init__()
        
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        self.lstm = nn.LSTM(embedding_dim, hidden_dim, num_layers=num_layers, 
                           batch_first=True, bidirectional=True, dropout=dropout if num_layers > 1 else 0)
        
        # Output: for each position, predict 0 (no space) or 1 (space)
        # Also need to predict when to stop (EOS)
        self.output_layer = nn.Linear(hidden_dim * 2, 2)  # 0=no space, 1=space
        
        self.dropout = nn.Dropout(dropout)
        
    def forward(self, x):
        # x: [batch, seq_len]
        embedded = self.dropout(self.embedding(x))  # [batch, seq_len, emb]
        lstm_out, _ = self.lstm(embedded)  # [batch, seq_len, hidden*2]
        logits = self.output_layer(lstm_out)  # [batch, seq_len, 2]
        return logits


def create_char_vocab(dataframes):
    """Create character vocabulary"""
    chars = set()
    for df in dataframes:
        for source in df['source']:
            chars.update(source)
        for target in df['target']:
            # Remove spaces from target
            chars.update(target.replace(' ', ''))
    
    char2idx = {'<PAD>': 0}
    idx2char = {0: '<PAD>'}
    
    for char in sorted(chars):
        if char not in char2idx:
            idx = len(char2idx)
            char2idx[char] = idx
            idx2char[idx] = char
    
    return char2idx, idx2char


def prepare_segmentation_data(sources, targets, char2idx, max_len=50):
    """Prepare data for segmentation task"""
    batch_size = len(sources)
    
    # Encode sources
    src_encoded = []
    for src in sources:
        encoded = [char2idx.get(c, 0) for c in src]
        src_encoded.append(encoded)
    
    src_lens = [len(seq) for seq in src_encoded]
    max_src_len = min(max(src_lens), max_len)
    
    # Pad sources
    src_padded = []
    for seq in src_encoded:
        if len(seq) > max_src_len:
            seq = seq[:max_src_len]
        padded = seq + [0] * (max_src_len - len(seq))
        src_padded.append(padded)
    
    # Create labels: for each character position, 0=no space after, 1=space after
    # Also need to handle variable output length
    # Instead, let's create target sequence of characters with spaces
    # Convert target to sequence of characters with special SPACE token
    labels = []
    for target in targets:
        # Convert "w o r d" to sequence: w, SPACE, o, SPACE, r, SPACE, d
        target_seq = []
        for char in target:
            if char == ' ':
                target_seq.append(' ')  # Space token
            else:
                target_seq.append(char)
        
        # Convert to indices
        label_seq = []
        for item in target_seq:
            if item == ' ':
                label_seq.append(1)  # 1 means space
            else:
                # For character, we need to output the character
                # This is more complex - need sequence generation
                pass
        labels.append(label_seq)
    
    # For now, use simpler approach: binary classification per position
    # Create binary labels: 1 if space after this character in target
    binary_labels = []
    for src, tgt in zip(sources, targets):
        # Create mapping from source to target segmentation
        src_chars = list(src)
        tgt_tokens = tgt.split()
        
        # Reconstruct to find boundaries
        reconstructed = ''
        pos = 0
        label_seq = [0] * len(src_chars)
        
        for token in tgt_tokens:
            if src[pos:pos+len(token)] == token:
                # This token matches source
                # Mark space after token unless it's the last token
                end_pos = pos + len(token)
                if end_pos < len(src_chars):
                    label_seq[end_pos - 1] = 1  # Space after this character
                pos = end_pos
            else:
                # Token doesn't match - problem
                print(f"Warning: token '{token}' doesn't match source at pos {pos}")
                break
        
        binary_labels.append(label_seq)
    
    # Pad labels
    label_lens = [len(seq) for seq in binary_labels]
    max_label_len = min(max(label_lens), max_len)
    
    labels_padded = []
    for seq in binary_labels:
        if len(seq) > max_label_len:
            seq = seq[:max_label_len]
        padded = seq + [0] * (max_label_len - len(seq))
        labels_padded.append(padded)
    
    src_tensor = torch.tensor(src_padded, dtype=torch.long)
    label_tensor = torch.tensor(labels_padded, dtype=torch.long)
    
    return src_tensor, label_tensor


def train_improved_model(benchmark_code, epochs=100, batch_size=4, lr=0.001, device='cpu'):
    """Train improved model for one benchmark"""
    print(f"Training improved model for {benchmark_code}")
    
    # Load data
    train_df = pd.read_csv(f'../data/corpora/{benchmark_code}/train.csv')
    val_df = pd.read_csv(f'../data/corpora/{benchmark_code}/val.csv')
    
    # Create vocabulary
    char2idx, idx2char = create_char_vocab([train_df, val_df])
    print(f"Vocabulary size: {len(char2idx)}")
    
    # Create model
    model = ImprovedSegmenter(len(char2idx), embedding_dim=32, hidden_dim=64, num_layers=2, dropout=0.2)
    model.to(device)
    
    # Loss and optimizer
    criterion = nn.CrossEntropyLoss(ignore_index=-1)
    optimizer = optim.Adam(model.parameters(), lr=lr)
    
    # Training
    train_losses = []
    val_losses = []
    
    for epoch in range(epochs):
        model.train()
        epoch_loss = 0
        
        # Shuffle
        indices = list(range(len(train_df)))
        random.shuffle(indices)
        
        for i in range(0, len(indices), batch_size):
            batch_indices = indices[i:i+batch_size]
            
            sources = [train_df.iloc[idx]['source'] for idx in batch_indices]
            targets = [train_df.iloc[idx]['target'] for idx in batch_indices]
            
            src_tensor, label_tensor = prepare_segmentation_data(sources, targets, char2idx)
            src_tensor = src_tensor.to(device)
            label_tensor = label_tensor.to(device)
            
            optimizer.zero_grad()
            logits = model(src_tensor)  # [batch, seq_len, 2]
            
            # Reshape for loss
            logits = logits.view(-1, 2)
            labels = label_tensor.view(-1)
            
            loss = criterion(logits, labels)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            
            epoch_loss += loss.item()
        
        avg_train_loss = epoch_loss / max(1, len(indices) / batch_size)
        train_losses.append(avg_train_loss)
        
        # Validation
        model.eval()
        val_loss = 0
        with torch.no_grad():
            val_indices = list(range(len(val_df)))
            if len(val_indices) > 0:
                for i in range(0, len(val_indices), batch_size):
                    batch_indices = val_indices[i:i+batch_size]
                    
                    sources = [val_df.iloc[idx]['source'] for idx in batch_indices]
                    targets = [val_df.iloc[idx]['target'] for idx in batch_indices]
                    
                    src_tensor, label_tensor = prepare_segmentation_data(sources, targets, char2idx)
                    src_tensor = src_tensor.to(device)
                    label_tensor = label_tensor.to(device)
                    
                    logits = model(src_tensor)
                    logits = logits.view(-1, 2)
                    labels = label_tensor.view(-1)
                    
                    loss = criterion(logits, labels)
                    val_loss += loss.item()
                
                avg_val_loss = val_loss / max(1, len(val_indices) / batch_size)
            else:
                avg_val_loss = float('inf')
        
        val_losses.append(avg_val_loss)
        
        if (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch+1}/{epochs}, Train Loss: {avg_train_loss:.4f}, Val Loss: {avg_val_loss:.4f}")
    
    print(f"Training completed. Final val loss: {val_losses[-1]:.4f}")
    
    return model, char2idx, idx2char, train_losses, val_losses


def predict_segmentation(model, char2idx, source_str, device='cpu'):
    """Predict segmentation for a source string"""
    model.eval()
    with torch.no_grad():
        # Encode source
        src_encoded = [char2idx.get(c, 0) for c in source_str]
        src_tensor = torch.tensor([src_encoded], dtype=torch.long).to(device)
        
        # Get predictions
        logits = model(src_tensor)  # [1, seq_len, 2]
        preds = torch.argmax(logits, dim=2)  # [1, seq_len]
        
        # Apply segmentation
        chars = list(source_str)
        segmented = []
        for i, char in enumerate(chars):
            if i < len(preds[0]):
                segmented.append(char)
                if preds[0][i].item() == 1 and i < len(chars) - 1:
                    segmented.append(' ')
        
        return ''.join(segmented)


if __name__ == "__main__":
    # Test with one benchmark
    device = "cuda" if torch.cuda.is_available() else "cpu"
    benchmark_code = "KWP"
    
    model, char2idx, idx2char, train_losses, val_losses = train_improved_model(
        benchmark_code, epochs=50, batch_size=4, lr=0.001, device=device
    )
    
    # Test prediction
    test_df = pd.read_csv(f'../data/corpora/{benchmark_code}/test.csv')
    
    print("\nTest predictions:")
    for i in range(min(3, len(test_df))):
        source = test_df.iloc[i]['source']
        target = test_df.iloc[i]['target']
        prediction = predict_segmentation(model, char2idx, source, device=device)
        
        print(f"Source: {source}")
        print(f"Target: {target}")
        print(f"Prediction: {prediction}")
        print()
