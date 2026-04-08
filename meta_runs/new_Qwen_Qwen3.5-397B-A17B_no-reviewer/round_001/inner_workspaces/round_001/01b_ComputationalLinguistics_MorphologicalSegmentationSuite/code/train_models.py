#!/usr/bin/env python3
"""
Morphological Segmentation Suite - Simple Training and Evaluation
Uses a very simple character-level model for fast training.
"""

import os
import json
import csv
import random
import numpy as np
import torch
import torch.nn as nn
import sacrebleu

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

SELECTED_BENCHMARKS = ['KWP', 'HLP', 'ZTE', 'ZAX', 'CWR']

HIDDEN_SIZE = 32
EMBEDDING_SIZE = 16
BATCH_SIZE = 2
LEARNING_RATE = 0.01
NUM_EPOCHS = 10
DEVICE = torch.device('cpu')

print(f"Using device: {DEVICE}")


class Vocab:
    def __init__(self, chars):
        self.char2idx = {c: i for i, c in enumerate(chars)}
        self.idx2char = {i: c for c, i in self.char2idx.items()}
        self.pad_idx = 0
        self.unk_idx = 1
        self.eos_idx = 2
    
    def __len__(self):
        return len(self.char2idx)
    
    def encode(self, text):
        return [self.char2idx.get(c, self.unk_idx) for c in text]
    
    def decode(self, indices):
        return ''.join([self.idx2char.get(i, '?') for i in indices])


class SimpleModel(nn.Module):
    def __init__(self, vocab_size, emb_size, hid_size):
        super().__init__()
        self.emb = nn.Embedding(vocab_size, emb_size, padding_idx=0)
        self.gru = nn.GRU(emb_size, hid_size, batch_first=True)
        self.fc = nn.Linear(hid_size, vocab_size)
        self.hid_size = hid_size
    
    def forward(self, x):
        # x: (batch, seq_len)
        emb = self.emb(x)
        out, hid = self.gru(emb)
        logits = self.fc(out)
        return logits, hid
    
    def generate(self, src_ids, max_len=100):
        self.eval()
        with torch.no_grad():
            # Encode source
            src_tensor = torch.tensor([src_ids], dtype=torch.long)
            emb = self.emb(src_tensor)
            _, hid = self.gru(emb)
            
            # Decode
            generated = []
            inp = torch.tensor([[2]], dtype=torch.long)  # EOS as start
            
            for _ in range(max_len):
                emb = self.emb(inp)
                out, hid = self.gru(emb, hid)
                logits = self.fc(out.squeeze(1))
                pred = logits.argmax(dim=-1).item()
                if pred == 2:
                    break
                generated.append(pred)
                inp = torch.tensor([[pred]], dtype=torch.long)
            
            return generated


def load_data(code, workspace_dir):
    base_path = os.path.join(workspace_dir, 'data', 'corpora', code)
    
    def read_csv(path):
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return [(row['source'], row['target']) for row in reader]
    
    train = read_csv(os.path.join(base_path, 'train.csv'))
    val = read_csv(os.path.join(base_path, 'val.csv'))
    test = read_csv(os.path.join(base_path, 'test.csv'))
    
    return [x[0] for x in train], [x[1] for x in train], \
           [x[0] for x in val], [x[1] for x in val], \
           [x[0] for x in test], [x[1] for x in test]


def build_vocab(sources, targets):
    all_chars = set()
    for text in sources + targets:
        all_chars.update(text)
    all_chars = ['<pad>', '<unk>', '<eos>'] + sorted(list(all_chars))
    return Vocab(all_chars)


def compute_chrf(hypotheses, references):
    score = sacrebleu.corpus_chrf(hypotheses, [references], word_order=2)
    return score.score


def train_and_evaluate(code, train_src, train_tgt, val_src, val_tgt, test_src, test_tgt):
    print(f"\n=== {code} ===")
    print(f"Train: {len(train_src)}, Val: {len(val_src)}, Test: {len(test_src)}")
    
    vocab = build_vocab(train_src + val_src, train_tgt + val_tgt)
    print(f"Vocab size: {len(vocab)}")
    
    model = SimpleModel(len(vocab), EMBEDDING_SIZE, HIDDEN_SIZE).to(DEVICE)
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    criterion = nn.CrossEntropyLoss(ignore_index=0)
    
    # Prepare training data
    train_data = [(vocab.encode(s), vocab.encode(t)) for s, t in zip(train_src, train_tgt)]
    
    best_chrf = -1
    best_state = None
    
    for epoch in range(NUM_EPOCHS):
        model.train()
        total_loss = 0
        
        for src_ids, tgt_ids in train_data:
            src_t = torch.tensor([src_ids], dtype=torch.long)
            tgt_t = torch.tensor([tgt_ids], dtype=torch.long)
            
            optimizer.zero_grad()
            logits, _ = model(src_t)
            
            # Match lengths
            min_len = min(logits.size(1), tgt_t.size(1))
            loss = criterion(logits[:, :min_len, :].reshape(-1, logits.size(-1)), 
                           tgt_t[:, :min_len].reshape(-1))
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        
        # Validation
        model.eval()
        val_hyps, val_refs = [], []
        for s, t in zip(val_src, val_tgt):
            gen_ids = model.generate(vocab.encode(s))
            val_hyps.append(vocab.decode(gen_ids))
            val_refs.append(t)
        
        val_chrf = compute_chrf(val_hyps, val_refs)
        if val_chrf > best_chrf:
            best_chrf = val_chrf
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
        
        if (epoch + 1) % 5 == 0:
            print(f"Epoch {epoch+1}: Loss={total_loss/len(train_data):.4f}, Val chrF={val_chrf:.2f}")
    
    if best_state:
        model.load_state_dict(best_state)
    
    # Test evaluation
    model.eval()
    test_hyps, test_refs = [], []
    for s, t in zip(test_src, test_tgt):
        gen_ids = model.generate(vocab.encode(s))
        test_hyps.append(vocab.decode(gen_ids))
        test_refs.append(t)
    
    test_chrf = compute_chrf(test_hyps, test_refs)
    print(f"Test chrF++: {test_chrf:.2f}")
    
    return test_chrf, test_hyps, test_refs


def main():
    workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    with open(os.path.join(workspace_dir, 'data', 'registry.json'), 'r') as f:
        registry = json.load(f)
    
    benchmark_info = {b['code']: b for b in registry['benchmarks']}
    results = {}
    
    for code in SELECTED_BENCHMARKS:
        info = benchmark_info[code]
        print(f"\n{'='*50}")
        print(f"Benchmark: {code} ({info['script_family']})")
        print(f"Dev BLEU: {info['dev_bleu']}, Test size: {info['test_size']}")
        
        train_src, train_tgt, val_src, val_tgt, test_src, test_tgt = load_data(code, workspace_dir)
        
        test_chrf, hypotheses, references = train_and_evaluate(
            code, train_src, train_tgt, val_src, val_tgt, test_src, test_tgt
        )
        
        results[code] = {
            'script_family': info['script_family'],
            'dev_bleu': info['dev_bleu'],
            'test_size': len(test_src),
            'test_chrf': test_chrf
        }
        
        # Save predictions
        outputs_dir = os.path.join(workspace_dir, 'outputs')
        os.makedirs(outputs_dir, exist_ok=True)
        with open(os.path.join(outputs_dir, f'predictions_{code}.csv'), 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['source', 'reference', 'hypothesis'])
            for s, r, h in zip(test_src, references, hypotheses):
                writer.writerow([s, r, h])
    
    # Save results
    with open(os.path.join(outputs_dir, 'results_summary.json'), 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "="*50)
    print("FINAL RESULTS")
    print("="*50)
    for code, res in results.items():
        print(f"{code} ({res['script_family']}): chrF++ = {res['test_chrf']:.2f}")
    
    return results


if __name__ == '__main__':
    main()
