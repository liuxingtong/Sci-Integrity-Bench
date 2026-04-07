import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
from model import CharVocab, Encoder, Decoder, Seq2Seq
import sys
import os

class MorphDataset(Dataset):
    def __init__(self, source_texts, target_texts, source_vocab, target_vocab, max_len=50):
        self.source_texts = source_texts
        self.target_texts = target_texts
        self.source_vocab = source_vocab
        self.target_vocab = target_vocab
        self.max_len = max_len
        
    def __len__(self):
        return len(self.source_texts)
    
    def __getitem__(self, idx):
        source = self.source_texts[idx]
        target = self.target_texts[idx]
        
        # Encode with special tokens
        source_encoded = self.source_vocab.encode(source, add_special=False)
        target_encoded = self.target_vocab.encode(target, add_special=True)
        
        # Pad sequences
        source_padded = self.pad_sequence(source_encoded, self.source_vocab.pad_idx, self.max_len)
        target_padded = self.pad_sequence(target_encoded, self.target_vocab.pad_idx, self.max_len)
        
        return torch.tensor(source_padded), torch.tensor(target_padded)
    
    def pad_sequence(self, seq, pad_idx, max_len):
        if len(seq) < max_len:
            seq = seq + [pad_idx] * (max_len - len(seq))
        else:
            seq = seq[:max_len]
        return seq

def train_model(code, epochs=100, batch_size=4):
    print(f"Training model for benchmark {code}")
    
    # Load data
    train_path = f'../data/corpora/{code}/train.csv'
    val_path = f'../data/corpora/{code}/val.csv'
    test_path = f'../data/corpora/{code}/test.csv'
    
    train_df = pd.read_csv(train_path)
    val_df = pd.read_csv(val_path)
    test_df = pd.read_csv(test_path)
    
    # Prepare texts
    train_sources = train_df['source'].tolist()
    train_targets = train_df['target'].tolist()
    val_sources = val_df['source'].tolist()
    val_targets = val_df['target'].tolist()
    test_sources = test_df['source'].tolist()
    test_targets = test_df['target'].tolist()
    
    # Create vocabularies
    print("Creating vocabularies...")
    source_vocab = CharVocab(train_sources + val_sources + test_sources)
    target_vocab = CharVocab(train_targets + val_targets + test_targets)
    
    print(f"Source vocab size: {source_vocab.vocab_size}")
    print(f"Target vocab size: {target_vocab.vocab_size}")
    
    # Create datasets
    train_dataset = MorphDataset(train_sources, train_targets, source_vocab, target_vocab)
    val_dataset = MorphDataset(val_sources, val_targets, source_vocab, target_vocab)
    test_dataset = MorphDataset(test_sources, test_targets, source_vocab, target_vocab)
    
    # Create data loaders
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    
    # Initialize model
    embedding_dim = 32
    hidden_dim = 64
    encoder = Encoder(source_vocab.vocab_size, embedding_dim, hidden_dim)
    decoder = Decoder(target_vocab.vocab_size, embedding_dim, hidden_dim)
    model = Seq2Seq(encoder, decoder)
    
    # Loss and optimizer
    criterion = nn.CrossEntropyLoss(ignore_index=target_vocab.pad_idx)
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    # Training loop
    best_val_loss = float('inf')
    patience = 20
    patience_counter = 0
    
    for epoch in range(epochs):
        model.train()
        train_loss = 0
        
        for batch_idx, (src, trg) in enumerate(train_loader):
            optimizer.zero_grad()
            
            output = model(src, trg, teacher_forcing_ratio=0.5)
            
            # Reshape for loss calculation
            output_dim = output.shape[-1]
            output = output[:, 1:].reshape(-1, output_dim)  # Skip SOS token
            trg = trg[:, 1:].reshape(-1)  # Skip SOS token
            
            loss = criterion(output, trg)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1)
            optimizer.step()
            
            train_loss += loss.item()
        
        avg_train_loss = train_loss / len(train_loader)
        
        # Validation
        model.eval()
        val_loss = 0
        with torch.no_grad():
            for src, trg in val_loader:
                output = model(src, trg, teacher_forcing_ratio=0)  # No teacher forcing
                
                output_dim = output.shape[-1]
                output = output[:, 1:].reshape(-1, output_dim)
                trg = trg[:, 1:].reshape(-1)
                
                loss = criterion(output, trg)
                val_loss += loss.item()
        
        avg_val_loss = val_loss / len(val_loader)
        
        print(f"Epoch {epoch+1}/{epochs}, Train Loss: {avg_train_loss:.4f}, Val Loss: {avg_val_loss:.4f}")
        
        # Early stopping
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            patience_counter = 0
            # Save best model
            torch.save(model.state_dict(), f'../outputs/model_{code}_best.pt')
            torch.save({
                'source_vocab': source_vocab,
                'target_vocab': target_vocab,
                'model_state': model.state_dict()
            }, f'../outputs/model_{code}_full.pt')
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"Early stopping at epoch {epoch+1}")
                break
    
    # Load best model
    model.load_state_dict(torch.load(f'../outputs/model_{code}_best.pt'))
    
    # Test evaluation
    model.eval()
    all_predictions = []
    all_targets = []
    
    with torch.no_grad():
        for src, trg in test_loader:
            batch_size = src.shape[0]
            trg_len = trg.shape[1]
            
            # Encode source
            encoder_outputs, (hidden, cell) = model.encoder(src)
            
            # Start with SOS token
            input = torch.full((batch_size,), target_vocab.sos_idx, dtype=torch.long)
            
            # Store predictions
            predictions = torch.zeros(batch_size, trg_len, dtype=torch.long)
            predictions[:, 0] = target_vocab.sos_idx
            
            for t in range(1, trg_len):
                output, hidden, cell, _ = model.decoder(input, hidden, cell, encoder_outputs)
                top1 = output.argmax(1)
                predictions[:, t] = top1
                input = top1
            
            # Decode predictions
            for i in range(batch_size):
                pred_indices = predictions[i].tolist()
                target_indices = trg[i].tolist()
                
                pred_text = target_vocab.decode(pred_indices)
                target_text = target_vocab.decode(target_indices)
                
                all_predictions.append(pred_text)
                all_targets.append(target_text)
    
    return all_predictions, all_targets, source_vocab, target_vocab

if __name__ == "__main__":
    if len(sys.argv) > 1:
        code = sys.argv[1]
    else:
        code = 'KWP'
    
    predictions, targets, _, _ = train_model(code, epochs=50, batch_size=2)
    
    print("\nTest predictions:")
    for i, (pred, target) in enumerate(zip(predictions, targets)):
        print(f"Sample {i}:")
        print(f"  Target: {target}")
        print(f"  Pred:   {pred}")
        print(f"  Match: {pred == target}")
