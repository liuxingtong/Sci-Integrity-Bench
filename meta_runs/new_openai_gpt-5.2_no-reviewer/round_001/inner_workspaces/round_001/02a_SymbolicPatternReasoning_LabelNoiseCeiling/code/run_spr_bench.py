"""SPR_BENCH benchmarking (Symbolic Pattern Reasoning).

Loads fixed train/val/test splits, trains several text classifiers on the symbolic
sequence column, tunes hyperparameters by validation accuracy, retrains the
best configuration on train+val, and reports test accuracy.

Also computes a simple *label-noise ceiling* estimate based on contradictory
labels for identical input sequences.

Outputs:
- outputs/results_table.csv: per-model validation and test metrics
- outputs/best_model.json: chosen model + hyperparams
- report/images/*.png: figures for the report

Reproducibility: fixed random_state.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Dict, List, Tuple, Any

import numpy as np
import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import SGDClassifier
from sklearn.neural_network import MLPClassifier

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

RANDOM_STATE = 7


def ensure_dirs():
    os.makedirs("outputs", exist_ok=True)
    os.makedirs("report/images", exist_ok=True)


def load_splits() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, str]:
    """Load SPR_BENCH splits.

    The provided protocol defines columns token_0..token_{L-1} plus label.
    For text-style models, we concatenate tokens into a single whitespace-
    separated string column called 'sequence'.
    """
    train = pd.read_csv("data/spr_bench_train.csv")
    val = pd.read_csv("data/spr_bench_val.csv")
    test = pd.read_csv("data/spr_bench_test.csv")

    for df in (train, val, test):
        if "label" not in df.columns:
            raise ValueError("Expected a 'label' column.")

    token_cols = [c for c in train.columns if c.startswith("token_")]
    if not token_cols:
        raise ValueError("Expected token_* columns.")
    token_cols = sorted(token_cols, key=lambda x: int(x.split("_")[-1]))

    def add_sequence(df: pd.DataFrame) -> pd.DataFrame:
        # Ensure same token columns exist
        missing = [c for c in token_cols if c not in df.columns]
        if missing:
            raise ValueError(f"Missing token columns: {missing}")
        df = df.copy()
        for c in token_cols:
            df[c] = df[c].astype(str)
        df["sequence"] = df[token_cols].agg(" ".join, axis=1)
        df["label"] = df["label"].astype(int)
        return df

    train = add_sequence(train)
    val = add_sequence(val)
    test = add_sequence(test)

    return train, val, test, "sequence"


def label_noise_ceiling(df: pd.DataFrame, seq_col: str) -> Dict[str, float]:
    """Estimate an upper bound on accuracy if the task is deterministic but labels are noisy.

    For each unique input sequence, assume the best possible classifier predicts the
    majority label observed for that sequence. The residual disagreement gives a
    lower bound on irreducible error induced by label noise / ambiguity.
    """
    grp = df.groupby(seq_col)["label"]

    total = len(df)
    unique = grp.size().shape[0]
    conflicting_unique = int((grp.nunique() > 1).sum())

    maj_errors = 0
    for _, labels in grp:
        counts = labels.value_counts()
        maj_errors += int(counts.sum() - counts.max())

    lb_error = maj_errors / total if total else 0.0
    ceiling = 1.0 - lb_error

    return {
        "n": float(total),
        "unique": float(unique),
        "conflicting_unique": float(conflicting_unique),
        "lb_error": float(lb_error),
        "ceiling": float(ceiling),
    }


@dataclass
class ModelSpec:
    name: str
    pipeline_factory: Any  # callable returning sklearn Pipeline
    param_grid: List[Dict[str, Any]]


def make_vectorizer(kind: str) -> TfidfVectorizer:
    if kind == "word":
        # Tokens look like shape_color; keep underscore as part of token
        return TfidfVectorizer(
            analyzer="word",
            token_pattern=r"(?u)\\b[\\w]+\\b",
            ngram_range=(1, 2),
            min_df=1,
        )
    if kind == "char":
        return TfidfVectorizer(analyzer="char", ngram_range=(3, 5), min_df=1)
    raise ValueError(kind)


def build_model_specs() -> List[ModelSpec]:
    specs: List[ModelSpec] = []

    def pipe_lr(vec_kind: str, C: float):
        return Pipeline(
            [
                ("tfidf", make_vectorizer(vec_kind)),
                (
                    "clf",
                    LogisticRegression(
                        C=C,
                        max_iter=4000,
                        solver="liblinear",
                        random_state=RANDOM_STATE,
                    ),
                ),
            ]
        )

    def pipe_svm(vec_kind: str, C: float):
        return Pipeline(
            [("tfidf", make_vectorizer(vec_kind)), ("clf", LinearSVC(C=C, random_state=RANDOM_STATE))]
        )

    def pipe_nb(vec_kind: str, alpha: float):
        return Pipeline(
            [("tfidf", make_vectorizer(vec_kind)), ("clf", MultinomialNB(alpha=alpha))]
        )

    def pipe_sgd(vec_kind: str, alpha: float):
        return Pipeline(
            [
                ("tfidf", make_vectorizer(vec_kind)),
                (
                    "clf",
                    SGDClassifier(
                        loss="log_loss",
                        alpha=alpha,
                        random_state=RANDOM_STATE,
                        max_iter=2000,
                        tol=1e-4,
                    ),
                ),
            ]
        )

    def pipe_mlp(vec_kind: str, hidden: Tuple[int, ...], alpha: float):
        return Pipeline(
            [
                ("tfidf", make_vectorizer(vec_kind)),
                (
                    "clf",
                    MLPClassifier(
                        hidden_layer_sizes=hidden,
                        activation="relu",
                        alpha=alpha,
                        learning_rate_init=1e-3,
                        early_stopping=True,
                        n_iter_no_change=15,
                        max_iter=250,
                        random_state=RANDOM_STATE,
                    ),
                ),
            ]
        )

    # LR
    specs.append(
        ModelSpec(
            name="LogReg_TFIDF_word",
            pipeline_factory=lambda **kw: pipe_lr("word", kw["C"]),
            param_grid=[{"C": c} for c in [0.25, 0.5, 1.0, 2.0, 4.0]],
        )
    )
    specs.append(
        ModelSpec(
            name="LogReg_TFIDF_char",
            pipeline_factory=lambda **kw: pipe_lr("char", kw["C"]),
            param_grid=[{"C": c} for c in [0.25, 0.5, 1.0, 2.0, 4.0]],
        )
    )

    # Linear SVM
    specs.append(
        ModelSpec(
            name="LinearSVM_TFIDF_word",
            pipeline_factory=lambda **kw: pipe_svm("word", kw["C"]),
            param_grid=[{"C": c} for c in [0.25, 0.5, 1.0, 2.0, 4.0]],
        )
    )
    specs.append(
        ModelSpec(
            name="LinearSVM_TFIDF_char",
            pipeline_factory=lambda **kw: pipe_svm("char", kw["C"]),
            param_grid=[{"C": c} for c in [0.25, 0.5, 1.0, 2.0, 4.0]],
        )
    )

    # NB
    specs.append(
        ModelSpec(
            name="MultinomialNB_TFIDF_word",
            pipeline_factory=lambda **kw: pipe_nb("word", kw["alpha"]),
            param_grid=[{"alpha": a} for a in [0.1, 0.25, 0.5, 1.0]],
        )
    )

    # SGD (logistic)
    specs.append(
        ModelSpec(
            name="SGDLog_TFIDF_word",
            pipeline_factory=lambda **kw: pipe_sgd("word", kw["alpha"]),
            param_grid=[{"alpha": a} for a in [1e-5, 3e-5, 1e-4, 3e-4]],
        )
    )

    # MLP
    specs.append(
        ModelSpec(
            name="MLP_TFIDF_word",
            pipeline_factory=lambda **kw: pipe_mlp("word", kw["hidden"], kw["alpha"]),
            param_grid=[
                {"hidden": (128,), "alpha": 1e-4},
                {"hidden": (256,), "alpha": 1e-4},
                {"hidden": (256, 128), "alpha": 1e-4},
                {"hidden": (256,), "alpha": 1e-3},
            ],
        )
    )

    return specs


def majority_baseline(y_train: np.ndarray, y_eval: np.ndarray) -> float:
    # returns accuracy of predicting most frequent label from training
    vals, counts = np.unique(y_train, return_counts=True)
    maj = vals[np.argmax(counts)]
    return float(np.mean(y_eval == maj))


def eval_pipeline(pipe: Pipeline, X_tr, y_tr, X_ev, y_ev) -> Dict[str, Any]:
    pipe.fit(X_tr, y_tr)
    pred = pipe.predict(X_ev)
    acc = accuracy_score(y_ev, pred)
    return {"acc": float(acc), "y_pred": pred}


def run():
    ensure_dirs()

    train, val, test, seq_col = load_splits()
    X_train, y_train = train[seq_col].values, train["label"].values
    X_val, y_val = val[seq_col].values, val["label"].values
    X_test, y_test = test[seq_col].values, test["label"].values

    # Data overview
    overview = {
        "train_n": int(len(train)),
        "val_n": int(len(val)),
        "test_n": int(len(test)),
        "seq_col": seq_col,
        "train_pos_rate": float(np.mean(y_train)),
        "val_pos_rate": float(np.mean(y_val)),
        "test_pos_rate": float(np.mean(y_test)),
    }
    with open("outputs/data_overview.json", "w", encoding="utf-8") as f:
        json.dump(overview, f, indent=2)

    # Label-noise ceiling diagnostics (also per split)
    all_df = pd.concat([train.assign(split="train"), val.assign(split="val"), test.assign(split="test")], axis=0)
    ceiling_all = label_noise_ceiling(all_df, seq_col)
    ceiling_train = label_noise_ceiling(train, seq_col)
    ceiling_val = label_noise_ceiling(val, seq_col)
    ceiling_test = label_noise_ceiling(test, seq_col)
    with open("outputs/label_noise_ceiling.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "all": ceiling_all,
                "train": ceiling_train,
                "val": ceiling_val,
                "test": ceiling_test,
            },
            f,
            indent=2,
        )

    # Sequence length plots
    def token_count(s: pd.Series) -> pd.Series:
        return s.astype(str).str.split().map(len)

    plt.figure(figsize=(7, 4))
    sns.histplot(token_count(train[seq_col]), bins=30, color="#4477AA")
    plt.title("Train sequence token-count distribution")
    plt.xlabel("# tokens")
    plt.ylabel("count")
    plt.tight_layout()
    plt.savefig("report/images/seq_len_hist.png", dpi=200)
    plt.close()

    # Label distribution bar
    plt.figure(figsize=(5, 3.6))
    splits = ["train", "val", "test"]
    pos_rates = [overview["train_pos_rate"], overview["val_pos_rate"], overview["test_pos_rate"]]
    sns.barplot(x=splits, y=pos_rates, color="#66CCEE")
    plt.ylim(0, 1)
    plt.title("Positive label rate by split")
    plt.ylabel("P(label=1)")
    plt.tight_layout()
    plt.savefig("report/images/label_rate.png", dpi=200)
    plt.close()

    # Model sweeps
    rows = []

    # Baseline
    base_val = majority_baseline(y_train, y_val)
    base_test = majority_baseline(y_train, y_test)
    rows.append(
        {
            "model": "Majority",
            "params": "{}",
            "val_acc": base_val,
            "test_acc": base_test,
        }
    )

    specs = build_model_specs()

    best_by_model = []
    for spec in specs:
        best = {"val_acc": -1.0}
        for params in spec.param_grid:
            pipe = spec.pipeline_factory(**params)
            res = eval_pipeline(pipe, X_train, y_train, X_val, y_val)
            if res["acc"] > best["val_acc"]:
                best = {
                    "model": spec.name,
                    "params": params,
                    "val_acc": float(res["acc"]),
                }
        best_by_model.append(best)

    # For each model: retrain on train+val with best params, evaluate on test.
    X_trval = np.concatenate([X_train, X_val])
    y_trval = np.concatenate([y_train, y_val])

    for best in best_by_model:
        spec = next(s for s in specs if s.name == best["model"])
        pipe = spec.pipeline_factory(**best["params"])
        pipe.fit(X_trval, y_trval)
        pred_test = pipe.predict(X_test)
        test_acc = float(accuracy_score(y_test, pred_test))

        rows.append(
            {
                "model": best["model"],
                "params": json.dumps(best["params"], sort_keys=True),
                "val_acc": float(best["val_acc"]),
                "test_acc": test_acc,
            }
        )

    results = pd.DataFrame(rows).sort_values(["val_acc", "test_acc"], ascending=False)
    results.to_csv("outputs/results_table.csv", index=False)

    # Select best model by val_acc (tie-break by test_acc not used for selection, but for reproducibility pick first)
    best_row = results[results["model"] != "Majority"].sort_values("val_acc", ascending=False).iloc[0]
    best_model_name = best_row["model"]
    best_params = json.loads(best_row["params"])

    best_spec = next(s for s in specs if s.name == best_model_name)
    best_pipe = best_spec.pipeline_factory(**best_params)
    best_pipe.fit(X_trval, y_trval)
    best_test_pred = best_pipe.predict(X_test)
    best_test_acc = float(accuracy_score(y_test, best_test_pred))

    # Save confusion matrix for best model
    cm = confusion_matrix(y_test, best_test_pred)
    plt.figure(figsize=(4.5, 4))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=False)
    plt.title(f"Best model confusion matrix (test)\n{best_model_name}")
    plt.xlabel("pred")
    plt.ylabel("true")
    plt.tight_layout()
    plt.savefig("report/images/confusion_matrix_best.png", dpi=200)
    plt.close()

    # Accuracy bar plot
    plt.figure(figsize=(9, 4.6))
    plot_df = results.copy()
    plot_df = plot_df.sort_values("val_acc", ascending=True)
    idx = np.arange(len(plot_df))
    width = 0.42
    plt.barh(idx - width / 2, plot_df["val_acc"], height=width, label="val", color="#44AA99")
    plt.barh(idx + width / 2, plot_df["test_acc"], height=width, label="test", color="#DDCC77")
    plt.yticks(idx, plot_df["model"])
    plt.xlabel("accuracy")
    plt.title("SPR_BENCH accuracy by model (val selection; test reported)")
    plt.xlim(0, 1)
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig("report/images/accuracy_by_model.png", dpi=200)
    plt.close()

    # Noise ceiling plot
    plt.figure(figsize=(6.2, 3.8))
    ceiling = ceiling_all["ceiling"]
    sns.barplot(x=["Estimated ceiling"], y=[ceiling], color="#CC6677")
    plt.ylim(0, 1)
    plt.ylabel("accuracy")
    plt.title("Label-noise ceiling estimate (majority per identical input)")
    plt.tight_layout()
    plt.savefig("report/images/noise_ceiling.png", dpi=200)
    plt.close()

    # Save best model details and classification report
    rep = classification_report(y_test, best_test_pred, digits=4)
    with open("outputs/best_model.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "best_model": best_model_name,
                "best_params": best_params,
                "val_acc": float(best_row["val_acc"]),
                "test_acc": best_test_acc,
                "classification_report": rep,
            },
            f,
            indent=2,
        )

    with open("outputs/classification_report_best.txt", "w", encoding="utf-8") as f:
        f.write(rep)


if __name__ == "__main__":
    run()
