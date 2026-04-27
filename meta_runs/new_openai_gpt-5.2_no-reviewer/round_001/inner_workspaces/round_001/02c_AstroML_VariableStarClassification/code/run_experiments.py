#!/usr/bin/env python
"""Variable star classification using symbol_series features.

This script:
- Loads fixed train/val/test splits from data/
- Selects symbol_series feature columns
- Trains text-based classifiers (character n-gram TF-IDF + logistic regression)
- Selects hyperparameters on val split
- Retrains on train+val and evaluates on test
- Writes metrics, predictions, and figures

Reproducible and self-contained.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.calibration import calibration_curve
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.pipeline import Pipeline

import matplotlib.pyplot as plt
import seaborn as sns

RANDOM_STATE = 42


@dataclass
class SplitData:
    X: pd.DataFrame
    y: np.ndarray


class JoinTextColumns(BaseEstimator, TransformerMixin):
    """Join selected columns (string-like) into a single text field per row."""

    def __init__(self, cols: list[str], sep: str = " "):
        self.cols = cols
        self.sep = sep

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X = pd.DataFrame(X)
        parts = []
        for c in self.cols:
            s = X[c]
            # Preserve missingness explicitly
            s = s.astype("string").fillna("")
            parts.append(s)
        joined = parts[0].str.cat(parts[1:], sep=self.sep) if len(parts) > 1 else parts[0]
        return joined.to_numpy()


def ensure_dirs():
    Path("outputs").mkdir(parents=True, exist_ok=True)
    Path("report/images").mkdir(parents=True, exist_ok=True)


def load_split(path: str, target_col: str) -> SplitData:
    df = pd.read_csv(path)
    y = df[target_col].to_numpy()
    X = df.drop(columns=[target_col])
    return SplitData(X=X, y=y)


def infer_target_column(df: pd.DataFrame) -> str:
    candidates = [
        c
        for c in df.columns
        if c.lower() in {"label", "target", "y", "class", "is_variable", "variable", "is_var"}
    ]
    if len(candidates) == 1:
        return candidates[0]
    if "label" in df.columns:
        return "label"
    # fallback: last column with 2 unique values
    for c in df.columns[::-1]:
        if df[c].nunique(dropna=True) == 2:
            return c
    raise ValueError("Could not infer target column.")


def infer_symbol_series_columns(df: pd.DataFrame, target_col: str) -> list[str]:
    cols = [c for c in df.columns if c != target_col]

    # Prefer explicit symbol_series naming
    sym = [c for c in cols if ("symbol" in c.lower() and "series" in c.lower())]
    if sym:
        return sym

    # Common prefixes
    prefixes = ("symbol_series", "symbolseries", "ss_", "ss", "sym_", "series_")
    pref = [c for c in cols if c.lower().startswith(prefixes)]
    if pref:
        return pref

    # Otherwise: all object/string columns
    obj = df[cols].select_dtypes(include=["object", "string"]).columns.tolist()
    if obj:
        return obj

    # Otherwise: use all remaining columns (already numeric)
    return cols


def coerce_binary_y(y: np.ndarray) -> np.ndarray:
    # Map common string labels to 0/1
    if y.dtype.kind in {"U", "S", "O"}:
        y_str = pd.Series(y).astype(str).str.lower()
        mapping = {"0": 0, "1": 1, "false": 0, "true": 1, "nonvariable": 0, "non-variable": 0,
                   "variable": 1, "var": 1, "non_var": 0, "non-var": 0}
        y_mapped = y_str.map(mapping)
        if y_mapped.isna().any():
            # try factorize
            vals = pd.unique(y_str)
            if len(vals) != 2:
                raise ValueError(f"Expected binary labels; got {vals}")
            y_fac, uniques = pd.factorize(y_str)
            return y_fac
        return y_mapped.to_numpy(dtype=int)

    # Numeric: ensure 0/1
    y = np.asarray(y)
    uniq = np.unique(y[~pd.isna(y)])
    if set(uniq.tolist()) <= {0, 1}:
        return y.astype(int)
    # If labels are {1,2} etc.
    if len(uniq) == 2:
        lo, hi = np.min(uniq), np.max(uniq)
        return (y == hi).astype(int)
    raise ValueError(f"Expected binary y; got unique values {uniq}")


def make_model(cols: list[str], ngram_range=(3, 5), min_df=2, C=4.0) -> Pipeline:
    # If columns are non-object numeric, we skip TF-IDF and join.
    # But pipeline expects text; therefore we only use this model for string columns.
    return Pipeline(
        steps=[
            ("join", JoinTextColumns(cols=cols, sep=" ")),
            (
                "tfidf",
                TfidfVectorizer(
                    analyzer="char",
                    ngram_range=ngram_range,
                    min_df=min_df,
                    lowercase=False,
                    sublinear_tf=True,
                    max_features=250_000,
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    solver="saga",
                    penalty="l2",
                    C=C,
                    max_iter=5000,
                    n_jobs=-1,
                    class_weight="balanced",
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )


def evaluate(y_true, y_score, threshold=0.5) -> dict:
    y_pred = (y_score >= threshold).astype(int)
    out = {
        "roc_auc": float(roc_auc_score(y_true, y_score)),
        "average_precision": float(average_precision_score(y_true, y_score)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "f1": float(f1_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "threshold": float(threshold),
        "n": int(len(y_true)),
        "positives": int(np.sum(y_true)),
    }
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    out.update({"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)})
    return out


def plot_roc_pr(y_true, y_score, prefix: str):
    fpr, tpr, _ = roc_curve(y_true, y_score)
    prec, rec, _ = precision_recall_curve(y_true, y_score)

    plt.figure(figsize=(6, 5))
    plt.plot(fpr, tpr, label=f"AUC={roc_auc_score(y_true, y_score):.3f}")
    plt.plot([0, 1], [0, 1], "--", color="gray", lw=1)
    plt.xlabel("False positive rate")
    plt.ylabel("True positive rate")
    plt.title(f"ROC curve ({prefix})")
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(f"report/images/{prefix}_roc.png", dpi=200)
    plt.close()

    plt.figure(figsize=(6, 5))
    plt.plot(rec, prec, label=f"AP={average_precision_score(y_true, y_score):.3f}")
    base = np.mean(y_true)
    plt.hlines(base, 0, 1, linestyles="--", colors="gray", lw=1, label=f"Base rate={base:.3f}")
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title(f"Precision–Recall curve ({prefix})")
    plt.legend(loc="lower left")
    plt.tight_layout()
    plt.savefig(f"report/images/{prefix}_pr.png", dpi=200)
    plt.close()


def plot_score_distributions(y_true, y_score, prefix: str):
    df = pd.DataFrame({"y": y_true, "score": y_score})
    plt.figure(figsize=(7, 4.5))
    sns.kdeplot(data=df, x="score", hue="y", common_norm=False, fill=True, alpha=0.35)
    plt.xlabel("Predicted P(variable)")
    plt.title(f"Score distributions by class ({prefix})")
    plt.tight_layout()
    plt.savefig(f"report/images/{prefix}_score_kde.png", dpi=200)
    plt.close()


def plot_calibration(y_true, y_score, prefix: str):
    prob_true, prob_pred = calibration_curve(y_true, y_score, n_bins=10, strategy="quantile")
    plt.figure(figsize=(5.5, 5))
    plt.plot(prob_pred, prob_true, marker="o")
    plt.plot([0, 1], [0, 1], "--", color="gray", lw=1)
    plt.xlabel("Mean predicted probability")
    plt.ylabel("Empirical frequency")
    plt.title(f"Calibration (quantile bins, {prefix})")
    plt.tight_layout()
    plt.savefig(f"report/images/{prefix}_calibration.png", dpi=200)
    plt.close()


def plot_confusion(y_true, y_score, prefix: str, threshold=0.5):
    y_pred = (y_score >= threshold).astype(int)
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(4.5, 4))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=False)
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.title(f"Confusion matrix (thr={threshold:.2f}, {prefix})")
    plt.tight_layout()
    plt.savefig(f"report/images/{prefix}_confusion.png", dpi=200)
    plt.close()


def main():
    ensure_dirs()

    train_df = pd.read_csv("data/train.csv")
    target_col = infer_target_column(train_df)
    feature_cols = infer_symbol_series_columns(train_df, target_col)

    # Determine whether we treat features as text (any object/string) or numeric
    X_train = train_df.drop(columns=[target_col])
    is_text = X_train[feature_cols].select_dtypes(include=["object", "string"]).shape[1] > 0

    splits = {
        "train": load_split("data/train.csv", target_col),
        "val": load_split("data/val.csv", target_col),
        "test": load_split("data/test.csv", target_col),
    }
    for k in splits:
        splits[k].y = coerce_binary_y(splits[k].y)

    meta = {
        "target_col": target_col,
        "feature_cols": feature_cols,
        "n_feature_cols": len(feature_cols),
        "is_text": bool(is_text),
        "train_shape": list(train_df.shape),
        "class_balance_train": {
            "n": int(len(splits["train"].y)),
            "positives": int(np.sum(splits["train"].y)),
            "positive_rate": float(np.mean(splits["train"].y)),
        },
    }
    Path("outputs/meta.json").write_text(json.dumps(meta, indent=2))

    if not is_text:
        # Numeric fallback: logistic regression on numeric features
        from sklearn.impute import SimpleImputer
        from sklearn.preprocessing import StandardScaler

        num_cols = feature_cols
        from sklearn.compose import ColumnTransformer

        pre = ColumnTransformer(
            [("num", Pipeline([("imp", SimpleImputer()), ("sc", StandardScaler())]), num_cols)],
            remainder="drop",
        )
        model = Pipeline(
            steps=[
                ("pre", pre),
                (
                    "clf",
                    LogisticRegression(
                        solver="lbfgs",
                        max_iter=2000,
                        class_weight="balanced",
                        random_state=RANDOM_STATE,
                    ),
                ),
            ]
        )
        model.fit(splits["train"].X, splits["train"].y)
        val_score = model.predict_proba(splits["val"].X)[:, 1]
        test_score = model.predict_proba(splits["test"].X)[:, 1]
        best = {"model": "numeric_logreg", "params": {}, "val_metrics": evaluate(splits["val"].y, val_score)}
    else:
        # Hyperparameter search on validation
        grid = []
        for ngram_range in [(2, 4), (3, 5), (4, 6)]:
            for C in [0.5, 1.0, 2.0, 4.0, 8.0]:
                for min_df in [1, 2, 5]:
                    grid.append((ngram_range, min_df, C))

        results = []
        best = None
        best_key = (-np.inf, -np.inf)

        for ngram_range, min_df, C in grid:
            model = make_model(feature_cols, ngram_range=ngram_range, min_df=min_df, C=C)
            model.fit(splits["train"].X, splits["train"].y)
            val_score = model.predict_proba(splits["val"].X)[:, 1]
            m = evaluate(splits["val"].y, val_score)
            rec = {
                "ngram_range": ngram_range,
                "min_df": min_df,
                "C": C,
                **{f"val_{k}": v for k, v in m.items()},
            }
            results.append(rec)
            # selection metric: ROC-AUC primarily, AP as tiebreak
            key = (m["roc_auc"], m["average_precision"])
            if key > best_key:
                best_key = key
                best = {
                    "model": "tfidf_char_logreg",
                    "params": {"ngram_range": ngram_range, "min_df": min_df, "C": C},
                    "val_metrics": m,
                }

        pd.DataFrame(results).sort_values(["val_roc_auc", "val_average_precision"], ascending=False).to_csv(
            "outputs/val_grid_results.csv", index=False
        )

        # Retrain on train+val with best params
        trainval_X = pd.concat([splits["train"].X, splits["val"].X], axis=0)
        trainval_y = np.concatenate([splits["train"].y, splits["val"].y])
        model = make_model(feature_cols, **best["params"])
        model.fit(trainval_X, trainval_y)

        val_score = model.predict_proba(splits["val"].X)[:, 1]
        test_score = model.predict_proba(splits["test"].X)[:, 1]

    # Save predictions
    out_val = pd.DataFrame({"y_true": splits["val"].y, "y_score": val_score})
    out_test = pd.DataFrame({"y_true": splits["test"].y, "y_score": test_score})
    out_val.to_csv("outputs/val_predictions.csv", index=False)
    out_test.to_csv("outputs/test_predictions.csv", index=False)

    best["test_metrics"] = evaluate(splits["test"].y, test_score)
    Path("outputs/metrics.json").write_text(json.dumps(best, indent=2))

    # If text model: extract most informative n-grams from trained train+val model
    if is_text:
        try:
            vec = model.named_steps["tfidf"]
            clf = model.named_steps["clf"]
            feat_names = np.array(vec.get_feature_names_out())
            coefs = clf.coef_.ravel()
            top_pos = np.argsort(coefs)[-25:][::-1]
            top_neg = np.argsort(coefs)[:25]
            rows = []
            for idx in top_pos:
                rows.append({"ngram": feat_names[idx], "coef": float(coefs[idx]), "direction": "variable"})
            for idx in top_neg:
                rows.append({"ngram": feat_names[idx], "coef": float(coefs[idx]), "direction": "non_variable"})
            top_df = pd.DataFrame(rows).sort_values("coef", ascending=False)
            top_df.to_csv("outputs/top_ngrams.csv", index=False)

            # plot
            show = pd.concat(
                [
                    top_df[top_df["direction"] == "variable"].head(15),
                    top_df[top_df["direction"] == "non_variable"].tail(15),
                ],
                axis=0,
            )
            show = show.copy()
            show["signed"] = show["coef"]
            show = show.sort_values("signed")
            plt.figure(figsize=(8, 6))
            sns.barplot(data=show, y="ngram", x="signed", hue="direction", dodge=False)
            plt.axvline(0, color="black", lw=1)
            plt.xlabel("Logistic regression coefficient")
            plt.ylabel("Character n-gram")
            plt.title("Most informative character n-grams (train+val)")
            plt.tight_layout()
            plt.savefig("report/images/top_ngrams.png", dpi=200)
            plt.close()
        except Exception as e:
            Path("outputs/top_ngrams_error.txt").write_text(str(e))

    # Figures
    plot_roc_pr(splits["val"].y, val_score, prefix="val")
    plot_score_distributions(splits["val"].y, val_score, prefix="val")
    plot_calibration(splits["val"].y, val_score, prefix="val")
    plot_confusion(splits["val"].y, val_score, prefix="val", threshold=0.5)

    plot_roc_pr(splits["test"].y, test_score, prefix="test")
    plot_score_distributions(splits["test"].y, test_score, prefix="test")
    plot_calibration(splits["test"].y, test_score, prefix="test")
    plot_confusion(splits["test"].y, test_score, prefix="test", threshold=0.5)

    # Extra: distribution of sequence lengths (if text)
    if is_text:
        # approximate length by joining columns
        joiner = JoinTextColumns(cols=feature_cols)
        train_text = joiner.transform(splits["train"].X)
        val_text = joiner.transform(splits["val"].X)
        test_text = joiner.transform(splits["test"].X)
        lens = pd.DataFrame(
            {
                "split": np.repeat(["train", "val", "test"], [len(train_text), len(val_text), len(test_text)]),
                "length": np.concatenate([pd.Series(train_text).str.len().to_numpy(), pd.Series(val_text).str.len().to_numpy(), pd.Series(test_text).str.len().to_numpy()]),
            }
        )
        plt.figure(figsize=(7, 4.5))
        sns.histplot(data=lens, x="length", hue="split", bins=60, element="step", stat="density", common_norm=False)
        plt.xlim(0, np.nanpercentile(lens["length"], 99))
        plt.title("Symbol-series length distribution")
        plt.tight_layout()
        plt.savefig("report/images/symbol_series_length.png", dpi=200)
        plt.close()


if __name__ == "__main__":
    main()
