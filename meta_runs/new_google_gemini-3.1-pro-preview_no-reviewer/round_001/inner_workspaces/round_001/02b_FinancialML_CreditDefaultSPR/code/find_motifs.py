import pandas as pd
import numpy as np
from collections import Counter

train = pd.read_csv('outputs/train.csv')

def get_all_substrings(seq, min_len=1, max_len=20):
    substrings = []
    for i in range(len(seq)):
        for j in range(i + min_len, min(i + max_len + 1, len(seq) + 1)):
            substrings.append(seq[i:j])
    return substrings

pos_seqs = train[train['default_flag'] == 1]['sym_seq']
neg_seqs = train[train['default_flag'] == 0]['sym_seq']

pos_substrings = []
for seq in pos_seqs:
    pos_substrings.extend(list(set(get_all_substrings(seq, 1, 20))))
    
neg_substrings = []
for seq in neg_seqs:
    neg_substrings.extend(list(set(get_all_substrings(seq, 1, 20))))

pos_counts = Counter(pos_substrings)
neg_counts = Counter(neg_substrings)

all_substrings = set(pos_counts.keys()).union(set(neg_counts.keys()))

motifs = []
for sub in all_substrings:
    p = pos_counts.get(sub, 0)
    n = neg_counts.get(sub, 0)
    if p + n >= 5:
        ratio = (p + 1) / (n + 1)
        motifs.append((sub, p, n, ratio))

motifs.sort(key=lambda x: x[3], reverse=True)
print("Top positive motifs:")
for m in motifs[:20]:
    print(m)
    
motifs.sort(key=lambda x: x[3])
print("\nTop negative motifs:")
for m in motifs[:20]:
    print(m)
