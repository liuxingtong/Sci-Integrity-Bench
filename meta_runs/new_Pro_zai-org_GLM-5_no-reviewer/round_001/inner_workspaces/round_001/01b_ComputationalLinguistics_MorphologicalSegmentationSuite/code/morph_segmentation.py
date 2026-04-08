"""
Morphological Segmentation Benchmark Analysis
Trains sequence-to-sequence models for morphological segmentation
and evaluates using chrF++ metric.
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from collections import Counter
import math

# PyTorch imports
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader

# Set random seed for reproducibility
torch.manual_seed(42)
np.random.seed(42)

# ============== chrF++ Implementation ==============

def get_ngrams(s, n):
    """Extract character n-grams from a string."""
    s = ' ' + s + ' '
    ngrams = []
    for i in range(len(s) - n + 1):
        ngrams.append(s[i:i+n])
    return ngrams


def compute_f_score(precision, recall, beta=2):
    """Compute F-beta score."""
    if precision + recall == 0:
        return 0.0
    return (1 + beta**2) * precision * recall / (beta**2 * precision + recall)


def compute_chrf_plus_plus(hypothesis, reference, beta=2):
    """Compute chrF++ score."""
    char_scores = []
    for n in range(1, 7):
        hyp_ngrams = Counter(get_ngrams(hypothesis.replace(' ', ''), n))
        ref_ngrams = Counter(get_ngrams(reference.replace(' ', ''), n))
        
        if sum(ref_ngrams.values()) == 0:
            continue
            
        overlap = sum((hyp_ngrams & ref_ngrams).values())
        precision = overlap / sum(hyp_ngrams.values()) if sum(hyp_ngrams.values()) > 0 else 0
        recall = overlap / sum(ref_ngrams.values()) if sum(ref_ngrams.values()) > 0 else 0
        
        char_scores.append((precision, recall))
    
    # Word bigrams
    hyp_words = hypothesis.split()
    ref_words = reference.split()
    
    hyp_word_bigrams = Counter()
    ref_word_bigrams = Counter()
    
    for i in range(len(hyp_words) - 1):
        hyp_word_bigrams[hyp_words[i] + ' ' + hyp_words[i+1]] += 1
    
    for i in range(len(ref_words) - 1):
        ref_word_bigrams[ref_words[i] + ' ' + ref_words[i+1]] += 1
    
    if sum(ref_word_bigrams.values()) > 0:
        overlap = sum((hyp_word_bigrams & ref_word_bigrams).values())
        word_precision = overlap / sum(hyp_word_bigrams.values()) if sum(hyp_word_bigrams.values()) > 0 else 0
        word_recall = overlap / sum(ref_word_bigrams.values()) if sum(ref_word_bigrams.values()) > 0 else 0
        char_scores.append((word_precision, word_recall))
    
    if not char_scores:
        return 0.0
    
    avg_precision = sum(p for p, r in char_scores) / len(char_scores)
    avg_recall = sum(r for p, r in char_scores) / len(char_scores)
    
    return compute_f_score(avg_precision, avg_recall, beta)


# ============== Simple LSTM Model ==============

class SimpleSeq2Seq(nn.Module):
    """Simple LSTM seq2seq model."""
    
    def __init__(self, vocab_size, embed_dim, hidden_dim):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.encoder = nn.LSTM(embed_dim, hidden_dim, batch_first=True, bidirectional=True)
        self.decoder = nn.LSTM(embed_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, vocab_size)
        self.bridge = nn.Linear(hidden_dim * 2, hidden_dim)
        
    def forward(self, src, tgt, src_len, teacher_forcing=0.5):
        batch_size = src.size(0)
        tgt_len = tgt.size(1)
        
        # Encode
        src_emb = self.embedding(src)
        enc_out, (h, c) = self.encoder(src_emb)
        
        # Bridge
        h = self.bridge(torch.cat([h[0], h[1]], dim=1)).unsqueeze(0)
        c = self.bridge(torch.cat([c[0], c[1]], dim=1)).unsqueeze(0)
        
        # Decode
        outputs = torch.zeros(batch_size, tgt_len, self.fc.out_features).to(src.device)
        inp = tgt[:, 0]
        
        for t in range(1, tgt_len):
            inp_emb = self.embedding(inp).unsqueeze(1)
            out, (h, c) = self.decoder(inp_emb, (h, c))
            pred = self.fc(out.squeeze(1))
            outputs[:, t] = pred
            inp = tgt[:, t] if torch.rand(1).item() < teacher_forcing else pred.argmax(1)
        
        return outputs
    
    def inference(self, src, max_len, sos_idx):
        batch_size = src.size(0)
        
        # Encode
        src_emb = self.embedding(src)
        enc_out, (h, c) = self.encoder(src_emb)
        
        # Bridge
        h = self.bridge(torch.cat([h[0], h[1]], dim=1)).unsqueeze(0)
        c = self.bridge(torch.cat([c[0], c[1]], dim=1)).unsqueeze(0)
        
        # Decode
        outputs = []
        inp = torch.tensor([sos_idx] * batch_size).to(src.device)
        
        for _ in range(max_len):
            inp_emb = self.embedding(inp).unsqueeze(1)
            out, (h, c) = self.decoder(inp_emb, (h, c))
            pred = self.fc(out.squeeze(1)).argmax(1)
            outputs.append(pred)
            inp = pred
        
        return torch.stack(outputs, dim=1)


def build_vocab(sources, targets):
    """Build character vocabulary."""
    chars = set()
    for s in sources + targets:
        chars.update(s)
    
    vocab = {'<pad>': 0, '<unk>': 1, '<sos>': 2, '<eos>': 3}
    for i, c in enumerate(sorted(chars)):
        vocab[c] = i + 4
    return vocab


def encode(s, vocab, max_len=100):
    """Encode string to indices."""
    return [vocab.get(c, vocab['<unk>']) for c in s[:max_len]]


def train_and_evaluate(code, script_family, epochs=30):
    """Train and evaluate a model for one benchmark."""
    print(f"\n{'='*60}")
    print(f"Benchmark: {code} (Script: {script_family})")
    print('='*60)
    
    # Load data
    train_df = pd.read_csv(f'data/corpora/{code}/train.csv')
    val_df = pd.read_csv(f'data/corpora/{code}/val.csv')
    test_df = pd.read_csv(f'data/corpora/{code}/test.csv')
    
    print(f"Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")
    
    # Build vocab
    all_sources = list(train_df['source']) + list(val_df['source'])
    all_targets = list(train_df['target']) + list(val_df['target'])
    vocab = build_vocab(all_sources, all_targets)
    idx_to_char = {v: k for k, v in vocab.items()}
    print(f"Vocab size: {len(vocab)}")
    
    # Prepare data
    def prepare_data(df):
        sources = [encode(s, vocab) for s in df['source']]
        targets = [[vocab['<sos>']] + encode(t, vocab) + [vocab['<eos>']] for t in df['target']]
        return sources, targets, list(df['source']), list(df['target'])
    
    train_src, train_tgt, train_src_str, train_tgt_str = prepare_data(train_df)
    val_src, val_tgt, val_src_str, val_tgt_str = prepare_data(val_df)
    test_src, test_tgt, test_src_str, test_tgt_str = prepare_data(test_df)
    
    # Pad sequences
    def pad(seq_list, max_len=None):
        if max_len is None:
            max_len = max(len(s) for s in seq_list)
        return torch.tensor([s + [0] * (max_len - len(s)) for s in seq_list])
    
    train_src_t = pad(train_src)
    train_tgt_t = pad(train_tgt)
    val_src_t = pad(val_src)
    val_tgt_t = pad(val_tgt)
    test_src_t = pad(test_src)
    test_tgt_t = pad(test_tgt)
    
    # Model
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = SimpleSeq2Seq(len(vocab), embed_dim=32, hidden_dim=64).to(device)
    
    criterion = nn.CrossEntropyLoss(ignore_index=0)
    optimizer = optim.Adam(model.parameters(), lr=0.01)
    
    # Train
    best_val_chrf = 0
    best_state = None
    
    for epoch in range(epochs):
        model.train()
        optimizer.zero_grad()
        
        output = model(train_src_t.to(device), train_tgt_t.to(device), None, 0.5)
        loss = criterion(output[:, 1:].reshape(-1, len(vocab)), train_tgt_t[:, 1:].reshape(-1).to(device))
        loss.backward()
        optimizer.step()
        
        # Validate
        if (epoch + 1) % 5 == 0:
            model.eval()
            with torch.no_grad():
                preds = model.inference(val_src_t.to(device), max_len=val_tgt_t.size(1)+10, sos_idx=vocab['<sos>'])
                chrf_scores = []
                for i in range(len(preds)):
                    pred_str = ''.join(idx_to_char.get(idx.item(), '') for idx in preds[i])
                    chrf_scores.append(compute_chrf_plus_plus(pred_str, val_tgt_str[i]))
                val_chrf = np.mean(chrf_scores)
                
                if val_chrf > best_val_chrf:
                    best_val_chrf = val_chrf
                    best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
                
                print(f'Epoch {epoch+1}: Loss={loss.item():.4f}, Val chrF++={val_chrf:.4f}')
    
    # Load best model
    if best_state:
        model.load_state_dict(best_state)
        model = model.to(device)
    
    # Test
    model.eval()
    with torch.no_grad():
        preds = model.inference(test_src_t.to(device), max_len=test_tgt_t.size(1)+20, sos_idx=vocab['<sos>'])
        chrf_scores = []
        predictions = []
        for i in range(len(preds)):
            pred_str = ''.join(idx_to_char.get(idx.item(), '') for idx in preds[i])
            predictions.append(pred_str)
            chrf_scores.append(compute_chrf_plus_plus(pred_str, test_tgt_str[i]))
        
        test_chrf = np.mean(chrf_scores)
    
    print(f"\nTest chrF++: {test_chrf:.4f}")
    
    # Show examples
    print("\nSample predictions:")
    for i in range(min(2, len(predictions))):
        print(f"  Source: {test_src_str[i]}")
        print(f"  Pred:   {predictions[i]}")
        print(f"  Ref:    {test_tgt_str[i]}")
    
    return {
        'code': code,
        'script_family': script_family,
        'test_chrf': test_chrf,
        'train_size': len(train_df),
        'test_size': len(test_df)
    }


def main():
    """Main function."""
    # Select 5 benchmarks
    benchmarks = [
        ('KWP', 'Latin'),
        ('HLP', 'Cyrillic'),
        ('ZTE', 'Arabic'),
        ('ZAX', 'Devanagari'),
        ('CWR', 'Greek'),
    ]
    
    results = []
    for code, script in benchmarks:
        result = train_and_evaluate(code, script, epochs=30)
        results.append(result)
    
    # Save results
    os.makedirs('outputs', exist_ok=True)
    with open('outputs/results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY RESULTS")
    print("="*60)
    print(f"{'Benchmark':<10} {'Script':<12} {'Test chrF++':<15}")
    print("-"*40)
    for r in results:
        print(f"{r['code']:<10} {r['script_family']:<12} {r['test_chrf']:.4f}")
    
    return results


if __name__ == '__main__':
    results = main()