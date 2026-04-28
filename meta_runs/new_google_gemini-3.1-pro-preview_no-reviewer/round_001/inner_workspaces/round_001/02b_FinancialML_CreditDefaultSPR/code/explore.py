import pandas as pd
import numpy as np

train = pd.read_csv('data/train.csv')

# Check if there are specific motifs that correlate with default
from collections import defaultdict

motifs_0 = defaultdict(int)
motifs_1 = defaultdict(int)

for _, row in train.iterrows():
    seq = row['sym_seq']
    label = row['default_flag']
    for i in range(len(seq) - 2):
        motif = seq[i:i+3]
        if label == 0:
            motifs_0[motif] += 1
        else:
            motifs_1[motif] += 1

all_motifs = set(motifs_0.keys()) | set(motifs_1.keys())

for motif in all_motifs:
    c0 = motifs_0[motif]
    c1 = motifs_1[motif]
    if c0 + c1 > 10:
        ratio = c1 / (c0 + c1)
        if ratio > 0.7 or ratio < 0.3:
            print(f'Motif {motif}: {c0} vs {c1} (ratio {ratio:.2f})')
