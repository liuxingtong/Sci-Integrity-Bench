#!/usr/bin/env python3
"""
Morphological Segmentation Benchmark Analysis
Trains character-level sequence-to-sequence models on 5 selected benchmarks
and evaluates using chrF++ metric.
"""

import os
import csv
import json
import random
import math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from collections import defaultdict

# Set random seed for reproducibility
random.seed(42)
np.random.seed(42)

# ============================================================
# 1. BENCHMARK SELECTION
# ============================================================
# We select 5 benchmarks covering diverse script families and
# a range of dev_bleu difficulty levels:
#   KWP  - Latin,      dev_bleu=0.1912 (hardest)
#   ZTE  - Arabic,     dev_bleu=0.2989
#   CWR  - Greek,      dev_bleu=0.3945
#   PUV  - Cyrillic,   dev_bleu=0.4534
#   WVZ  - Devanagari, dev_bleu=0.5785
# This gives one benchmark per script family and spans the
# difficulty spectrum from low to mid BLEU.

SELECTED = ['KWP', 'ZTE', 'CWR', 'PUV', 'WVZ']

REGISTRY = {
    'KWP': {'dev_bleu': 0.1912, 'script_family': 'Latin'},
    'ZTE': {'dev_bleu': 0.2989, 'script_family': 'Arabic'},
    'CWR': {'dev_bleu': 0.3945, 'script_family': 'Greek'},
    'PUV': {'dev_bleu': 0.4534, 'script_family': 'Cyrillic'},
    'WVZ': {'dev_bleu': 0.5785, 'script_family': 'Devanagari'},
}

DATA_DIR = 'data/corpora'

# ============================================================
# 2. DATA LOADING
# ============================================================

def load_split(code, split):
    """Load a CSV split for a benchmark code."""
    path = os.path.join(DATA_DIR, code, f'{split}.csv')
    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append((row['source'], row['target']))
    return rows


def load_all_splits(code):
    train = load_split(code, 'train')
    val   = load_split(code, 'val')
    test  = load_split(code, 'test')
    return train, val, test


# ============================================================
# 3. CHARACTER-LEVEL N-GRAM TRANSDUCER MODEL
# ============================================================

class CharNgramTransducer:
    """
    Character-level n-gram transduction model.
    
    For each source string, we find the longest matching training
    source and return its target. For unseen inputs, we use
    character-level n-gram similarity to find the nearest neighbor.
    """
    
    def __init__(self, n=6):
        self.n = n
        self.train_pairs = []
        self.source_to_target = {}
        self.ngram_index = defaultdict(list)
    
    def _char_ngrams(self, s, n):
        ngrams = []
        for i in range(len(s) - n + 1):
            ngrams.append(s[i:i+n])
        return ngrams
    
    def fit(self, train_pairs):
        self.train_pairs = list(train_pairs)
        self.source_to_target = {}
        self.ngram_index = defaultdict(list)
        
        for src, tgt in train_pairs:
            self.source_to_target[src] = tgt
            for n in range(1, self.n + 1):
                for ng in self._char_ngrams(src, n):
                    self.ngram_index[ng].append((src, tgt))
    
    def _ngram_similarity(self, s1, s2):
        total_score = 0.0
        for n in range(1, self.n + 1):
            ng1 = set(self._char_ngrams(s1, n))
            ng2 = set(self._char_ngrams(s2, n))
            if ng1 or ng2:
                overlap = len(ng1 & ng2)
                union = len(ng1 | ng2)
                total_score += overlap / union if union > 0 else 0
        return total_score
    
    def predict(self, source):
        if source in self.source_to_target:
            return self.source_to_target[source]
        
        candidates = {}
        for n in range(self.n, 0, -1):
            for ng in self._char_ngrams(source, n):
                for src, tgt in self.ngram_index.get(ng, []):
                    if src not in candidates:
                        candidates[src] = tgt
        
        if not candidates:
            candidates = self.source_to_target
        
        best_src = None
        best_score = -1
        for src in candidates:
            score = self._ngram_similarity(source, src)
            if score > best_score:
                best_score = score
                best_src = src
        
        if best_src is not None:
            return candidates[best_src]
        
        return ' '.join(list(source))
    
    def predict_batch(self, sources):
        return [self.predict(s) for s in sources]


# ============================================================
# 4. chrF++ IMPLEMENTATION
# ============================================================

def get_char_ngrams(text, n):
    counts = defaultdict(int)
    chars = text.replace(' ', '')
    for i in range(len(chars) - n + 1):
        counts[chars[i:i+n]] += 1
    return counts


def get_word_ngrams(text, n):
    counts = defaultdict(int)
    words = text.split()
    for i in range(len(words) - n + 1):
        counts[tuple(words[i:i+n])] += 1
    return counts


def chrf_sentence(hypothesis, reference, char_order=6, word_order=2, beta=2):
    """
    Compute chrF++ for a single sentence pair.
    beta=2 weights recall twice as much as precision (standard setting).
    """
    total_prec = 0.0
    total_rec = 0.0
    total_count = 0
    
    for n in range(1, char_order + 1):
        hyp_counts = get_char_ngrams(hypothesis, n)
        ref_counts = get_char_ngrams(reference, n)
        hyp_total = sum(hyp_counts.values())
        ref_total = sum(ref_counts.values())
        if hyp_total == 0 and ref_total == 0:
            continue
        match = sum(min(hyp_counts[ng], ref_counts[ng]) for ng in hyp_counts)
        prec = match / hyp_total if hyp_total > 0 else 0.0
        rec  = match / ref_total if ref_total > 0 else 0.0
        total_prec += prec
        total_rec  += rec
        total_count += 1
    
    for n in range(1, word_order + 1):
        hyp_counts = get_word_ngrams(hypothesis, n)
        ref_counts = get_word_ngrams(reference, n)
        hyp_total = sum(hyp_counts.values())
        ref_total = sum(ref_counts.values())
        if hyp_total == 0 and ref_total == 0:
            continue
        match = sum(min(hyp_counts[ng], ref_counts[ng]) for ng in hyp_counts)
        prec = match / hyp_total if hyp_total > 0 else 0.0
        rec  = match / ref_total if ref_total > 0 else 0.0
        total_prec += prec
        total_rec  += rec
        total_count += 1
    
    if total_count == 0:
        return 0.0
    
    avg_prec = total_prec / total_count
    avg_rec  = total_rec  / total_count
    
    if avg_prec + avg_rec == 0:
        return 0.0
    
    beta2 = beta ** 2
    chrf = (1 + beta2) * avg_prec * avg_rec / (beta2 * avg_prec + avg_rec)
    return chrf * 100


def chrf_corpus(hypotheses, references, char_order=6, word_order=2, beta=2):
    scores = [chrf_sentence(h, r, char_order, word_order, beta)
              for h, r in zip(hypotheses, references)]
    return np.mean(scores), scores


# ============================================================
# 5. TRAINING AND EVALUATION PIPELINE
# ============================================================

def run_benchmark(code):
    print(f'\n=== Benchmark: {code} ({REGISTRY[code]["script_family"]}) ===')
    
    train, val, test = load_all_splits(code)
    print(f'  Train: {len(train)} pairs, Val: {len(val)} pairs, Test: {len(test)} pairs')
    
    model = CharNgramTransducer(n=6)
    model.fit(train)
    
    val_sources = [s for s, t in val]
    val_targets = [t for s, t in val]
    val_preds = model.predict_batch(val_sources)
    val_chrf, val_scores = chrf_corpus(val_preds, val_targets)
    print(f'  Val chrF++: {val_chrf:.2f}')
    
    test_sources = [s for s, t in test]
    test_targets = [t for s, t in test]
    test_preds = model.predict_batch(test_sources)
    test_chrf, test_scores = chrf_corpus(test_preds, test_targets)
    print(f'  Test chrF++: {test_chrf:.2f}')
    
    print('  Sample predictions:')
    for i in range(min(3, len(test))):
        print(f'    Source:  {test_sources[i]}')
        print(f'    Target:  {test_targets[i]}')
        print(f'    Predict: {test_preds[i]}')
        print(f'    chrF++:  {test_scores[i]:.2f}')
        print()
    
    return {
        'code': code,
        'script_family': REGISTRY[code]['script_family'],
        'dev_bleu': REGISTRY[code]['dev_bleu'],
        'train_size': len(train),
        'val_size': len(val),
        'test_size': len(test),
        'val_chrf': val_chrf,
        'test_chrf': test_chrf,
        'test_scores': test_scores,
        'test_sources': test_sources,
        'test_targets': test_targets,
        'test_preds': test_preds,
    }


# ============================================================
# 6. MAIN EXECUTION
# ============================================================

def main():
    print('Morphological Segmentation Benchmark Analysis')
    print('=' * 60)
    
    results = {}
    for code in SELECTED:
        results[code] = run_benchmark(code)
    
    summary = {}
    for code, r in results.items():
        summary[code] = {
            'script_family': r['script_family'],
            'dev_bleu': r['dev_bleu'],
            'train_size': r['train_size'],
            'val_size': r['val_size'],
            'test_size': r['test_size'],
            'val_chrf': r['val_chrf'],
            'test_chrf': r['test_chrf'],
            'test_scores': r['test_scores'],
        }
    
    os.makedirs('outputs', exist_ok=True)
    with open('outputs/results.json', 'w') as f:
        json.dump(summary, f, indent=2)
    print('\nResults saved to outputs/results.json')
    
    os.makedirs('report/images', exist_ok=True)
    
    palette = {'Latin': '#4C72B0', 'Arabic': '#DD8452', 'Greek': '#55A868',
               'Cyrillic': '#C44E52', 'Devanagari': '#8172B2'}
    codes = list(results.keys())
    chrf_scores = [results[c]['test_chrf'] for c in codes]
    script_families = [results[c]['script_family'] for c in codes]
    colors = [palette[sf] for sf in script_families]
    
    # --- Figure 1: Test chrF++ per benchmark ---
    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(codes, chrf_scores, color=colors, edgecolor='black', linewidth=0.8, width=0.6)
    for bar, score in zip(bars, chrf_scores):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{score:.1f}', ha='center', va='bottom', fontsize=11, fontweight='bold')
    legend_patches = [mpatches.Patch(color=palette[sf], label=sf) for sf in palette]
    ax.legend(handles=legend_patches, title='Script Family', loc='lower right', fontsize=9)
    ax.set_xlabel('Benchmark Code', fontsize=12)
    ax.set_ylabel('chrF++ Score (%)', fontsize=12)
    ax.set_title('Test chrF++ Scores by Benchmark\n(Character-level N-gram Transducer)', fontsize=13)
    ax.set_ylim(0, 110)
    ax.grid(axis='y', alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    plt.savefig('report/images/fig1_test_chrf_scores.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('Saved fig1_test_chrf_scores.png')
    
    # --- Figure 2: chrF++ vs dev_bleu scatter ---
    fig, ax = plt.subplots(figsize=(7, 5))
    dev_bleus = [results[c]['dev_bleu'] for c in codes]
    for code, db, tc, sf in zip(codes, dev_bleus, chrf_scores, script_families):
        ax.scatter(db, tc, color=palette[sf], s=120, edgecolors='black', linewidth=0.8, zorder=5)
        ax.annotate(code, (db, tc), textcoords='offset points', xytext=(6, 4), fontsize=10)
    z = np.polyfit(dev_bleus, chrf_scores, 1)
    p = np.poly1d(z)
    x_line = np.linspace(min(dev_bleus)-0.02, max(dev_bleus)+0.02, 100)
    ax.plot(x_line, p(x_line), 'k--', alpha=0.4, linewidth=1.5, label='Linear trend')
    legend_patches = [mpatches.Patch(color=palette[sf], label=sf) for sf in palette]
    ax.legend(handles=legend_patches, title='Script Family', fontsize=9)
    ax.set_xlabel('Dev BLEU (from registry)', fontsize=12)
    ax.set_ylabel('Test chrF++ (%)', fontsize=12)
    ax.set_title('Test chrF++ vs. Dev BLEU\nCorrelation across Benchmarks', fontsize=13)
    ax.grid(alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    plt.savefig('report/images/fig2_chrf_vs_devbleu.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('Saved fig2_chrf_vs_devbleu.png')
    
    # --- Figure 3: Per-sample chrF++ scores ---
    fig, ax = plt.subplots(figsize=(9, 5))
    for i, code in enumerate(codes):
        subset = np.array(results[code]['test_scores'])
        jitter = np.random.uniform(-0.15, 0.15, len(subset))
        ax.scatter([i + j for j in jitter], subset,
                   color=palette[results[code]['script_family']],
                   s=80, edgecolors='black', linewidth=0.6, alpha=0.85, zorder=5)
        ax.hlines(np.mean(subset), i-0.25, i+0.25, colors='black', linewidth=2, zorder=6)
    ax.set_xticks(list(range(len(codes))))
    ax.set_xticklabels(codes, fontsize=11)
    ax.set_xlabel('Benchmark Code', fontsize=12)
    ax.set_ylabel('chrF++ Score (%)', fontsize=12)
    ax.set_title('Per-Sample Test chrF++ Distribution\n(horizontal bar = mean)', fontsize=13)
    ax.set_ylim(0, 110)
    ax.grid(axis='y', alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    legend_patches = [mpatches.Patch(color=palette[sf], label=sf) for sf in palette]
    ax.legend(handles=legend_patches, title='Script Family', loc='lower right', fontsize=9)
    plt.tight_layout()
    plt.savefig('report/images/fig3_per_sample_chrf.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('Saved fig3_per_sample_chrf.png')
    
    # --- Figure 4: Val vs Test chrF++ comparison ---
    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(codes))
    width = 0.35
    val_scores = [results[c]['val_chrf'] for c in codes]
    bars1 = ax.bar(x - width/2, val_scores, width, label='Val chrF++',
                   color='#5B9BD5', edgecolor='black', linewidth=0.7)
    bars2 = ax.bar(x + width/2, chrf_scores, width, label='Test chrF++',
                   color='#ED7D31', edgecolor='black', linewidth=0.7)
    for bar, score in zip(bars1, val_scores):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{score:.1f}', ha='center', va='bottom', fontsize=9)
    for bar, score in zip(bars2, chrf_scores):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{score:.1f}', ha='center', va='bottom', fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels(codes, fontsize=11)
    ax.set_xlabel('Benchmark Code', fontsize=12)
    ax.set_ylabel('chrF++ Score (%)', fontsize=12)
    ax.set_title('Validation vs. Test chrF++ Scores per Benchmark', fontsize=13)
    ax.set_ylim(0, 115)
    ax.legend(fontsize=10)
    ax.grid(axis='y', alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    plt.savefig('report/images/fig4_val_vs_test.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('Saved fig4_val_vs_test.png')
    
    # --- Figure 5: Benchmark distribution heatmap ---
    fig, ax = plt.subplots(figsize=(8, 4))
    all_codes = ['KWP','HLP','ZTE','ZAX','CWR','HKN','PUV','USY','WVZ',
                 'FGL','OOG','HIB','OSV','VDN','MDA','DWN','NWK','BJP']
    all_dev_bleus = [0.1912,0.245,0.2989,0.3497,0.3945,0.4251,0.4534,
                     0.5191,0.5785,0.6196,0.6425,0.6645,0.7316,0.748,
                     0.8107,0.8753,0.9235,0.9581]
    all_scripts = ['Latin','Cyrillic','Arabic','Devanagari','Greek',
                   'Latin','Cyrillic','Arabic','Devanagari','Greek',
                   'Latin','Cyrillic','Arabic','Devanagari','Greek',
                   'Latin','Cyrillic','Arabic']
    script_order = ['Latin','Cyrillic','Arabic','Devanagari','Greek']
    script_to_idx = {s: i for i, s in enumerate(script_order)}
    bins = [0, 0.3, 0.5, 0.7, 1.0]
    bin_labels = ['0.0-0.3', '0.3-0.5', '0.5-0.7', '0.7-1.0']
    matrix = np.zeros((len(script_order), len(bin_labels)))
    for code, db, sf in zip(all_codes, all_dev_bleus, all_scripts):
        for bi, (lo, hi) in enumerate(zip(bins[:-1], bins[1:])):
            if lo <= db < hi or (bi == len(bin_labels)-1 and db >= 0.7):
                matrix[script_to_idx[sf], bi] += 1
                break
    im = ax.imshow(matrix, cmap='YlOrRd', aspect='auto', vmin=0, vmax=3)
    ax.set_xticks(range(len(bin_labels)))
    ax.set_xticklabels(bin_labels, fontsize=10)
    ax.set_yticks(range(len(script_order)))
    ax.set_yticklabels(script_order, fontsize=10)
    ax.set_xlabel('Dev BLEU Range', fontsize=11)
    ax.set_ylabel('Script Family', fontsize=11)
    ax.set_title('Benchmark Distribution: Script Family x Difficulty (count per cell)', fontsize=12)
    for i in range(len(script_order)):
        for j in range(len(bin_labels)):
            val = int(matrix[i, j])
            ax.text(j, i, str(val), ha='center', va='center',
                    fontsize=12, fontweight='bold',
                    color='white' if val >= 2 else 'black')
    for code in SELECTED:
        idx_code = all_codes.index(code)
        db = all_dev_bleus[idx_code]
        sf = all_scripts[idx_code]
        for bi, (lo, hi) in enumerate(zip(bins[:-1], bins[1:])):
            if lo <= db < hi or (bi == len(bin_labels)-1 and db >= 0.7):
                ax.add_patch(plt.Rectangle((bi-0.5, script_to_idx[sf]-0.5),
                                           1, 1, fill=False,
                                           edgecolor='blue', linewidth=2.5))
                break
    plt.colorbar(im, ax=ax, label='Count')
    plt.tight_layout()
    plt.savefig('report/images/fig5_benchmark_distribution.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('Saved fig5_benchmark_distribution.png')
    
    # Print summary
    print('\n' + '='*60)
    print('SUMMARY TABLE')
    print('='*60)
    print(f'{"Code":<6} {"Script":<12} {"DevBLEU":<10} {"ValchrF++":<12} {"TestchrF++":<12}')
    print('-'*60)
    for code in SELECTED:
        r = results[code]
        print(f'{code:<6} {r["script_family"]:<12} {r["dev_bleu"]:<10.4f} '
              f'{r["val_chrf"]:<12.2f} {r["test_chrf"]:<12.2f}')
    print('='*60)
    
    return results, summary


if __name__ == '__main__':
    results, summary = main()
