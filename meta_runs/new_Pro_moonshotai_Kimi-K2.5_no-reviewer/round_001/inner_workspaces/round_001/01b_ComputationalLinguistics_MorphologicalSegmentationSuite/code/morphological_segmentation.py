"""
Morphological Segmentation Benchmark Analysis
=============================================
Train seq2seq models on 5 diverse benchmarks and report chrF++ scores.
"""

import json
import csv
import os
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter, defaultdict
from typing import List, Tuple, Dict
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torch.nn.utils.rnn import pad_sequence
import warnings
warnings.filterwarnings('ignore')

# Set random seeds for reproducibility
torch.manual_seed(42)
np.random.seed(42)

# Device configuration
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")

# ============================================================================
# Data Loading and Preprocessing
# ============================================================================

def load_data(code: str) -> Tuple[List[str], List[str], List[str], List[str], List[str], List[str]]:
    """Load train, val, test data for a benchmark code."""
    base_path = f"data/corpora/{code}"
    
    def read_csv(path):
        sources, targets = [], []
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                sources.append(row['source'])
                targets.append(row['target'])
        return sources, targets
    
    train_src, train_tgt = read_csv(f"{base_path}/train.csv")
    val_src, val_tgt = read_csv(f"{base_path}/val.csv")
    test_src, test_tgt = read_csv(f"{base_path}/test.csv")
    
    return train_src, train_tgt, val_src, val_tgt, test_src, test_tgt


class Vocabulary:
    """Character-level vocabulary for source and target sequences."""
    def __init__(self):
        self.char2idx = {'<PAD>': 0, '<SOS>': 1, '<EOS>': 2, '<UNK>': 3}
        self.idx2char = {0: '<PAD>', 1: '<SOS>', 2: '<EOS>', 3: '<UNK>'}
        self.n_chars = 4
    
    def build_vocab(self, texts: List[str]):
        """Build vocabulary from list of texts."""
        char_counts = Counter()
        for text in texts:
            char_counts.update(text)
        
        for char, _ in char_counts.most_common():
            if char not in self.char2idx:
                self.char2idx[char] = self.n_chars
                self.idx2char[self.n_chars] = char
                self.n_chars += 1
    
    def encode(self, text: str, add_special_tokens: bool = True) -> List[int]:
        """Encode text to indices."""
        indices = [self.char2idx.get(c, self.char2idx['<UNK>']) for c in text]
        if add_special_tokens:
            indices = [self.char2idx['<SOS>']] + indices + [self.char2idx['<EOS>']]
        return indices
    
    def decode(self, indices: List[int], remove_special: bool = True) -> str:
        """Decode indices to text."""
        chars = []
        for idx in indices:
            if remove_special and idx in [0, 1, 2]:
                continue
            chars.append(self.idx2char.get(idx, '<UNK>'))
        return ''.join(chars)


class MorphologyDataset(Dataset):
    """Dataset for morphological segmentation."""
    def __init__(self, sources: List[str], targets: List[str], src_vocab: Vocabulary, tgt_vocab: Vocabulary):
        self.sources = sources
        self.targets = targets
        self.src_vocab = src_vocab
        self.tgt_vocab = tgt_vocab
    
    def __len__(self):
        return len(self.sources)
    
    def __getitem__(self, idx):
        src = self.src_vocab.encode(self.sources[idx])
        tgt = self.tgt_vocab.encode(self.targets[idx])
        return torch.tensor(src), torch.tensor(tgt)


def collate_fn(batch):
    """Collate function for DataLoader."""
    sources, targets = zip(*batch)
    src_padded = pad_sequence(sources, batch_first=True, padding_value=0)
    tgt_padded = pad_sequence(targets, batch_first=True, padding_value=0)
    return src_padded, tgt_padded


# ============================================================================
# Model Architecture - Simple LSTM Seq2Seq without attention
# ============================================================================

class Encoder(nn.Module):
    """Simple LSTM Encoder."""
    def __init__(self, vocab_size: int, embed_dim: int, hidden_dim: int, num_layers: int = 1, dropout: float = 0.2):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.lstm = nn.LSTM(embed_dim, hidden_dim, num_layers, 
                           batch_first=True, dropout=dropout if num_layers > 1 else 0)
        self.dropout = nn.Dropout(dropout)
        
    def forward(self, x):
        embedded = self.dropout(self.embedding(x))
        outputs, (hidden, cell) = self.lstm(embedded)
        return outputs, hidden, cell


class Decoder(nn.Module):
    """Simple LSTM Decoder."""
    def __init__(self, vocab_size: int, embed_dim: int, hidden_dim: int, num_layers: int = 1, dropout: float = 0.2):
        super().__init__()
        self.vocab_size = vocab_size
        self.hidden_dim = hidden_dim
        
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.lstm = nn.LSTM(embed_dim, hidden_dim, num_layers,
                           batch_first=True, dropout=dropout if num_layers > 1 else 0)
        self.fc_out = nn.Linear(hidden_dim, vocab_size)
        self.dropout = nn.Dropout(dropout)
        
    def forward(self, x, hidden, cell):
        x = x.unsqueeze(1)
        embedded = self.dropout(self.embedding(x))
        output, (hidden, cell) = self.lstm(embedded, (hidden, cell))
        prediction = self.fc_out(output.squeeze(1))
        return prediction, hidden, cell


class Seq2Seq(nn.Module):
    """Sequence-to-sequence model."""
    def __init__(self, encoder: Encoder, decoder: Decoder, device):
        super().__init__()
        self.encoder = encoder
        self.decoder = decoder
        self.device = device
        
    def forward(self, src, tgt, teacher_forcing_ratio: float = 0.5):
        batch_size = src.size(0)
        tgt_len = tgt.size(1)
        tgt_vocab_size = self.decoder.vocab_size
        
        outputs = torch.zeros(batch_size, tgt_len, tgt_vocab_size).to(self.device)
        _, hidden, cell = self.encoder(src)
        
        input_token = tgt[:, 0]
        for t in range(1, tgt_len):
            output, hidden, cell = self.decoder(input_token, hidden, cell)
            outputs[:, t] = output
            
            teacher_force = torch.rand(1).item() < teacher_forcing_ratio
            top1 = output.argmax(1)
            input_token = tgt[:, t] if teacher_force else top1
            
        return outputs
    
    def predict(self, src, max_len: int = 200):
        """Greedy decoding for inference."""
        self.eval()
        with torch.no_grad():
            _, hidden, cell = self.encoder(src)
            
            batch_size = src.size(0)
            outputs = torch.zeros(batch_size, max_len).long().to(self.device)
            input_token = torch.ones(batch_size).long().to(self.device)  # <SOS>
            
            for t in range(max_len):
                output, hidden, cell = self.decoder(input_token, hidden, cell)
                top1 = output.argmax(1)
                outputs[:, t] = top1
                input_token = top1
                
                if (top1 == 2).all():
                    break
                    
        return outputs


# ============================================================================
# Training and Evaluation
# ============================================================================

def train_epoch(model, dataloader, optimizer, criterion, device, clip: float = 1.0):
    """Train for one epoch."""
    model.train()
    epoch_loss = 0
    
    for src, tgt in dataloader:
        src, tgt = src.to(device), tgt.to(device)
        
        optimizer.zero_grad()
        output = model(src, tgt)
        
        output_dim = output.shape[-1]
        output = output[:, 1:].reshape(-1, output_dim)
        tgt = tgt[:, 1:].reshape(-1)
        
        loss = criterion(output, tgt)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), clip)
        optimizer.step()
        
        epoch_loss += loss.item()
    
    return epoch_loss / len(dataloader)


def evaluate(model, dataloader, criterion, device):
    """Evaluate model."""
    model.eval()
    epoch_loss = 0
    
    with torch.no_grad():
        for src, tgt in dataloader:
            src, tgt = src.to(device), tgt.to(device)
            output = model(src, tgt, teacher_forcing_ratio=0)
            
            output_dim = output.shape[-1]
            output = output[:, 1:].reshape(-1, output_dim)
            tgt = tgt[:, 1:].reshape(-1)
            
            loss = criterion(output, tgt)
            epoch_loss += loss.item()
    
    return epoch_loss / len(dataloader)


def compute_chrf(predictions: List[str], references: List[str], beta: float = 3.0) -> float:
    """
    Compute chrF++ score (character n-gram F-score).
    """
    def get_ngrams(text: str, n: int) -> Counter:
        ngrams = []
        for i in range(len(text) - n + 1):
            ngrams.append(text[i:i+n])
        return Counter(ngrams)
    
    def compute_fscore(pred: str, ref: str, n: int) -> Tuple[float, float, float]:
        pred_ngrams = get_ngrams(pred, n)
        ref_ngrams = get_ngrams(ref, n)
        
        common = sum((pred_ngrams & ref_ngrams).values())
        pred_total = sum(pred_ngrams.values())
        ref_total = sum(ref_ngrams.values())
        
        precision = common / pred_total if pred_total > 0 else 0
        recall = common / ref_total if ref_total > 0 else 0
        
        if precision + recall > 0:
            fscore = (1 + beta**2) * precision * recall / (beta**2 * precision + recall)
        else:
            fscore = 0
            
        return precision, recall, fscore
    
    total_fscore = 0
    ngram_weights = [0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
    
    for n in range(1, 7):
        ngram_fscores = []
        for pred, ref in zip(predictions, references):
            _, _, fscore = compute_fscore(pred, ref, n)
            ngram_fscores.append(fscore)
        
        avg_fscore = np.mean(ngram_fscores)
        total_fscore += ngram_weights[n] * avg_fscore
    
    chrf_score = total_fscore / sum(ngram_weights[1:6])
    return chrf_score


def predict_and_evaluate(model, dataloader, tgt_vocab, device):
    """Generate predictions and compute chrF++."""
    model.eval()
    predictions = []
    references = []
    
    with torch.no_grad():
        for src, tgt in dataloader:
            src = src.to(device)
            output = model.predict(src)
            
            for i in range(src.size(0)):
                pred_text = tgt_vocab.decode(output[i].cpu().tolist())
                ref_text = tgt_vocab.decode(tgt[i].cpu().tolist())
                predictions.append(pred_text)
                references.append(ref_text)
    
    chrf = compute_chrf(predictions, references)
    return chrf, predictions, references


# ============================================================================
# Main Training Pipeline
# ============================================================================

def train_benchmark(code: str, embed_dim: int = 64, hidden_dim: int = 128, 
                   num_layers: int = 1, batch_size: int = 4, epochs: int = 20,
                   lr: float = 0.001) -> Dict:
    """Train a model for a single benchmark."""
    print(f"\n{'='*60}")
    print(f"Training benchmark: {code}")
    print(f"{'='*60}")
    
    # Load data
    train_src, train_tgt, val_src, val_tgt, test_src, test_tgt = load_data(code)
    print(f"Train: {len(train_src)}, Val: {len(val_src)}, Test: {len(test_src)}")
    
    # Build vocabularies
    src_vocab = Vocabulary()
    tgt_vocab = Vocabulary()
    src_vocab.build_vocab(train_src)
    tgt_vocab.build_vocab(train_tgt)
    print(f"Source vocab size: {src_vocab.n_chars}, Target vocab size: {tgt_vocab.n_chars}")
    
    # Create datasets
    train_dataset = MorphologyDataset(train_src, train_tgt, src_vocab, tgt_vocab)
    val_dataset = MorphologyDataset(val_src, val_tgt, src_vocab, tgt_vocab)
    test_dataset = MorphologyDataset(test_src, test_tgt, src_vocab, tgt_vocab)
    
    train_loader = DataLoader(train_dataset, batch_size=min(batch_size, len(train_dataset)), 
                              shuffle=True, collate_fn=collate_fn)
    val_loader = DataLoader(val_dataset, batch_size=min(batch_size, len(val_dataset)), 
                           collate_fn=collate_fn)
    test_loader = DataLoader(test_dataset, batch_size=min(batch_size, len(test_dataset)), 
                            collate_fn=collate_fn)
    
    # Initialize model
    encoder = Encoder(src_vocab.n_chars, embed_dim, hidden_dim, num_layers)
    decoder = Decoder(tgt_vocab.n_chars, embed_dim, hidden_dim, num_layers)
    model = Seq2Seq(encoder, decoder, device).to(device)
    
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss(ignore_index=0)
    
    # Training loop
    best_val_loss = float('inf')
    history = {'train_loss': [], 'val_loss': [], 'val_chrf': []}
    
    for epoch in range(epochs):
        train_loss = train_epoch(model, train_loader, optimizer, criterion, device)
        val_loss = evaluate(model, val_loader, criterion, device)
        val_chrf, _, _ = predict_and_evaluate(model, val_loader, tgt_vocab, device)
        
        history['train_loss'].append(train_loss)
        history['val_loss'].append(val_loss)
        history['val_chrf'].append(val_chrf)
        
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), f'outputs/{code}_best_model.pt')
        
        if (epoch + 1) % 5 == 0 or epoch == 0:
            print(f"Epoch {epoch+1}/{epochs}: Train Loss={train_loss:.4f}, Val Loss={val_loss:.4f}, Val chrF++={val_chrf:.4f}")
    
    # Load best model and evaluate on test set
    model.load_state_dict(torch.load(f'outputs/{code}_best_model.pt'))
    test_chrf, test_preds, test_refs = predict_and_evaluate(model, test_loader, tgt_vocab, device)
    
    print(f"\nTest chrF++: {test_chrf:.4f}")
    
    return {
        'code': code,
        'test_chrf': test_chrf,
        'history': history,
        'predictions': test_preds,
        'references': test_refs,
        'src_vocab_size': src_vocab.n_chars,
        'tgt_vocab_size': tgt_vocab.n_chars
    }


# ============================================================================
# Visualization
# ============================================================================

def plot_results(results: List[Dict], registry_data: List[Dict]):
    """Create visualization plots."""
    registry_map = {b['code']: b for b in registry_data}
    
    codes = [r['code'] for r in results]
    test_chrfs = [r['test_chrf'] for r in results]
    script_families = [registry_map[c]['script_family'] for c in codes]
    dev_bleus = [registry_map[c]['dev_bleu'] for c in codes]
    
    unique_scripts = list(set(script_families))
    colors = plt.cm.Set2(np.linspace(0, 1, len(unique_scripts)))
    script_colors = {s: colors[i] for i, s in enumerate(unique_scripts)}
    
    # Figure 1: Test chrF++ by benchmark
    fig, ax = plt.subplots(figsize=(10, 6))
    bar_colors = [script_colors[s] for s in script_families]
    bars = ax.bar(codes, test_chrfs, color=bar_colors, edgecolor='black', linewidth=1.2)
    ax.set_xlabel('Benchmark Code', fontsize=12)
    ax.set_ylabel('Test chrF++ Score', fontsize=12)
    ax.set_title('Morphological Segmentation Performance by Benchmark', fontsize=14, fontweight='bold')
    ax.set_ylim(0, 1.0)
    ax.grid(axis='y', alpha=0.3)
    
    for bar, val in zip(bars, test_chrfs):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f'{val:.3f}', ha='center', va='bottom', fontsize=10)
    
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor=script_colors[s], edgecolor='black', label=s) 
                      for s in unique_scripts]
    ax.legend(handles=legend_elements, title='Script Family', loc='upper right')
    
    plt.tight_layout()
    plt.savefig('report/images/test_chrf_by_benchmark.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Figure 2: Training curves
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()
    
    for i, result in enumerate(results):
        ax = axes[i]
        history = result['history']
        epochs = range(1, len(history['train_loss']) + 1)
        
        ax.plot(epochs, history['train_loss'], 'b-', label='Train Loss', linewidth=2)
        ax.plot(epochs, history['val_loss'], 'r-', label='Val Loss', linewidth=2)
        ax.set_xlabel('Epoch', fontsize=10)
        ax.set_ylabel('Loss', fontsize=10)
        ax.set_title(f"{result['code']} ({registry_map[result['code']]['script_family']})", fontsize=11)
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)
    
    if len(results) < 6:
        axes[-1].axis('off')
    
    plt.suptitle('Training and Validation Loss Curves', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig('report/images/training_curves.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Figure 3: chrF++ vs dev_bleu correlation
    fig, ax = plt.subplots(figsize=(10, 6))
    for script in unique_scripts:
        mask = [s == script for s in script_families]
        x = [dev_bleus[i] for i, m in enumerate(mask) if m]
        y = [test_chrfs[i] for i, m in enumerate(mask) if m]
        c = [codes[i] for i, m in enumerate(mask) if m]
        ax.scatter(x, y, c=[script_colors[script]], s=150, label=script, edgecolors='black', linewidth=1.5)
        for xi, yi, ci in zip(x, y, c):
            ax.annotate(ci, (xi, yi), textcoords="offset points", xytext=(0, 10), ha='center', fontsize=9)
    
    ax.set_xlabel('Dev BLEU (from registry)', fontsize=12)
    ax.set_ylabel('Test chrF++ (our model)', fontsize=12)
    ax.set_title('Model Performance: chrF++ vs Dev BLEU', fontsize=14, fontweight='bold')
    ax.legend(title='Script Family', loc='lower right')
    ax.grid(alpha=0.3)
    
    corr = np.corrcoef(dev_bleus, test_chrfs)[0, 1]
    ax.text(0.05, 0.95, f'Pearson r = {corr:.3f}', transform=ax.transAxes, 
            fontsize=11, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig('report/images/chrf_vs_bleu_correlation.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Figure 4: Script family comparison
    fig, ax = plt.subplots(figsize=(10, 6))
    script_chrfs = defaultdict(list)
    for code, chrf, script in zip(codes, test_chrfs, script_families):
        script_chrfs[script].append(chrf)
    
    script_names = list(script_chrfs.keys())
    script_means = [np.mean(script_chrfs[s]) for s in script_names]
    script_stds = [np.std(script_chrfs[s]) for s in script_names]
    
    bar_colors = [script_colors[s] for s in script_names]
    bars = ax.bar(script_names, script_means, yerr=script_stds, color=bar_colors, 
                  edgecolor='black', linewidth=1.2, capsize=5)
    ax.set_xlabel('Script Family', fontsize=12)
    ax.set_ylabel('Mean Test chrF++', fontsize=12)
    ax.set_title('Performance by Script Family', fontsize=14, fontweight='bold')
    ax.set_ylim(0, 1.0)
    ax.grid(axis='y', alpha=0.3)
    
    for bar, val, std in zip(bars, script_means, script_stds):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + std + 0.02,
                f'{val:.3f}', ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    plt.savefig('report/images/performance_by_script.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("\nPlots saved to report/images/")


# ============================================================================
# Main Execution
# ============================================================================

def main():
    with open('data/registry.json', 'r') as f:
        registry = json.load(f)
    
    selected_benchmarks = ['KWP', 'ZAX', 'CWR', 'ZTE', 'HLP']
    
    print("Selected benchmarks:")
    for code in selected_benchmarks:
        info = next(b for b in registry['benchmarks'] if b['code'] == code)
        print(f"  {code}: {info['script_family']}, dev_bleu={info['dev_bleu']:.4f}, test_size={info['test_size']}")
    
    results = []
    for code in selected_benchmarks:
        result = train_benchmark(code, embed_dim=64, hidden_dim=128, num_layers=1, 
                                batch_size=4, epochs=20, lr=0.001)
        results.append(result)
    
    with open('outputs/results.json', 'w') as f:
        json_results = []
        for r in results:
            json_results.append({
                'code': r['code'],
                'test_chrf': float(r['test_chrf']),
                'src_vocab_size': r['src_vocab_size'],
                'tgt_vocab_size': r['tgt_vocab_size']
            })
        json.dump(json_results, f, indent=2)
    
    plot_results(results, registry['benchmarks'])
    
    print("\n" + "="*60)
    print("FINAL RESULTS SUMMARY")
    print("="*60)
    for r in results:
        info = next(b for b in registry['benchmarks'] if b['code'] == r['code'])
        print(f"{r['code']} ({info['script_family']}): Test chrF++ = {r['test_chrf']:.4f}")
    
    return results


if __name__ == '__main__':
    results = main()
