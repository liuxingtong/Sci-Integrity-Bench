# -*- coding: utf-8 -*-
"""CreditDefaultSPR: default prediction from symbolic sequences.

Reproducible training/selection on train/val, final evaluation on test.
Saves:
- outputs/model_selection.csv
- outputs/test_predictions.csv
- outputs/results.json
- report/images/*.png

Run:
  python code/train_eval.py
"""

import json
import os
import re
from dataclasses import dataclass
from typing import Callable, Dict, List, Tuple

import numpy as np
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    log_loss,
    brier_score_loss,
    roc_curve,
    precision_recall_curve,
)
from sklearn.model_selection import ParameterGrid

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

RANDOM_STATE = 42


def infer_columns(df: pd.DataFrame) -> Tuple[str, str]:
    """Infer sequence column and label column."""
    seq_candidates = [c for c in df.columns if "seq" in c.lower() or "sym" in c.lower()]
    if not seq_candidates:
        # fallback: first object column
        obj_cols = [c for c in df.columns if df[c].dtype == object]
        if not obj_cols:
            raise ValueError("Could not infer sequence column")
        seq_col = obj_cols[0]
    else:
        seq_col = seq_candidates[0]

    label_candidates = [c for c in df.columns if c.lower() in {"label", "y", "target", "default"}]
    if label_candidates:
        label_col = label_candidates[0]
    else:
        # fallback: a non-object binary/int column
        non_seq = [c for c in df.columns if c != seq_col]
        # prefer columns with only {0,1}
        bin_cols = []
        for c in non_seq:
            if pd.api.types.is_numeric_dtype(df[c]):
                u = pd.unique(df[c].dropna())
                if len(u) <= 2 and set(map(int, u)) <= {0, 1}:
                    bin_cols.append(c)
        if bin_cols:
            label_col = bin_cols[0]
        else:
            # last resort: first non-seq column
            label_col = non_seq[0]

    return seq_col, label_col


def guess_tokenizer(seqs: pd.Series) -> Callable[[str], List[str]]:
    """Choose a reasonable tokenization strategy based on delimiters."""
    s = seqs.dropna().astype(str)
    # determine prevalent delimiter
    delims = [" ", "|", ",", ";", "\t"]
    rates = {d: float(s.str.contains(re.escape(d)).mean()) for d in delims}
    best = max(rates, key=rates.get)

    def tok_split(delim: str):
        def f(x: str) -> List[str]:
            if x is None or (isinstance(x, float) and np.isnan(x)):
                return []
            x = str(x).strip()
            if not x:
                return []
            # strip common wrappers
            if (x[0] == "[" and x[-1] == "]") or (x[0] == "(" and x[-1] == ")"):
                x = x[1:-1]
            parts = [p for p in x.split(delim) if p != ""]
            return parts
        return f

    # If no delimiter is common, attempt regex tokenization.
    if rates[best] < 0.2:
        token_re = re.compile(r"<[^>]+>|[A-Za-z]+\d+|[A-Za-z]+|\d+|[^\s]")

        def f(x: str) -> List[str]:
            if x is None or (isinstance(x, float) and np.isnan(x)):
                return []
            x = str(x).strip()
            if not x:
                return []
            if (x[0] == "[" and x[-1] == "]") or (x[0] == "(" and x[-1] == ")"):
                x = x[1:-1]
            toks = token_re.findall(x)
            return [t for t in toks if t and not t.isspace()]

        return f

    return tok_split(best)


# ---- Metrics ----

def metric_spr(y_true: np.ndarray, y_score: np.ndarray, k: int | None = None, frac: float | None = None) -> float:
    """Compute the SPR metric.

    The scenario name suggests SPR is a *selection* metric: sort examples by
    predicted risk and measure the default rate in a fixed-size "review" bucket.

    We support two common variants:
      - SPR@k: precision among the top-k highest-risk accounts.
      - SPR@frac: precision among the top ceil(frac * N) highest-risk accounts.

    If k and frac are both None, default to SPR@P where P is the number of
    positives in y_true (common in information retrieval: precision at R).

    Returns: higher is better.
    """
    y_true = np.asarray(y_true).astype(int)
    y_score = np.asarray(y_score)
    n = int(len(y_true))

    if frac is not None:
        k_eff = int(np.ceil(frac * n))
    elif k is not None:
        k_eff = int(k)
    else:
        k_eff = int(y_true.sum())

    k_eff = max(1, min(n, k_eff))
    idx = np.argsort(-y_score)
    top = y_true[idx[:k_eff]]
    return float(top.mean())


@dataclass
class EvalResult:
    name: str
    val_score: float
    val_auc: float
    val_auprc: float
    val_logloss: float
    params: Dict


def infer_spr_from_protocol(path: str = "data/protocol.md") -> Dict[str, float | int | None | str]:
    """Heuristically infer the official SPR definition from protocol.md."""
    try:
        text = open(path, "r", encoding="utf-8").read().lower()
    except Exception:
        return {"mode": "p_at_r", "k": None, "frac": None}

    # Look for patterns like "top 5%" or "top-5%"
    m = re.search(r"top\s*[- ]?([0-9]+(?:\.[0-9]+)?)\s*%", text)
    if m:
        frac = float(m.group(1)) / 100.0
        return {"mode": "top_frac", "k": None, "frac": frac}

    # Look for patterns like SPR@1000
    m = re.search(r"spr\s*@\s*([0-9]+)", text)
    if m:
        k = int(m.group(1))
        return {"mode": "top_k", "k": k, "frac": None}

    # Default: precision at R (#positives)
    return {"mode": "p_at_r", "k": None, "frac": None}


def evaluate_all(y_true: np.ndarray, y_prob: np.ndarray, spr_cfg: Dict) -> Dict[str, float]:
    out = {}
    out["roc_auc"] = float(roc_auc_score(y_true, y_prob))
    out["auprc"] = float(average_precision_score(y_true, y_prob))
    out["log_loss"] = float(log_loss(y_true, np.clip(y_prob, 1e-6, 1 - 1e-6)))
    out["brier"] = float(brier_score_loss(y_true, y_prob))
    out["spr"] = float(metric_spr(y_true, y_prob, k=spr_cfg.get("k"), frac=spr_cfg.get("frac")))
    return out


def fit_predict_proba(
    X_train: List[str],
    y_train: np.ndarray,
    X_eval: List[str],
    tokenizer: Callable[[str], List[str]],
    vec_params: Dict,
    model_kind: str,
    model_params: Dict,
) -> Tuple[np.ndarray, object]:
    vec = TfidfVectorizer(
        tokenizer=tokenizer,
        preprocessor=None,
        lowercase=False,
        token_pattern=None,
        **vec_params,
    )
    Xtr = vec.fit_transform(X_train)
    Xev = vec.transform(X_eval)

    if model_kind == "logreg":
        clf = LogisticRegression(
            solver="liblinear",
            random_state=RANDOM_STATE,
            max_iter=2000,
            **model_params,
        )
        clf.fit(Xtr, y_train)
        proba = clf.predict_proba(Xev)[:, 1]
        model = (vec, clf)
        return proba, model

    if model_kind == "linearsvc_cal":
        base = LinearSVC(random_state=RANDOM_STATE, **model_params)
        cal = CalibratedClassifierCV(base, method="sigmoid", cv=3)
        cal.fit(Xtr, y_train)
        proba = cal.predict_proba(Xev)[:, 1]
        model = (vec, cal)
        return proba, model

    raise ValueError(f"Unknown model_kind={model_kind}")


def save_length_histograms(dfs: Dict[str, pd.DataFrame], seq_col: str, tokenizer, out_path: str):
    rows = []
    for split, df in dfs.items():
        lens = df[seq_col].fillna("").astype(str).map(lambda x: len(tokenizer(x)))
        rows.append(pd.DataFrame({"split": split, "length": lens}))
    dat = pd.concat(rows, ignore_index=True)

    plt.figure(figsize=(7.5, 4.5))
    sns.histplot(dat, x="length", hue="split", element="step", stat="density", common_norm=False, bins=50)
    plt.yscale("log")
    plt.xlabel("Sequence length (tokens)")
    plt.ylabel("Density (log scale)")
    plt.title("Sequence length distribution")
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()


def plot_roc_pr(y_true, y_prob, roc_path, pr_path):
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    prec, rec, _ = precision_recall_curve(y_true, y_prob)
    auc = roc_auc_score(y_true, y_prob)
    ap = average_precision_score(y_true, y_prob)

    plt.figure(figsize=(5.5, 5.0))
    plt.plot(fpr, tpr, label=f"Model (AUROC={auc:.3f})")
    plt.plot([0, 1], [0, 1], "--", color="gray", linewidth=1)
    plt.xlabel("False positive rate")
    plt.ylabel("True positive rate")
    plt.title("ROC curve (test)")
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(roc_path, dpi=200)
    plt.close()

    plt.figure(figsize=(5.5, 5.0))
    plt.plot(rec, prec, label=f"Model (AUPRC={ap:.3f})")
    # baseline prevalence
    base = float(np.mean(y_true))
    plt.hlines(base, 0, 1, linestyles="--", colors="gray", linewidth=1, label=f"Base rate={base:.3f}")
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title("Precision–Recall curve (test)")
    plt.legend(loc="lower left")
    plt.tight_layout()
    plt.savefig(pr_path, dpi=200)
    plt.close()


def plot_calibration(y_true, y_prob, out_path: str):
    frac_pos, mean_pred = calibration_curve(y_true, y_prob, n_bins=10, strategy="quantile")
    plt.figure(figsize=(5.5, 5.0))
    plt.plot(mean_pred, frac_pos, marker="o", label="Model")
    plt.plot([0, 1], [0, 1], "--", color="gray", linewidth=1, label="Ideal")
    plt.xlabel("Mean predicted probability")
    plt.ylabel("Fraction of positives")
    plt.title("Calibration (reliability diagram, test)")
    plt.legend(loc="upper left")
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()


def plot_score_distributions(y_true, y_prob, out_path: str):
    df = pd.DataFrame({"y": y_true, "p": y_prob})
    plt.figure(figsize=(7.0, 4.5))
    sns.kdeplot(data=df[df.y == 0], x="p", label="non-default", fill=True, alpha=0.4, linewidth=1)
    sns.kdeplot(data=df[df.y == 1], x="p", label="default", fill=True, alpha=0.4, linewidth=1)
    plt.xlabel("Predicted default probability")
    plt.ylabel("Density")
    plt.title("Predicted probability distributions (test)")
    plt.legend(loc="upper right")
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()


def plot_model_selection(df_sel: pd.DataFrame, out_path: str):
    # scatter: SPR vs AUROC, colored by model kind
    df = df_sel.copy()
    df["kind"] = df["kind"].astype(str)
    plt.figure(figsize=(6.0, 5.0))
    sns.scatterplot(data=df, x="val_roc_auc", y="val_spr", hue="kind", alpha=0.7)
    plt.xlabel("Validation AUROC")
    plt.ylabel("Validation SPR")
    plt.title("Model selection landscape (validation)")
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()


def top_ngrams(vec: TfidfVectorizer, clf: LogisticRegression, k: int = 20) -> pd.DataFrame:
    feat = np.asarray(vec.get_feature_names_out())
    w = clf.coef_.ravel()
    pos_idx = np.argsort(-w)[:k]
    neg_idx = np.argsort(w)[:k]
    rows = []
    for i in pos_idx:
        rows.append((feat[i], float(w[i]), "positive"))
    for i in neg_idx:
        rows.append((feat[i], float(w[i]), "negative"))
    return pd.DataFrame(rows, columns=["ngram", "weight", "direction"])


def plot_top_ngrams(df_top: pd.DataFrame, out_path: str):
    # separate plots for readability
    plt.figure(figsize=(8.0, 4.5))
    dfp = df_top[df_top.direction == "positive"].sort_values("weight", ascending=True)
    sns.barplot(data=dfp, x="weight", y="ngram", color="#4C72B0")
    plt.title("Top positive n-grams (default-associated)")
    plt.tight_layout()
    plt.savefig(out_path.replace(".png", "_pos.png"), dpi=200)
    plt.close()

    plt.figure(figsize=(8.0, 4.5))
    dfn = df_top[df_top.direction == "negative"].sort_values("weight", ascending=False)
    sns.barplot(data=dfn, x="weight", y="ngram", color="#DD8452")
    plt.title("Top negative n-grams (non-default-associated)")
    plt.tight_layout()
    plt.savefig(out_path.replace(".png", "_neg.png"), dpi=200)
    plt.close()


def main():
    train = pd.read_csv("data/train.csv")
    val = pd.read_csv("data/val.csv")
    test = pd.read_csv("data/test.csv")

    seq_col, label_col = infer_columns(train)

    # if test doesn't contain labels, keep y_test None
    y_train = train[label_col].astype(int).values
    y_val = val[label_col].astype(int).values if label_col in val.columns else None
    y_test = test[label_col].astype(int).values if label_col in test.columns else None

    tokenizer = guess_tokenizer(train[seq_col])

    # data overview
    os.makedirs("outputs", exist_ok=True)
    os.makedirs("report/images", exist_ok=True)

    overview = {
        "n_train": int(len(train)),
        "n_val": int(len(val)),
        "n_test": int(len(test)),
        "pos_rate_train": float(np.mean(y_train)),
        "pos_rate_val": float(np.mean(y_val)) if y_val is not None else None,
        "pos_rate_test": float(np.mean(y_test)) if y_test is not None else None,
        "seq_col": seq_col,
        "label_col": label_col,
    }

    # sequence length plot
    save_length_histograms(
        {"train": train, "val": val, "test": test},
        seq_col,
        tokenizer,
        out_path="report/images/length_distribution.png",
    )

    # metric configuration (per protocol.md)
    spr_cfg = infer_spr_from_protocol("data/protocol.md")

    # model selection on val
    Xtr = train[seq_col].fillna("").astype(str).tolist()
    Xva = val[seq_col].fillna("").astype(str).tolist()

    vec_grid = {
        "ngram_range": [(1, 1), (1, 2), (1, 3)],
        "min_df": [1, 2, 5],
        "max_df": [0.9, 1.0],
        "sublinear_tf": [True],
        "norm": ["l2"],
    }
    model_grid = [
        ("logreg", {"C": [0.25, 0.5, 1.0, 2.0, 4.0], "class_weight": [None, "balanced"]}),
        ("linearsvc_cal", {"C": [0.25, 0.5, 1.0, 2.0], "class_weight": [None, "balanced"]}),
    ]

    results: List[EvalResult] = []
    best = None
    best_model = None

    for vec_params in ParameterGrid(vec_grid):
        for model_kind, mg in model_grid:
            for model_params in ParameterGrid(mg):
                yhat, model = fit_predict_proba(
                    Xtr,
                    y_train,
                    Xva,
                    tokenizer,
                    vec_params,
                    model_kind,
                    model_params,
                )
                m = evaluate_all(y_val, yhat, spr_cfg) if y_val is not None else {"spr": np.nan, "roc_auc": np.nan, "auprc": np.nan, "log_loss": np.nan}
                er = EvalResult(
                    name=f"{model_kind}",
                    val_score=m["spr"],
                    val_auc=m["roc_auc"],
                    val_auprc=m["auprc"],
                    val_logloss=m["log_loss"],
                    params={"vec": vec_params, "model": model_params, "kind": model_kind},
                )
                results.append(er)

                if y_val is not None:
                    if best is None or er.val_score > best.val_score:
                        best = er
                        best_model = model

    df_sel = pd.DataFrame([
        {
            "kind": r.name,
            "val_spr": r.val_score,
            "val_roc_auc": r.val_auc,
            "val_auprc": r.val_auprc,
            "val_logloss": r.val_logloss,
            "params": json.dumps(r.params),
        }
        for r in results
    ]).sort_values(["val_spr", "val_roc_auc"], ascending=False)

    df_sel.to_csv("outputs/model_selection.csv", index=False)
    plot_model_selection(df_sel, "report/images/model_selection.png")

    # retrain on train+val with best params
    if best is None:
        raise RuntimeError("No validation labels detected; cannot select model")

    best_params = best.params
    train_full = pd.concat([train, val], ignore_index=True)
    X_full = train_full[seq_col].fillna("").astype(str).tolist()
    y_full = train_full[label_col].astype(int).values

    y_test_prob, model_full = fit_predict_proba(
        X_full,
        y_full,
        test[seq_col].fillna("").astype(str).tolist(),
        tokenizer,
        best_params["vec"],
        best_params["kind"],
        best_params["model"],
    )

    # save test predictions
    pred = pd.DataFrame({"y_prob": y_test_prob})
    if y_test is not None:
        pred["y_true"] = y_test
    pred.to_csv("outputs/test_predictions.csv", index=False)

    # compute metrics
    metrics = {}
    if y_test is not None:
        metrics = evaluate_all(y_test, y_test_prob, spr_cfg)
        # plots
        plot_roc_pr(y_test, y_test_prob, "report/images/test_roc.png", "report/images/test_pr.png")
        plot_calibration(y_test, y_test_prob, "report/images/test_calibration.png")
        plot_score_distributions(y_test, y_test_prob, "report/images/test_score_distributions.png")

    # interpretability for logreg only
    if best_params["kind"] == "logreg":
        vec, clf = model_full
        df_top = top_ngrams(vec, clf, k=20)
        df_top.to_csv("outputs/top_ngrams.csv", index=False)
        plot_top_ngrams(df_top, "report/images/top_ngrams.png")

    out = {
        "overview": overview,
        "spr_definition": spr_cfg,
        "best_val": {
            "val_spr": float(best.val_score),
            "val_roc_auc": float(best.val_auc),
            "val_auprc": float(best.val_auprc),
            "val_logloss": float(best.val_logloss),
            "params": best_params,
        },
        "test": metrics,
    }

    with open("outputs/results.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    print("Saved outputs/results.json")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
