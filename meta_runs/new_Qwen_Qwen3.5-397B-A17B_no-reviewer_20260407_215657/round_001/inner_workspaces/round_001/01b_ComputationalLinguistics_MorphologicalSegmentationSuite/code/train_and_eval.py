#!/usr/bin/env python3
"""
Morphological Segmentation Suite - Training and Evaluation
Trains a character-level seq2seq model on 5 benchmarks and reports chrF++
"""

import os
import json
import random
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from collections import Counter
import sacrebleu

# Set seeds for reproducibility
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

# Select 5 benchmarks with diverse script families
SELECTED_BENCHMARKS = ['KWP', 'HLP', 'ZTE', 'ZAX', 'CWR']

# Model hyperparameters
HIDDEN_DIM = 256
EMBED_DIM = 128
NUM_LAYERS = 2
DROPOUT = 0.3
BATCH_SIZE = 32
EPOCHS = 30
LEARNING_RATE = 0.001
MAX_LEN = 200

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {DEVICE}")


class Vocab:
    def __init__(self, chars):
        self.char2idx = {c: i for i, c in enumerate(chars)}
        self.idx2char = {i: c for i, c in enumerate(chars)}
        self.pad_idx = self.char2idx.get('<pad>', 0)
        self.unk_idx = self.char2idx.get('<unk>', 1)
        
    def encode(self, text):
        return [self.char2idx.get(c, self.unk_idx) for c in text]
    
    def decode(self, indices):
        return ''.join([self.idx2char.get(i, '<unk>') for i in indices])
    
    def __len__(self):
        return len(self.char2idx)


class SegmentationDataset(Dataset):
    def __init__(self, sources, targets, src_vocab, tgt_vocab, max_len=MAX_LEN):
        self.sources = sources
        self.targets = targets
        self.src_vocab = src_vocab
        self.tgt_vocab = tgt_vocab
        self.max_len = max_len
        
    def __len__(self):
        return len(self.sources)
    
    def __getitem__(self, idx):
        src = self.sources[idx]
        tgt = self.targets[idx]
        
        src_ids = self.src_vocab.encode(src)
        tgt_ids = self.tgt_vocab.encode(tgt)
        
        # Add SOS and EOS tokens
        src_ids = [self.src_vocab.char2idx.get('<sos>', 0)] + src_ids + [self.src_vocab.char2idx.get('<eos>', 0)]
        tgt_ids = [self.tgt_vocab.char2idx.get('<sos>', 0)] + tgt_ids + [self.tgt_vocab.char2idx.get('<eos>', 0)]
        
        return torch.tensor(src_ids, dtype=torch.long), torch.tensor(tgt_ids, dtype=torch.long)


def collate_fn(batch, pad_idx=0):
    src_batch, tgt_batch = zip(*batch)
    
    max_src_len = max(len(s) for s in src_batch)
    max_tgt_len = max(len(t) for t in tgt_batch)
    
    src_padded = torch.zeros(len(src_batch), max_src_len, dtype=torch.long)
    tgt_padded = torch.zeros(len(tgt_batch), max_tgt_len, dtype=torch.long)
    
    for i, (src, tgt) in enumerate(batch):
        src_padded[i, :len(src)] = src
        tgt_padded[i, :len(tgt)] = tgt
    
    return src_padded, tgt_padded


class Encoder(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, num_layers, dropout):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.lstm = nn.LSTM(embed_dim, hidden_dim, num_layers, 
                           batch_first=True, bidirectional=True, dropout=dropout if num_layers > 1 else 0)
        self.dropout = nn.Dropout(dropout)
        
    def forward(self, x):
        embedded = self.dropout(self.embedding(x))
        outputs, (hidden, cell) = self.lstm(embedded)
        # Combine bidirectional hidden states
        hidden = torch.cat([hidden[-2::2], hidden[-1::2]], dim=2)
        cell = torch.cat([cell[-2::2], cell[-1::2]], dim=2)
        return outputs, hidden, cell


class Decoder(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, num_layers, dropout):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.lstm = nn.LSTM(embed_dim, hidden_dim * 2, num_layers,
                           batch_first=True, dropout=dropout if num_layers > 1 else 0)
        self.fc = nn.Linear(hidden_dim * 2, vocab_size)
        self.dropout = nn.Dropout(dropout)
        
    def forward(self, x, hidden, cell):
        embedded = self.dropout(self.embedding(x.unsqueeze(1)))
        output, (hidden, cell) = self.lstm(embedded, (hidden, cell))
        prediction = self.fc(output.squeeze(1))
        return prediction, hidden, cell


class Seq2Seq(nn.Module):
    def __init__(self, encoder, decoder, tgt_vocab):
        super().__init__()
        self.encoder = encoder
        self.decoder = decoder
        self.tgt_vocab = tgt_vocab
        
    def forward(self, src, tgt, teacher_forcing_ratio=0.5):
        batch_size = src.shape[0]
        tgt_len = tgt.shape[1]
        tgt_vocab_size = len(self.tgt_vocab)
        
        outputs = torch.zeros(batch_size, tgt_len, tgt_vocab_size).to(DEVICE)
        
        encoder_outputs, hidden, cell = self.encoder(src)
        
        x = tgt[:, 0]  # SOS token
        
        for t in range(1, tgt_len):
            output, hidden, cell = self.decoder(x, hidden, cell)
            outputs[:, t, :] = output
            
            teacher_force = random.random() < teacher_forcing_ratio
            top1 = output.argmax(1)
            x = tgt[:, t] if teacher_force else top1
            
        return outputs
    
    def generate(self, src, max_len=MAX_LEN):
        self.eval()
        batch_size = src.shape[0]
        
        encoder_outputs, hidden, cell = self.encoder(src)
        
        x = torch.tensor([self.tgt_vocab.char2idx.get('<sos>', 0)] * batch_size).to(DEVICE)
        
        generated = []
        eos_idx = self.tgt_vocab.char2idx.get('<eos>', 0)
        
        with torch.no_grad():
            for t in range(max_len):
                output, hidden, cell = self.decoder(x, hidden, cell)
                top1 = output.argmax(1)
                generated.append(top1.cpu().numpy())
                
                if all(top1 == eos_idx):
                    break
                x = top1
        
        generated = np.stack(generated, axis=1)
        return generated


def build_vocab(data, min_freq=1):
    char_counter = Counter()
    for text in data:
        char_counter.update(text)
    
    # Add special tokens
    chars = ['<pad>', '<unk>', '<sos>', '<eos>'] + [c for c, _ in char_counter.most_common() if char_counter[c] >= min_freq]
    return Vocab(chars)


def train_epoch(model, dataloader, optimizer, criterion, clip):
    model.train()
    epoch_loss = 0
    
    for src, tgt in dataloader:
        src = src.to(DEVICE)
        tgt = tgt.to(DEVICE)
        
        optimizer.zero_grad()
        output = model(src, tgt, teacher_forcing_ratio=0.5)
        
        # Reshape for loss calculation
        output = output[:, 1:].reshape(-1, output.shape[-1])
        tgt = tgt[:, 1:].reshape(-1)
        
        loss = criterion(output, tgt)
        loss.backward()
        
        torch.nn.utils.clip_grad_norm_(model.parameters(), clip)
        optimizer.step()
        
        epoch_loss += loss.item()
    
    return epoch_loss / len(dataloader)


def evaluate(model, dataloader, criterion):
    model.eval()
    epoch_loss = 0
    
    with torch.no_grad():
        for src, tgt in dataloader:
            src = src.to(DEVICE)
            tgt = tgt.to(DEVICE)
            
            output = model(src, tgt, teacher_forcing_ratio=0.0)
            
            output = output[:, 1:].reshape(-1, output.shape[-1])
            tgt = tgt[:, 1:].reshape(-1)
            
            loss = criterion(output, tgt)
            epoch_loss += loss.item()
    
    return epoch_loss / len(dataloader)


def generate_predictions(model, sources, src_vocab, tgt_vocab, batch_size=32):
    model.eval()
    predictions = []
    
    dataset = SegmentationDataset(sources, sources, src_vocab, tgt_vocab)
    dataloader = DataLoader(dataset, batch_size=batch_size, collate_fn=collate_fn)
    
    all_preds = []
    with torch.no_grad():
        for src, _ in dataloader:
            src = src.to(DEVICE)
            generated = model.generate(src)
            
            for gen in generated:
                pred_str = tgt_vocab.decode(gen)
                # Remove special tokens
                pred_str = pred_str.replace('<sos>', '').replace('<eos>', '').replace('<pad>', '')
                all_preds.append(pred_str)
    
    return all_preds


def compute_chrfpp(references, hypotheses):
    """Compute chrF++ score using sacrebleu"""
    # sacrebleu expects list of strings
    refs = [[ref] for ref in references]
    hypos = hypotheses
    
    # Use chrF++ (beta=3, which weights precision more)
    chrf = sacrebleu.corpus_chrf(hypos, refs, beta=3, word_order=2)
    return chrf.score


def load_data(code):
    """Load train, val, test data for a benchmark"""
    base_path = f"../data/corpora/{code}"
    train_df = pd.read_csv(f"{base_path}/train.csv")
    val_df = pd.read_csv(f"{base_path}/val.csv")
    test_df = pd.read_csv(f"{base_path}/test.csv")
    
    return train_df['source'].tolist(), train_df['target'].tolist(), \
           val_df['source'].tolist(), val_df['target'].tolist(), \
           test_df['source'].tolist(), test_df['target'].tolist()


def train_benchmark(code, results_dir):
    """Train model on a single benchmark"""
    print(f"\n{'='*50}")
    print(f"Training on benchmark: {code}")
    print(f"{'='*50}")
    
    # Load data
    train_sources, train_targets, val_sources, val_targets, test_sources, test_targets = load_data(code)
    
    print(f"Train: {len(train_sources)}, Val: {len(val_sources)}, Test: {len(test_sources)}")
    
    # Build vocabularies
    all_chars = train_sources + train_targets + val_sources + val_targets
    src_vocab = build_vocab(all_chars)
    tgt_vocab = build_vocab(all_chars)
    
    print(f"Vocab size: {len(src_vocab)}")
    
    # Create datasets
    train_dataset = SegmentationDataset(train_sources, train_targets, src_vocab, tgt_vocab)
    val_dataset = SegmentationDataset(val_sources, val_targets, src_vocab, tgt_vocab)
    test_dataset = SegmentationDataset(test_sources, test_targets, src_vocab, tgt_vocab)
    
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, collate_fn=collate_fn)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, collate_fn=collate_fn)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, collate_fn=collate_fn)
    
    # Initialize model
    encoder = Encoder(len(src_vocab), EMBED_DIM, HIDDEN_DIM, NUM_LAYERS, DROPOUT)
    decoder = Decoder(len(tgt_vocab), EMBED_DIM, HIDDEN_DIM, NUM_LAYERS, DROPOUT)
    model = Seq2Seq(encoder, decoder, tgt_vocab).to(DEVICE)
    
    # Count parameters
    num_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Model parameters: {num_params:,}")
    
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    criterion = nn.CrossEntropyLoss(ignore_index=0)
    
    # Training loop
    best_val_loss = float('inf')
    best_model_state = None
    
    train_losses = []
    val_losses = []
    
    for epoch in range(EPOCHS):
        train_loss = train_epoch(model, train_loader, optimizer, criterion, clip=1.0)
        val_loss = evaluate(model, val_loader, criterion)
        
        train_losses.append(train_loss)
        val_losses.append(val_loss)
        
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_model_state = model.state_dict().copy()
        
        if (epoch + 1) % 5 == 0:
            print(f"Epoch {epoch+1}/{EPOCHS} - Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")
    
    # Load best model
    model.load_state_dict(best_model_state)
    
    # Generate predictions on test set
    predictions = generate_predictions(model, test_sources, src_vocab, tgt_vocab)
    
    # Compute chrF++
    chrfpp_score = compute_chrfpp(test_targets, predictions)
    
    print(f"\nTest chrF++: {chrfpp_score:.2f}")
    
    # Save results
    result = {
        'code': code,
        'chrfpp': chrfpp_score,
        'train_size': len(train_sources),
        'test_size': len(test_sources),
        'best_val_loss': best_val_loss,
        'num_params': num_params,
        'predictions': predictions[:10],  # Save first 10 for inspection
        'train_losses': train_losses,
        'val_losses': val_losses
    }
    
    os.makedirs(results_dir, exist_ok=True)
    with open(f"{results_dir}/{code}_results.json", 'w') as f:
        json.dump(result, f, indent=2)
    
    # Save all predictions
    with open(f"{results_dir}/{code}_predictions.txt", 'w') as f:
        for pred in predictions:
            f.write(pred + '\n')
    
    return result


def main():
    results_dir = "outputs"
    os.makedirs(results_dir, exist_ok=True)
    
    all_results = []
    
    for code in SELECTED_BENCHMARKS:
        result = train_benchmark(code, results_dir)
        all_results.append(result)
    
    # Summary
    print(f"\n{'='*50}")
    print("SUMMARY")
    print(f"{'='*50}")
    
    summary_table = []
    for r in all_results:
        summary_table.append(f"{r['code']}: chrF++ = {r['chrfpp']:.2f}")
        print(f"{r['code']}: chrF++ = {r['chrfpp']:.2f}")
    
    # Save summary
    with open(f"{results_dir}/summary.json", 'w') as f:
        json.dump(all_results, f, indent=2)
    
    with open(f"{results_dir}/summary.txt", 'w') as f:
        f.write('\n'.join(summary_table))
    
    print(f"\nResults saved to {results_dir}/")
    
    return all_results


if __name__ == "__main__":
    main()
