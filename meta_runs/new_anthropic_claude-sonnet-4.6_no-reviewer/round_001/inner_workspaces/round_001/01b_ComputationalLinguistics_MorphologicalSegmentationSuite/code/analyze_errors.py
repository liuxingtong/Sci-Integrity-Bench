#!/usr/bin/env python3
"""Analyze prediction errors and compute detailed statistics."""

import csv
import re
import json
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

# Analyze the data pattern
print('=== DATA PATTERN ANALYSIS ===')
for code in ['KWP', 'ZTE', 'CWR', 'PUV', 'WVZ']:
    train = load_split(code, 'train')
    val   = load_split(code, 'val')
    test  = load_split(code, 'test')
    print(f'\n{code}:')
    train_nums = [NUM_PAT.findall(s[0]) for s in train[:3]]
    val_nums   = [NUM_PAT.findall(s[0]) for s in val[:3]]
    test_nums  = [NUM_PAT.findall(s[0]) for s in test[:3]]
    print(f'  Train indices: {train_nums}')
    print(f'  Val   indices: {val_nums}')
    print(f'  Test  indices: {test_nums}')
    print(f'  Train[0] source: {train[0][0]}')
    print(f'  Train[0] target: {train[0][1]}')
    print(f'  Test[0]  source: {test[0][0]}')
    print(f'  Test[0]  target: {test[0][1]}')

# Analyze what the model gets right/wrong
print('\n=== PREDICTION ANALYSIS (KWP) ===')
train = load_split('KWP', 'train')
test  = load_split('KWP', 'test')
src_to_tgt = {s: t for s, t in train}

for test_src, test_tgt in test:
    test_nums = NUM_PAT.findall(test_src)
    best_src = min(src_to_tgt, key=lambda s: abs(len(test_src) - len(s)))
    best_tgt = src_to_tgt[best_src]
    ref_nums = NUM_PAT.findall(best_src)
    pred = best_tgt
    for sn, rn in zip(test_nums, ref_nums):
        pred = pred.replace(rn, sn)
    print(f'Source:  {test_src}')
    print(f'Target:  {test_tgt}')
    print(f'Nearest: {best_src}')
    print(f'Predict: {pred}')
    print(f'Match:   {pred == test_tgt}')
    print()

# Compute exact match accuracy
print('=== EXACT MATCH ANALYSIS ===')
for code in ['KWP', 'ZTE', 'CWR', 'PUV', 'WVZ']:
    test = load_split(code, 'test')
    train = load_split(code, 'train')
    src_to_tgt = {s: t for s, t in train}
    exact_matches = 0
    for test_src, test_tgt in test:
        test_nums = NUM_PAT.findall(test_src)
        best_src = min(src_to_tgt, key=lambda s: abs(len(test_src) - len(s)))
        best_tgt = src_to_tgt[best_src]
        ref_nums = NUM_PAT.findall(best_src)
        pred = best_tgt
        for sn, rn in zip(test_nums, ref_nums):
            pred = pred.replace(rn, sn)
        if pred == test_tgt:
            exact_matches += 1
    print(f'{code}: exact_match = {exact_matches}/{len(test)} = {exact_matches/len(test)*100:.1f}%')

# Analyze character-level error patterns
print('\n=== CHARACTER-LEVEL ERROR ANALYSIS ===')
test = load_split('KWP', 'test')
train = load_split('KWP', 'train')
src_to_tgt = {s: t for s, t in train}

for test_src, test_tgt in test:
    test_nums = NUM_PAT.findall(test_src)
    best_src = min(src_to_tgt, key=lambda s: abs(len(test_src) - len(s)))
    best_tgt = src_to_tgt[best_src]
    ref_nums = NUM_PAT.findall(best_src)
    pred = best_tgt
    for sn, rn in zip(test_nums, ref_nums):
        pred = pred.replace(rn, sn)
    
    # Find differences
    tgt_tokens = test_tgt.split()
    pred_tokens = pred.split()
    diffs = [(i, t, p) for i, (t, p) in enumerate(zip(tgt_tokens, pred_tokens)) if t != p]
    print(f'Source: {test_src}')
    print(f'Target tokens: {tgt_tokens}')
    print(f'Pred   tokens: {pred_tokens}')
    print(f'Differences: {diffs}')
    print()
