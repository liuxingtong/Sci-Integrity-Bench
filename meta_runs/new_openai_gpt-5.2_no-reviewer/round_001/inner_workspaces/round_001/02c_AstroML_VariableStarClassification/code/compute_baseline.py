#!/usr/bin/env python
"""Compute simple baselines per protocol: majority/constant score."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

import sys
from pathlib import Path as _Path
sys.path.insert(0, str(_Path(__file__).resolve().parent))

from run_experiments import infer_target_column, coerce_binary_y, evaluate


def main():
    Path('outputs').mkdir(parents=True, exist_ok=True)

    train = pd.read_csv('data/train.csv')
    target = infer_target_column(train)

    def load(split):
        df = pd.read_csv(f'data/{split}.csv')
        y = coerce_binary_y(df[target].to_numpy())
        return y

    y_train = load('train')
    y_val = load('val')
    y_test = load('test')

    p = float(np.mean(y_train))

    # Constant probability baseline
    val_score = np.full_like(y_val, fill_value=p, dtype=float)
    test_score = np.full_like(y_test, fill_value=p, dtype=float)

    out = {
        'target_col': target,
        'train_positive_rate': p,
        'val': evaluate(y_val, val_score, threshold=0.5),
        'test': evaluate(y_test, test_score, threshold=0.5),
    }

    Path('outputs/baseline_constantprob.json').write_text(json.dumps(out, indent=2))

    # Majority class hard baseline
    maj = int(p >= 0.5)
    val_score2 = np.full_like(y_val, fill_value=float(maj), dtype=float)
    test_score2 = np.full_like(y_test, fill_value=float(maj), dtype=float)
    out2 = {
        'target_col': target,
        'train_positive_rate': p,
        'majority_class': maj,
        'val': evaluate(y_val, val_score2, threshold=0.5),
        'test': evaluate(y_test, test_score2, threshold=0.5),
    }
    Path('outputs/baseline_majority.json').write_text(json.dumps(out2, indent=2))


if __name__ == '__main__':
    main()
