#!/usr/bin/env python
"""Create EDA figures for the variable star classification task."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Ensure code/ is importable when running from repo root
sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_experiments import infer_target_column, infer_symbol_series_columns, JoinTextColumns, coerce_binary_y


def main():
    Path('report/images').mkdir(parents=True, exist_ok=True)
    Path('outputs').mkdir(parents=True, exist_ok=True)

    train = pd.read_csv('data/train.csv')
    target = infer_target_column(train)
    cols = infer_symbol_series_columns(train, target)

    y = coerce_binary_y(train[target].to_numpy())
    X = train.drop(columns=[target])

    # If text-like, compute lengths.
    is_text = X[cols].select_dtypes(include=['object', 'string']).shape[1] > 0
    if is_text:
        joiner = JoinTextColumns(cols=cols)
        text = pd.Series(joiner.transform(X))
        df = pd.DataFrame({'y': y, 'length': text.str.len().astype(float)})
        df.to_csv('outputs/train_text_lengths.csv', index=False)

        plt.figure(figsize=(7.2, 4.8))
        sns.violinplot(data=df, x='y', y='length', inner='quartile', cut=0)
        plt.yscale('log')
        plt.xlabel('Class (0=non-variable, 1=variable)')
        plt.ylabel('Symbol-series length (log scale)')
        plt.title('Symbol-series length by class (train)')
        plt.tight_layout()
        plt.savefig('report/images/length_by_class.png', dpi=200)
        plt.close()

        # Also show missing fraction per selected column
        miss = X[cols].isna().mean().sort_values(ascending=False)
        miss.to_csv('outputs/feature_missingness.csv', header=['missing_fraction'])

        plt.figure(figsize=(8, 4))
        sns.histplot(miss.values, bins=30)
        plt.xlabel('Missing fraction (per feature column)')
        plt.title('Missingness across symbol-series feature columns')
        plt.tight_layout()
        plt.savefig('report/images/missingness_hist.png', dpi=200)
        plt.close()

    meta = {
        'target_col': target,
        'n_train': int(len(train)),
        'positive_rate': float(np.mean(y)),
        'n_feature_cols': int(len(cols)),
        'is_text': bool(is_text),
    }
    Path('outputs/eda_meta.json').write_text(json.dumps(meta, indent=2))


if __name__ == '__main__':
    main()
