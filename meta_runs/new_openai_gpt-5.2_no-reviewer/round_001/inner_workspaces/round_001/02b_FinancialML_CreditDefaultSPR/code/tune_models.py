from __future__ import annotations

"""Lightweight hyperparameter tuning on the validation split.

The symbolic sequence has no separators, so character n-gram TF-IDF is the
natural baseline. We tune LogisticRegression(C) and n-gram range.

Outputs:
- outputs/tuning_char_tfidf.csv
- outputs/tuning_char_tfidf_best.json
"""

import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from run_experiment import SEED, SequenceStats, load_metric_spec, eval_all_metrics


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if 'label' not in df.columns and 'default_flag' in df.columns:
        df = df.rename(columns={'default_flag': 'label'})
    return df


def build_char_model(C: float, ngram_range=(3, 6), min_df: int = 1, max_df: float = 0.95) -> Pipeline:
    char = TfidfVectorizer(
        analyzer='char',
        ngram_range=tuple(ngram_range),
        min_df=min_df,
        max_df=max_df,
        sublinear_tf=True,
    )
    feats = ColumnTransformer(
        transformers=[
            ('char', char, 'sym_seq'),
            ('stats', SequenceStats('sym_seq'), ['sym_seq']),
        ],
        remainder='drop',
        sparse_threshold=0.3,
    )
    clf = LogisticRegression(
        solver='saga',
        penalty='l2',
        C=C,
        max_iter=6000,
        n_jobs=-1,
        class_weight='balanced',
        random_state=SEED,
    )
    return Pipeline([('feats', feats), ('clf', clf)])


def main():
    Path('outputs').mkdir(parents=True, exist_ok=True)

    train = normalize(pd.read_csv('data/train.csv'))
    val = normalize(pd.read_csv('data/val.csv'))

    metric_spec = load_metric_spec()

    grid = {
        'C': [0.25, 0.5, 1.0, 2.0, 4.0, 8.0],
        'ngram_range': [(2, 4), (3, 5), (3, 6), (4, 6)],
        'min_df': [1, 2, 3],
    }

    rows = []
    best = None

    for C, ngr, min_df in itertools.product(grid['C'], grid['ngram_range'], grid['min_df']):
        model = build_char_model(C=C, ngram_range=ngr, min_df=min_df)
        model.fit(train, train['label'].values)
        val_prob = model.predict_proba(val)[:, 1]
        m = eval_all_metrics(val['label'].values, val_prob, metric_spec)
        row = {'C': C, 'ngram_range': str(ngr), 'min_df': min_df, **m}
        rows.append(row)
        if best is None or (row['roc_auc'], row['spr']) > (best['roc_auc'], best['spr']):
            best = row
        print(row)

    df = pd.DataFrame(rows).sort_values(['roc_auc', 'spr'], ascending=False)
    df.to_csv('outputs/tuning_char_tfidf.csv', index=False)
    Path('outputs/tuning_char_tfidf_best.json').write_text(json.dumps(best, indent=2))
    print('BEST', best)


if __name__ == '__main__':
    main()
