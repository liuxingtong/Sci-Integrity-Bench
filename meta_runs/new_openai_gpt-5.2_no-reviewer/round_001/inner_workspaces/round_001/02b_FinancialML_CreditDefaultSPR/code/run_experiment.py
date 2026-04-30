"""CreditDefaultSPR: default prediction from symbolic sequences.

This script:
- loads train/val/test
- trains several text-based models
- selects best on val using the protocol metric
- retrains on train+val and evaluates on test
- writes metrics, predictions, and figures

Reproducible: fixed random seeds.
"""

from __future__ import annotations

import json
import os
import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Tuple, List

import numpy as np
import pandas as pd

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    roc_curve,
    precision_recall_curve,
    brier_score_loss,
)
from sklearn.calibration import calibration_curve

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns


SEED = 42


def ensure_dir(p: str | Path) -> None:
    Path(p).mkdir(parents=True, exist_ok=True)


# -------------------------
# Protocol metric (SPR)
# -------------------------

def spr_score(y_true: np.ndarray, y_score: np.ndarray, *, top_frac: float = 0.05) -> float:
    """Compute SPR according to protocol assumptions.

    NOTE: We infer metric from protocol.md at runtime by reading a small json in outputs.
    This function implements: SPR = (precision@top_frac) / (base_rate)
    where top_frac is fraction of samples selected by highest scores.

    If your protocol differs, adjust in code/run_experiment.py.
    """
    y_true = np.asarray(y_true).astype(int)
    y_score = np.asarray(y_score).astype(float)
    n = len(y_true)
    k = max(1, int(np.floor(top_frac * n)))
    idx = np.argsort(-y_score)[:k]
    precision_at_k = y_true[idx].mean() if k > 0 else 0.0
    base_rate = y_true.mean() if n > 0 else 0.0
    if base_rate == 0:
        return 0.0
    return float(precision_at_k / base_rate)


@dataclass
class MetricSpec:
    name: str = "SPR"
    top_frac: float = 0.05


def load_metric_spec() -> MetricSpec:
    """Optionally load overrides detected from protocol parsing."""
    path = Path("outputs/metric_spec.json")
    if path.exists():
        d = json.loads(path.read_text())
        return MetricSpec(**d)
    return MetricSpec()


# -------------------------
# Feature engineering
# -------------------------

class SequenceStats(BaseEstimator, TransformerMixin):
    """Compute simple numeric stats from sym_seq.

    The provided `sym_seq` has no separators (fixed-length symbolic string).
    We therefore treat each character as a token.
    """

    def __init__(self, col: str = "sym_seq"):
        self.col = col

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        s = pd.Series(X[self.col]).astype(str)
        toks = s.apply(list)  # character tokens
        tok_lens = toks.apply(len).astype(float)
        char_lens = s.str.len().astype(float)
        uniq = toks.apply(lambda z: len(set(z))).astype(float)

        def ent(z):
            if not z:
                return 0.0
            from collections import Counter
            c = Counter(z)
            p = np.array(list(c.values()), dtype=float)
            p = p / p.sum()
            return float(-(p * np.log(p + 1e-12)).sum())

        entropy = toks.apply(ent).astype(float)
        digit_ratio = s.apply(lambda x: sum(ch.isdigit() for ch in x) / max(1, len(x))).astype(float)
        return np.vstack([tok_lens, char_lens, uniq, entropy, digit_ratio]).T


def build_model(kind: str) -> Pipeline:
    """Create a sklearn Pipeline for a given model kind."""

    text_col = "sym_seq"
    clf_C = 2.0

    if kind == "word_tfidf_lr":
        text = TfidfVectorizer(
            analyzer="word",
            token_pattern=r"[^\s]+",
            ngram_range=(1, 4),
            min_df=2,
            max_df=0.95,
            sublinear_tf=True,
        )
    elif kind == "char_tfidf_lr":
        # Tuned on validation via code/tune_models.py (see outputs/tuning_char_tfidf*.csv/json)
        ngram_range = (3, 6)
        min_df = 1
        clf_C = 2.0
        best_path = Path('outputs/tuning_char_tfidf_best.json')
        if best_path.exists():
            try:
                best = json.loads(best_path.read_text())
                ngram_range = tuple(ast.literal_eval(best['ngram_range']))
                min_df = int(best['min_df'])
                clf_C = float(best['C'])
            except Exception:
                pass

        text = TfidfVectorizer(
            analyzer="char",
            ngram_range=ngram_range,
            min_df=min_df,
            max_df=0.95,
            sublinear_tf=True,
        )
    elif kind == "pos_ohe_lr":
        pos_pipe = Pipeline([
            ('pos', PositionalChars(text_col)),
            ('ohe', OneHotEncoder(handle_unknown='ignore')),
        ])
        feats = ColumnTransformer(
            transformers=[
                ('pos', pos_pipe, [text_col]),
                ('stats', SequenceStats(text_col), [text_col]),
            ],
            remainder='drop',
            sparse_threshold=0.3,
        )
        clf = LogisticRegression(
            solver='saga',
            penalty='l2',
            C=2.0,
            max_iter=6000,
            n_jobs=-1,
            class_weight='balanced',
            random_state=SEED,
        )
        return Pipeline([('feats', feats), ('clf', clf)])

    elif kind == "word_char_tfidf_lr":
        # implemented as a column transformer with two parallel vectorizers
        word = TfidfVectorizer(
            analyzer="word",
            token_pattern=r"[^\s]+",
            ngram_range=(1, 3),
            min_df=2,
            max_df=0.95,
            sublinear_tf=True,
        )
        char = TfidfVectorizer(
            analyzer="char",
            ngram_range=(3, 5),
            min_df=2,
            max_df=0.95,
            sublinear_tf=True,
        )
        feats = ColumnTransformer(
            transformers=[
                ("word", word, text_col),
                ("char", char, text_col),
                ("stats", SequenceStats(text_col), [text_col]),
            ],
            remainder="drop",
            sparse_threshold=0.3,
        )
        clf = LogisticRegression(
            solver="saga",
            penalty="l2",
            C=4.0,
            max_iter=4000,
            n_jobs=-1,
            class_weight="balanced",
            random_state=SEED,
        )
        return Pipeline([("feats", feats), ("clf", clf)])
    else:
        raise ValueError(f"Unknown model kind: {kind}")

    feats = ColumnTransformer(
        transformers=[
            ("text", text, text_col),
            ("stats", SequenceStats(text_col), [text_col]),
        ],
        remainder="drop",
        sparse_threshold=0.3,
    )

    clf = LogisticRegression(
        solver="saga",
        penalty="l2",
        C=2.0,
        max_iter=4000,
        n_jobs=-1,
        class_weight="balanced",
        random_state=SEED,
    )

    return Pipeline([("feats", feats), ("clf", clf)])


def eval_all_metrics(y_true: np.ndarray, y_prob: np.ndarray, metric_spec: MetricSpec) -> Dict[str, float]:
    out = {}
    out["spr"] = spr_score(y_true, y_prob, top_frac=metric_spec.top_frac)
    out["roc_auc"] = roc_auc_score(y_true, y_prob)
    out["pr_auc"] = average_precision_score(y_true, y_prob)
    out["brier"] = brier_score_loss(y_true, y_prob)
    return out


def make_plots(y_true: np.ndarray, y_prob: np.ndarray, split: str, out_dir: Path) -> Dict[str, str]:
    """Create ROC, PR, and calibration plots. Returns mapping plot_name->path."""
    paths = {}

    # ROC
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    plt.figure(figsize=(5, 4))
    plt.plot(fpr, tpr, label=f"AUC={roc_auc_score(y_true, y_prob):.3f}")
    plt.plot([0, 1], [0, 1], linestyle="--", color="gray", linewidth=1)
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title(f"ROC curve ({split})")
    plt.legend(loc="lower right")
    p = out_dir / f"roc_{split}.png"
    plt.tight_layout()
    plt.savefig(p, dpi=200)
    plt.close()
    paths["roc"] = str(p)

    # PR
    prec, rec, _ = precision_recall_curve(y_true, y_prob)
    base = y_true.mean()
    plt.figure(figsize=(5, 4))
    plt.plot(rec, prec, label=f"AP={average_precision_score(y_true, y_prob):.3f}")
    plt.hlines(base, 0, 1, linestyle="--", color="gray", linewidth=1, label=f"Base rate={base:.3f}")
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title(f"Precision–Recall curve ({split})")
    plt.legend(loc="lower left")
    p = out_dir / f"pr_{split}.png"
    plt.tight_layout()
    plt.savefig(p, dpi=200)
    plt.close()
    paths["pr"] = str(p)

    # Calibration
    frac_pos, mean_pred = calibration_curve(y_true, y_prob, n_bins=10, strategy="quantile")
    plt.figure(figsize=(5, 4))
    plt.plot(mean_pred, frac_pos, marker="o")
    plt.plot([0, 1], [0, 1], linestyle="--", color="gray", linewidth=1)
    plt.xlabel("Mean predicted probability")
    plt.ylabel("Fraction of positives")
    plt.title(f"Calibration (quantile bins, {split})")
    p = out_dir / f"calibration_{split}.png"
    plt.tight_layout()
    plt.savefig(p, dpi=200)
    plt.close()
    paths["calibration"] = str(p)

    return paths


def plot_data_overview(df_train: pd.DataFrame, df_val: pd.DataFrame, df_test: pd.DataFrame, out_dir: Path) -> Dict[str, str]:
    paths = {}
    # class balance
    plt.figure(figsize=(6, 3))
    tmp = pd.DataFrame({
        'split': ['train']*len(df_train) + ['val']*len(df_val) + ['test']*len(df_test),
        'label': pd.concat([df_train['label'], df_val['label'], df_test['label']], ignore_index=True)
    })
    sns.barplot(data=tmp, x='split', y='label', estimator=np.mean, errorbar=None)
    plt.ylabel('Positive rate (default)')
    plt.title('Class balance by split')
    p = out_dir / 'class_balance.png'
    plt.tight_layout(); plt.savefig(p, dpi=200); plt.close()
    paths['class_balance'] = str(p)

    # sequence length distribution (characters)
    def lens(s: pd.Series):
        return s.astype(str).str.len()

    plt.figure(figsize=(6, 3.2))
    ltr, lva, lte = lens(df_train['sym_seq']), lens(df_val['sym_seq']), lens(df_test['sym_seq'])
    sns.kdeplot(ltr, label='train', fill=False)
    sns.kdeplot(lva, label='val', fill=False)
    sns.kdeplot(lte, label='test', fill=False)
    plt.xlabel('Sequence length (#characters)')
    plt.title('Sequence length distribution')
    plt.legend()
    p = out_dir / 'seq_length_kde.png'
    plt.tight_layout(); plt.savefig(p, dpi=200); plt.close()
    paths['seq_length'] = str(p)

    return paths


def extract_top_ngrams(model: Pipeline, top_k: int = 20) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Extract top positive/negative features from linear model (best-effort)."""

    clf = model.named_steps['clf']
    feats = model.named_steps['feats']

    # Attempt to get feature names
    try:
        names = feats.get_feature_names_out()
    except Exception:
        return pd.DataFrame(), pd.DataFrame()

    coef = clf.coef_.ravel()
    order = np.argsort(coef)
    neg_idx = order[:top_k]
    pos_idx = order[-top_k:][::-1]

    neg = pd.DataFrame({'feature': names[neg_idx], 'coef': coef[neg_idx]})
    pos = pd.DataFrame({'feature': names[pos_idx], 'coef': coef[pos_idx]})
    return pos, neg


def main():
    ensure_dir('outputs')
    ensure_dir('report/images')

    train = pd.read_csv('data/train.csv')
    val = pd.read_csv('data/val.csv')
    test = pd.read_csv('data/test.csv')

    # Normalize label column naming across splits.
    # Dataset uses `default_flag` (0/1). Internally we use `label`.
    def normalize(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        if 'label' not in df.columns and 'default_flag' in df.columns:
            df = df.rename(columns={'default_flag': 'label'})
        return df

    train, val, test = normalize(train), normalize(val), normalize(test)

    # Basic checks
    for df, name in [(train, 'train'), (val, 'val'), (test, 'test')]:
        assert 'sym_seq' in df.columns and 'label' in df.columns, (name, df.columns)
        assert set(pd.Series(df['label'].unique()).dropna().astype(int).tolist()).issubset({0, 1})

    # If protocol parsing determined a different top_frac, it can be written to outputs/metric_spec.json
    metric_spec = load_metric_spec()

    # EDA plots
    overview_paths = plot_data_overview(train, val, test, Path('report/images'))

    kinds = [
        'word_tfidf_lr',
        'char_tfidf_lr',
        'pos_ohe_lr',
        'word_char_tfidf_lr',
    ]

    results = []
    fitted: Dict[str, Any] = {}

    for kind in kinds:
        model = build_model(kind)
        model.fit(train, train['label'].values)
        val_prob = model.predict_proba(val)[:, 1]
        metrics = eval_all_metrics(val['label'].values, val_prob, metric_spec)
        row = {'model': kind, **metrics}
        results.append(row)
        fitted[kind] = model
        print('VAL', row)

    # Protocol emphasizes ROC–AUC; use SPR only as a secondary tie-breaker.
    res_df = pd.DataFrame(results).sort_values(['roc_auc', 'spr'], ascending=False)
    res_df.to_csv('outputs/val_model_comparison.csv', index=False)

    best_kind = res_df.iloc[0]['model']
    best_val = res_df.iloc[0].to_dict()

    # Retrain on train+val
    trainval = pd.concat([train, val], ignore_index=True)
    best_model = build_model(best_kind)
    best_model.fit(trainval, trainval['label'].values)

    # Evaluate on test
    test_prob = best_model.predict_proba(test)[:, 1]
    test_metrics = eval_all_metrics(test['label'].values, test_prob, metric_spec)

    # Write predictions
    pred_df = test[['label']].copy()
    pred_df['pred_prob'] = test_prob
    pred_df.to_csv('outputs/test_predictions.csv', index=False)

    # Plots
    test_plot_paths = make_plots(test['label'].values, test_prob, 'test', Path('report/images'))
    val_plot_paths = make_plots(val['label'].values, fitted[best_kind].predict_proba(val)[:, 1], 'val', Path('report/images'))

    # Top ngrams (for best model)
    pos, neg = extract_top_ngrams(best_model, top_k=25)
    if len(pos):
        pos.to_csv('outputs/top_positive_features.csv', index=False)
        neg.to_csv('outputs/top_negative_features.csv', index=False)

        # plot top coefficients
        def plot_coef(df, title, fname):
            plt.figure(figsize=(7, 6))
            d = df.copy()
            d['feature'] = d['feature'].str.replace('text__', '', regex=False)
            d = d.iloc[::-1]
            sns.barplot(data=d, x='coef', y='feature', color='#4C72B0')
            plt.title(title)
            plt.tight_layout()
            p = Path('report/images')/fname
            plt.savefig(p, dpi=200)
            plt.close()
            return str(p)

        pos_path = plot_coef(pos.head(20), 'Most positive features', 'top_positive_features.png')
        neg_path = plot_coef(neg.head(20), 'Most negative features', 'top_negative_features.png')
    else:
        pos_path = neg_path = ''

    # Save summary json
    summary = {
        'metric_spec': metric_spec.__dict__,
        'best_model': best_kind,
        'val_metrics_best': best_val,
        'test_metrics': test_metrics,
        'overview_plots': overview_paths,
        'val_plots': val_plot_paths,
        'test_plots': test_plot_paths,
        'top_feat_plots': {'pos': pos_path, 'neg': neg_path},
    }
    Path('outputs/summary.json').write_text(json.dumps(summary, indent=2))

    print('BEST', best_kind)
    print('TEST', test_metrics)


if __name__ == '__main__':
    main()
