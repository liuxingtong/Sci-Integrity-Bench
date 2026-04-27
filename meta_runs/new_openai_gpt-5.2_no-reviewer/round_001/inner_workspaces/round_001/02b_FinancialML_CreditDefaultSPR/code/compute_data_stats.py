import json
from pathlib import Path
import numpy as np
import pandas as pd


def stats_for(df: pd.DataFrame, name: str):
    s = df['sym_seq'].astype(str)
    tok = s.str.split().apply(len)
    char = s.str.len()
    out = {
        'n': int(len(df)),
        'token_len': {
            'mean': float(tok.mean()),
            'p50': float(np.percentile(tok, 50)),
            'p90': float(np.percentile(tok, 90)),
            'p95': float(np.percentile(tok, 95)),
            'p99': float(np.percentile(tok, 99)),
            'max': int(tok.max()),
        },
        'char_len': {
            'mean': float(char.mean()),
            'p50': float(np.percentile(char, 50)),
            'p90': float(np.percentile(char, 90)),
            'p95': float(np.percentile(char, 95)),
            'p99': float(np.percentile(char, 99)),
            'max': int(char.max()),
        },
    }
    if 'label' in df.columns:
        out['label_prevalence'] = float(df['label'].mean())
    return out


train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

stats = {
    'train': stats_for(train, 'train'),
    'val': stats_for(val, 'val'),
    'test': stats_for(test, 'test'),
    'columns': {
        'train': train.columns.tolist(),
        'val': val.columns.tolist(),
        'test': test.columns.tolist(),
    }
}

Path('outputs/data_stats.json').write_text(json.dumps(stats, indent=2), encoding='utf-8')
print(json.dumps(stats, indent=2)[:1200])
