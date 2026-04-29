import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score
import zlib

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

def get_compression_ratio(seq):
    compressed = zlib.compress(seq.encode('utf-8'))
    return len(compressed) / len(seq)

train['comp_ratio'] = train['sym_seq'].apply(get_compression_ratio)
val['comp_ratio'] = val['sym_seq'].apply(get_compression_ratio)

auc = roc_auc_score(val['default_flag'], val['comp_ratio'])
print(f'Compression Ratio Val AUC: {auc:.4f}')

auc_inv = roc_auc_score(val['default_flag'], -val['comp_ratio'])
print(f'Inverse Compression Ratio Val AUC: {auc_inv:.4f}')
