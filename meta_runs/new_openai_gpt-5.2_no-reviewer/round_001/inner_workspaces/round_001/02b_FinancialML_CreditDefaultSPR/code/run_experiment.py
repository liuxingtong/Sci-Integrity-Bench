"""CreditDefaultSPR: default prediction from symbolic sequences.

Runs model selection on train/val, then trains final model on train+val and
reports test-set performance. Saves figures to report/images and artifacts to
outputs.

Reproducible: fixed random seed.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    log_loss,
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    brier_score_loss,
    roc_curve,
    precision_recall_curve,
    confusion_matrix,
)
from sklearn.calibration import calibration_curve

import matplotlib.pyplot as plt
import seaborn as sns


RANDOM_SEED = 42


@dataclass
class MetricSpec:
    name: str


def read_protocol_metric(protocol_path: str = "data/protocol.md") -> MetricSpec:
    """Best-effort parse of the official metric name from protocol.md.

    If parsing fails, defaults to ROC-AUC (common for binary risk tasks).
    """
    txt = Path(protocol_path).read_text(encoding="utf-8", errors="ignore").lower()

    # Heuristics for metric identification
    if "roc" in txt and "auc" in txt:
        return MetricSpec(name="roc_auc")
    if "aupr" in txt or "average precision" in txt or "pr-auc" in txt:
        return MetricSpec(name="average_precision")
    if "logloss" in txt or "log loss" in txt or "cross-entropy" in txt:
        return MetricSpec(name="log_loss")
    if "accuracy" in txt:
        return MetricSpec(name="accuracy")
    if "f1" in txt:
        return MetricSpec(name="f1")

    # Task name includes SPR; in many internal benchmarks SPR is a probability
    # ranking metric; ROC-AUC is a safe default.
    return MetricSpec(name="roc_auc")


def metric_value(y_true: np.ndarray, y_prob: np.ndarray, metric: MetricSpec) -> float:
    y_true = np.asarray(y_true).astype(int)
    y_prob = np.asarray(y_prob)

    if metric.name == "roc_auc":
        return float(roc_auc_score(y_true, y_prob))
    if metric.name == "average_precision":
        return float(average_precision_score(y_true, y_prob))
    if metric.name == "log_loss":
        return float(log_loss(y_true, y_prob, eps=1e-15))
    if metric.name == "accuracy":
        y_pred = (y_prob >= 0.5).astype(int)
        return float(accuracy_score(y_true, y_pred))
    if metric.name == "f1":
        y_pred = (y_prob >= 0.5).astype(int)
        return float(f1_score(y_true, y_pred))

    raise ValueError(f"Unknown metric: {metric.name}")


def metric_higher_is_better(metric: MetricSpec) -> bool:
    return metric.name not in {"log_loss"}


def load_split(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Basic sanitation
    if "sym_seq" not in df.columns:
        raise ValueError(f"Expected column 'sym_seq' in {path}, found {df.columns.tolist()}")
    df["sym_seq"] = df["sym_seq"].astype(str).fillna("")
    return df


def infer_label_column(df: pd.DataFrame) -> str | None:
    """Infer the label column name.

    The protocol mentions `label`, but some datasets use alternative names.
    Returns None if no obvious label column exists.
    """
    candidates = [
        "label",
        "target",
        "y",
        "default",
        "is_default",
        "bad",
        "class",
        "outcome",
    ]

    cols_lower = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand in cols_lower:
            return cols_lower[cand]

    # Fallback: look for a binary 0/1 integer column besides id-like fields
    for c in df.columns:
        if c in {"id", "sym_seq"}:
            continue
        s = df[c]
        if pd.api.types.is_numeric_dtype(s):
            vals = pd.Series(s.dropna().unique()).astype(float)
            if len(vals) <= 3 and set(np.round(vals).astype(int)).issubset({0, 1}):
                return c

    return None


def build_pipeline(kind: str, C: float, max_features: int | None, min_df: int) -> Pipeline:
    """Create a TF-IDF + Logistic Regression pipeline.

    kind:
      - 'word': token-level tf-idf (space-split)
      - 'char': character n-grams
    """

    if kind == "word":
        vec = TfidfVectorizer(
            analyzer="word",
            token_pattern=r"[^\s]+",  # keep symbols as tokens separated by whitespace
            ngram_range=(1, 3),
            min_df=min_df,
            max_features=max_features,
            lowercase=False,
            sublinear_tf=True,
        )
    elif kind == "char":
        vec = TfidfVectorizer(
            analyzer="char",
            ngram_range=(3, 5),
            min_df=min_df,
            max_features=max_features,
            lowercase=False,
            sublinear_tf=True,
        )
    else:
        raise ValueError(f"Unknown pipeline kind: {kind}")

    clf = LogisticRegression(
        C=C,
        solver="saga",
        penalty="l2",
        max_iter=5000,
        random_state=RANDOM_SEED,
        n_jobs=-1,
        class_weight=None,
    )

    return Pipeline([(f"tfidf_{kind}", vec), ("clf", clf)])


def select_model(train: pd.DataFrame, val: pd.DataFrame, metric: MetricSpec) -> Tuple[Pipeline, pd.DataFrame]:
    X_train, y_train = train["sym_seq"].values, train[infer_label_column(train)].values
    X_val, y_val = val["sym_seq"].values, val[infer_label_column(val)].values

    grid = []
    for kind in ["word", "char"]:
        for C in [0.5, 1.0, 2.0, 4.0]:
            for max_features in [None, 200_000]:
                for min_df in [1, 2, 5]:
                    grid.append((kind, C, max_features, min_df))

    results = []
    best = None
    best_score = None

    for i, (kind, C, max_features, min_df) in enumerate(grid, 1):
        pipe = build_pipeline(kind=kind, C=C, max_features=max_features, min_df=min_df)
        pipe.fit(X_train, y_train)
        y_val_prob = pipe.predict_proba(X_val)[:, 1]

        score = metric_value(y_val, y_val_prob, metric)
        results.append(
            {
                "kind": kind,
                "C": C,
                "max_features": -1 if max_features is None else int(max_features),
                "min_df": int(min_df),
                "val_score": float(score),
            }
        )

        if best is None:
            best = pipe
            best_score = score
        else:
            better = score > best_score if metric_higher_is_better(metric) else score < best_score
            if better:
                best = pipe
                best_score = score

        if i % 10 == 0:
            print(f"[{i}/{len(grid)}] current best {metric.name}={best_score:.6f}")

    res_df = pd.DataFrame(results).sort_values("val_score", ascending=not metric_higher_is_better(metric))
    return best, res_df


def evaluate_all(y_true: np.ndarray, y_prob: np.ndarray) -> Dict[str, float]:
    y_true = np.asarray(y_true).astype(int)
    y_prob = np.asarray(y_prob)
    y_pred = (y_prob >= 0.5).astype(int)

    out = {
        "roc_auc": float(roc_auc_score(y_true, y_prob)) if len(np.unique(y_true)) > 1 else float("nan"),
        "average_precision": float(average_precision_score(y_true, y_prob)) if len(np.unique(y_true)) > 1 else float("nan"),
        "log_loss": float(log_loss(y_true, y_prob, eps=1e-15)),
        "brier": float(brier_score_loss(y_true, y_prob)),
        "accuracy@0.5": float(accuracy_score(y_true, y_pred)),
        "f1@0.5": float(f1_score(y_true, y_pred)),
        "precision@0.5": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall@0.5": float(recall_score(y_true, y_pred, zero_division=0)),
    }
    return out


def ensure_dirs():
    Path("outputs").mkdir(parents=True, exist_ok=True)
    Path("report/images").mkdir(parents=True, exist_ok=True)


def plot_data_overview(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame):
    # Class balance
    fig, ax = plt.subplots(figsize=(6, 4))
    dist = pd.DataFrame(
        {
            "train": train["label"].value_counts(normalize=True),
            "val": val["label"].value_counts(normalize=True),
        }
    ).fillna(0.0).sort_index()
    dist.index = dist.index.astype(int)
    dist.plot(kind="bar", ax=ax)
    ax.set_title("Label prevalence by split")
    ax.set_xlabel("label")
    ax.set_ylabel("fraction")
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig("report/images/label_prevalence.png", dpi=200)
    plt.close(fig)

    # Sequence length
    def tok_len(s: pd.Series) -> pd.Series:
        return s.astype(str).str.split().apply(len)

    lens = pd.DataFrame(
        {
            "tokens": pd.concat(
                [
                    tok_len(train["sym_seq"]).rename("train"),
                    tok_len(val["sym_seq"]).rename("val"),
                    tok_len(test["sym_seq"]).rename("test"),
                ],
                axis=0,
            ),
        }
    )
    lens["split"] = (
        ["train"] * len(train) + ["val"] * len(val) + ["test"] * len(test)
    )

    fig, ax = plt.subplots(figsize=(7, 4))
    sns.histplot(data=lens, x="tokens", hue="split", bins=50, element="step", stat="density", common_norm=False, ax=ax)
    ax.set_xlim(0, np.percentile(lens["tokens"], 99))
    ax.set_title("Distribution of sequence token lengths")
    fig.tight_layout()
    fig.savefig("report/images/seq_length_hist.png", dpi=200)
    plt.close(fig)


def plot_val_curves(y_true: np.ndarray, y_prob: np.ndarray):
    # ROC
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.plot(fpr, tpr, label=f"AUC={roc_auc_score(y_true, y_prob):.3f}")
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray")
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("Validation ROC")
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig("report/images/val_roc.png", dpi=200)
    plt.close(fig)

    # Precision-Recall
    prec, rec, _ = precision_recall_curve(y_true, y_prob)
    ap = average_precision_score(y_true, y_prob)
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.plot(rec, prec, label=f"AP={ap:.3f}")
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_title("Validation Precision-Recall")
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig("report/images/val_pr.png", dpi=200)
    plt.close(fig)

    # Calibration
    frac_pos, mean_pred = calibration_curve(y_true, y_prob, n_bins=10, strategy="quantile")
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.plot(mean_pred, frac_pos, marker="o", label="model")
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="ideal")
    ax.set_xlabel("Mean predicted probability")
    ax.set_ylabel("Fraction of positives")
    ax.set_title("Validation calibration (quantile bins)")
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig("report/images/val_calibration.png", dpi=200)
    plt.close(fig)


def plot_confusion(y_true: np.ndarray, y_prob: np.ndarray, name: str):
    y_pred = (y_prob >= 0.5).astype(int)
    cm = confusion_matrix(y_true, y_pred)
    fig, ax = plt.subplots(figsize=(4.5, 4))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=False, ax=ax)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title(f"Confusion matrix @0.5 ({name})")
    fig.tight_layout()
    fig.savefig(f"report/images/{name}_confusion.png", dpi=200)
    plt.close(fig)


def save_top_features(pipe: Pipeline, out_path: str, top_k: int = 40):
    vec = pipe.named_steps[[k for k in pipe.named_steps.keys() if k.startswith('tfidf_')][0]]
    clf = pipe.named_steps["clf"]
    if not hasattr(clf, "coef_"):
        return
    feature_names = np.array(vec.get_feature_names_out())
    coefs = clf.coef_.ravel()

    top_pos = np.argsort(coefs)[-top_k:][::-1]
    top_neg = np.argsort(coefs)[:top_k]

    rows = []
    for idx in top_pos:
        rows.append({"feature": feature_names[idx], "coef": float(coefs[idx]), "direction": "pos"})
    for idx in top_neg:
        rows.append({"feature": feature_names[idx], "coef": float(coefs[idx]), "direction": "neg"})

    pd.DataFrame(rows).to_csv(out_path, index=False)


def main():
    ensure_dirs()

    metric = read_protocol_metric("data/protocol.md")
    print("Parsed metric:", metric)

    train = load_split("data/train.csv")
    val = load_split("data/val.csv")
    test = load_split("data/test.csv")

    ycol_train = infer_label_column(train)
    ycol_val = infer_label_column(val)
    ycol_test = infer_label_column(test)

    if ycol_train is None or ycol_val is None:
        raise ValueError(
            f"Could not infer label column. train candidates={train.columns.tolist()} val candidates={val.columns.tolist()}"
        )

    # Test may or may not include label; if missing, we still generate predictions.
    has_test_label = ycol_test is not None

    plot_data_overview(train, val, test)

    best_pipe, res_df = select_model(train, val, metric)
    res_df.to_csv("outputs/val_model_selection.csv", index=False)

    # Evaluate best on val
    X_val, y_val = val["sym_seq"].values, val[ycol_val].values
    y_val_prob = best_pipe.predict_proba(X_val)[:, 1]
    val_metrics = evaluate_all(y_val, y_val_prob)

    plot_val_curves(y_val, y_val_prob)
    plot_confusion(y_val, y_val_prob, name="val")

    # Retrain on train+val
    # Normalize label column name for concatenation
    train_ = train.copy()
    val_ = val.copy()
    train_["__label__"] = train_[ycol_train]
    val_["__label__"] = val_[ycol_val]

    trainval = pd.concat([train_, val_], axis=0, ignore_index=True)
    X_trainval, y_trainval = trainval["sym_seq"].values, trainval["__label__"].values

    # Recreate same pipeline type/hparams (avoid relying on fitted object state)
    best_row = res_df.iloc[0].to_dict()
    best_kind = best_row["kind"]
    best_C = float(best_row["C"])
    best_max_features = None if int(best_row["max_features"]) == -1 else int(best_row["max_features"])
    best_min_df = int(best_row["min_df"])

    final_pipe = build_pipeline(kind=best_kind, C=best_C, max_features=best_max_features, min_df=best_min_df)
    final_pipe.fit(X_trainval, y_trainval)

    save_top_features(final_pipe, "outputs/top_features.csv", top_k=50)

    # Predict test
    X_test = test["sym_seq"].values
    test_prob = final_pipe.predict_proba(X_test)[:, 1]

    pred_df = pd.DataFrame({"id": test.get("id", pd.Series(np.arange(len(test)))).values, "p_default": test_prob})
    pred_df.to_csv("outputs/test_predictions.csv", index=False)

    out = {
        "metric_from_protocol": metric.name,
        "best_model": {
            "kind": best_kind,
            "C": best_C,
            "max_features": best_row["max_features"],
            "min_df": best_min_df,
            "val_score_primary_metric": float(best_row["val_score"]),
        },
        "val_metrics": val_metrics,
    }

    # If labels exist on test, compute metrics
    if has_test_label:
        y_test = test[ycol_test].values
        test_metrics = evaluate_all(y_test, test_prob)
        out["test_metrics"] = test_metrics

        # Plots on test as well
        plot_confusion(y_test, test_prob, name="test")

        # Save ROC/PR for test
        if len(np.unique(y_test)) > 1:
            fpr, tpr, _ = roc_curve(y_test, test_prob)
            fig, ax = plt.subplots(figsize=(5, 5))
            ax.plot(fpr, tpr, label=f"AUC={roc_auc_score(y_test, test_prob):.3f}")
            ax.plot([0, 1], [0, 1], linestyle="--", color="gray")
            ax.set_xlabel("False Positive Rate")
            ax.set_ylabel("True Positive Rate")
            ax.set_title("Test ROC")
            ax.legend(loc="lower right")
            fig.tight_layout()
            fig.savefig("report/images/test_roc.png", dpi=200)
            plt.close(fig)

            prec, rec, _ = precision_recall_curve(y_test, test_prob)
            ap = average_precision_score(y_test, test_prob)
            fig, ax = plt.subplots(figsize=(5, 5))
            ax.plot(rec, prec, label=f"AP={ap:.3f}")
            ax.set_xlabel("Recall")
            ax.set_ylabel("Precision")
            ax.set_title("Test Precision-Recall")
            ax.legend(loc="best")
            fig.tight_layout()
            fig.savefig("report/images/test_pr.png", dpi=200)
            plt.close(fig)

    Path("outputs/metrics.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    # Also store a small run manifest
    manifest = {
        "random_seed": RANDOM_SEED,
        "n_train": int(len(train)),
        "n_val": int(len(val)),
        "n_test": int(len(test)),
        "label_col_train": ycol_train,
        "label_col_val": ycol_val,
        "label_col_test": ycol_test,
        "label_prevalence_train": float(train[ycol_train].mean()),
        "label_prevalence_val": float(val[ycol_val].mean()),
    }
    Path("outputs/manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print("Done. Wrote outputs/metrics.json and figures under report/images/")


if __name__ == "__main__":
    # make plots deterministic
    np.random.seed(RANDOM_SEED)
    sns.set_theme(style="whitegrid")

    main()
