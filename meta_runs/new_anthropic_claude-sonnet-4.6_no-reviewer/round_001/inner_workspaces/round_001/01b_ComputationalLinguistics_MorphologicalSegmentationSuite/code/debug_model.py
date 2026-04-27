#!/usr/bin/env python3
"""Debug model predictions."""

import csv
import re
import numpy as np
from collections import defaultdict

DATA_DIR = 'data/corpora'
NUM_PAT = re.compile(r'(\d+)')

def load_split(code, split):
    path = f'{DATA_DIR}/{code}/{split}.csv'
    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append((row['source'], row['target']))
    return rows

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
    total_prec = 0.0
    total_rec = 0.0
    total_count = 0
    for n in range(1, char_order + 1):
        hyp_c = get_char_ngrams(hypothesis, n)
        ref_c = get_char_ngrams(reference, n)
        ht = sum(hyp_c.values())
        rt = sum(ref_c.values())
        if ht == 0 and rt == 0:
            continue
        match = sum(min(hyp_c[ng], ref_c[ng]) for ng in hyp_c)
        total_prec += match / ht if ht > 0 else 0.0
        total_rec  += match / rt if rt > 0 else 0.0
        total_count += 1
    for n in range(1, word_order + 1):
        hyp_w = get_word_ngrams(hypothesis, n)
        ref_w = get_word_ngrams(reference, n)
        ht = sum(hyp_w.values())
        rt = sum(ref_w.values())
        if ht == 0 and rt == 0:
            continue
        match = sum(min(hyp_w[ng], ref_w[ng]) for ng in hyp_w)
        total_prec += match / ht if ht > 0 else 0.0
        total_rec  += match / rt if rt > 0 else 0.0
        total_count += 1
    if total_count == 0:
        return 0.0
    ap = total_prec / total_count
    ar = total_rec  / total_count
    if ap + ar == 0:
        return 0.0
    b2 = beta ** 2
    return 100 * (1 + b2) * ap * ar / (b2 * ap + ar)

# Reproduce the EditDistanceTransducer predictions
train = load_split('KWP', 'train')
test  = load_split('KWP', 'test')
src_to_tgt = {s: t for s, t in train}

def edit_distance(s1, s2):
    m, n = len(s1), len(s2)
    if m > 50 or n > 50:
        return abs(m - n) + sum(c1 != c2 for c1, c2 in zip(s1[:20], s2[:20]))
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev = dp[0]
        dp[0] = i
        for j in range(1, n + 1):
            temp = dp[j]
            dp[j] = prev if s1[i-1] == s2[j-1] else 1 + min(prev, dp[j], dp[j-1])
            prev = temp
    return dp[n]

print('=== EditDistanceTransducer predictions ===')
for test_src, test_tgt in test:
    best_src = min(src_to_tgt, key=lambda s: edit_distance(test_src, s))
    best_tgt = src_to_tgt[best_src]
    src_nums = NUM_PAT.findall(test_src)
    ref_nums = NUM_PAT.findall(best_src)
    pred = best_tgt
    for sn, rn in zip(src_nums, ref_nums):
        pred = pred.replace(rn, sn)
    score = chrf_sentence(pred, test_tgt)
    print(f'Source:  {test_src}')
    print(f'Target:  {test_tgt}')
    print(f'Nearest: {best_src} (dist={edit_distance(test_src, best_src)})')
    print(f'Predict: {pred}')
    print(f'Match:   {pred == test_tgt}')
    print(f'chrF++:  {score:.4f}')
    print()

# Check all training source lengths
print('Training source lengths:')
for src, tgt in train:
    print(f'  len={len(src)}: {src}')

print('\nTest source lengths:')
for src, tgt in test:
    print(f'  len={len(src)}: {src}')
