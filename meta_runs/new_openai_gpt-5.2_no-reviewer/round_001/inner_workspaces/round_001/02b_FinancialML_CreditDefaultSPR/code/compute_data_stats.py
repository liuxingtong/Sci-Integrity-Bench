from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if 'label' not in df.columns and 'default_flag' in df.columns:
        df = df.rename(columns={'default_flag': 'label'})
    return df


def stats(df: pd.DataFrame):
    s = df['sym_seq'].astype(str)
    lens = s.str.len()
    return {
        'n': int(len(df)),
        'pos_rate': float(df['label'].mean()),
        'seq_len_char_mean': float(lens.mean()),
        'seq_len_char_med': float(lens.median()),
        'seq_len_char_min': int(lens.min()),
        'seq_len_char_max': int(lens.max()),
    }


def main():
    train = normalize(pd.read_csv('data/train.csv'))
    val = normalize(pd.read_csv('data/val.csv'))
    test = normalize(pd.read_csv('data/test.csv'))
    out = {'train': stats(train), 'val': stats(val), 'test': stats(test)}
    Path('outputs').mkdir(parents=True, exist_ok=True)
    Path('outputs/data_stats.json').write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == '__main__':
    main()
