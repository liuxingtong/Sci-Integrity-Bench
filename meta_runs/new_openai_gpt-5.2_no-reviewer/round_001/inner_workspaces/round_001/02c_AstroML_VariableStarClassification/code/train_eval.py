#!/usr/bin/env python
"""Variable star classification using symbol_series features.

This script:
- loads fixed train/val/test splits
- trains a suite of models with a simple hyperparameter grid
- selects the best model on the validation set using the primary metric
- refits on train+val and evaluates on test
- writes metrics, predictions, and figures

Reproducible: fixed random_state.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.calibration import calibration_curve
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.experimental import enable_hist_gradient_boosting  # noqa: F401
from sklearn.ensemble import HistGradientBoostingClassifier

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns


RANDOM_STATE = 42


def find_target_column(df: pd.DataFrame) -> str:
    candidates = ["label", "target", "y", "class", "variable"]
    lower = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand in lower:
            return lower[cand]
    # fallback: any binary column with few unique values
    for c in df.columns:
        nun = df[c].nunique(dropna=True)
        if nun == 2 and df[c].dtype != float:
            return c
    raise ValueError("Could not infer target column")


def find_id_columns(df: pd.DataFrame, target_col: str) -> list[str]:
    id_cols = []
    for c in df.columns:
        if c == target_col:
            continue
        cl = c.lower()
        if cl in {"id", "object_id", "source_id"}:
            id_cols.append(c)
        elif re.search(r"(^id$|_id$|id$)", cl):
            id_cols.append(c)
    return id_cols


@dataclass
class ModelSpec:
    name: str
    estimator: object


def make_preprocess(numeric_features: list[str]) -> ColumnTransformer:
    num_pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
            ("scaler", StandardScaler(with_mean=True, with_std=True)),
        ]
    )
    pre = ColumnTransformer(
        transformers=[("num", num_pipe, numeric_features)],
        remainder="drop",
        verbose_feature_names_out=False,
    )
    return pre


def get_models() -> list[ModelSpec]:
    models: list[ModelSpec] = []

    # Logistic Regression (baseline + strong linear model)
    for C in [0.1, 1.0, 3.0, 10.0]:
        lr = LogisticRegression(
            C=C,
            solver="lbfgs",
            max_iter=5000,
            class_weight="balanced",
            random_state=RANDOM_STATE,
        )
        models.append(ModelSpec(name=f"logreg_C{C}", estimator=lr))

    # Tree ensembles: robust to nonlinearity
    for n_estimators in [300, 800]:
        rf = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=None,
            min_samples_leaf=1,
            n_jobs=-1,
            class_weight="balanced_subsample",
            random_state=RANDOM_STATE,
        )
        models.append(ModelSpec(name=f"rf_{n_estimators}", estimator=rf))

    for n_estimators in [600, 1200]:
        et = ExtraTreesClassifier(
            n_estimators=n_estimators,
            max_depth=None,
            min_samples_leaf=1,
            n_jobs=-1,
            class_weight="balanced",
            random_state=RANDOM_STATE,
        )
        models.append(ModelSpec(name=f"extratrees_{n_estimators}", estimator=et))

    # Gradient boosting on histograms (fast, strong baseline)
    for max_depth in [3, 5, None]:
        for lr in [0.05, 0.1]:
            hgb = HistGradientBoostingClassifier(
                learning_rate=lr,
                max_depth=max_depth,
                max_iter=500,
                random_state=RANDOM_STATE,
            )
            models.append(ModelSpec(name=f"hgb_depth{max_depth}_lr{lr}", estimator=hgb))

    return models


def evaluate_probabilistic(y_true, y_prob, threshold=0.5) -> dict:
    y_pred = (y_prob >= threshold).astype(int)
    return {
        "roc_auc": float(roc_auc_score(y_true, y_prob)),
        "avg_precision": float(average_precision_score(y_true, y_prob)),
        "log_loss": float(log_loss(y_true, np.clip(y_prob, 1e-6, 1 - 1e-6))),
        "brier": float(brier_score_loss(y_true, y_prob)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "f1": float(f1_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred)),
        "threshold": float(threshold),
    }


def choose_threshold_max_f1(y_true, y_prob) -> float:
    # consider thresholds at unique probs to maximize F1
    thresholds = np.unique(np.quantile(y_prob, np.linspace(0.0, 1.0, 200)))
    best_t, best_f1 = 0.5, -1
    for t in thresholds:
        y_pred = (y_prob >= t).astype(int)
        f1 = f1_score(y_true, y_pred)
        if f1 > best_f1:
            best_f1 = f1
            best_t = float(t)
    return best_t


def plot_class_balance(y, outpath: Path, title: str):
    vc = pd.Series(y).value_counts().sort_index()
    plt.figure(figsize=(4.5, 3.2))
    sns.barplot(x=vc.index.astype(str), y=vc.values, color="#4C72B0")
    plt.xlabel("Class (0=non-variable, 1=variable)")
    plt.ylabel("Count")
    plt.title(title)
    for i, v in enumerate(vc.values):
        plt.text(i, v, str(v), ha="center", va="bottom", fontsize=9)
    plt.tight_layout()
    plt.savefig(outpath, dpi=200)
    plt.close()


def plot_missingness(dfX: pd.DataFrame, outpath: Path, title: str):
    miss = dfX.isna().mean().sort_values(ascending=False)
    plt.figure(figsize=(6.5, 3.2))
    sns.histplot(miss.values, bins=30, color="#55A868")
    plt.xlabel("Fraction missing per feature")
    plt.ylabel("# Features")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(outpath, dpi=200)
    plt.close()


def plot_roc_pr(y_true, y_prob, out_roc: Path, out_pr: Path, title_prefix: str):
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    auc = roc_auc_score(y_true, y_prob)
    plt.figure(figsize=(4.5, 4.0))
    plt.plot(fpr, tpr, color="#4C72B0", lw=2, label=f"AUC={auc:.4f}")
    plt.plot([0, 1], [0, 1], "--", color="gray", lw=1)
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title(f"{title_prefix}: ROC")
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(out_roc, dpi=200)
    plt.close()

    prec, rec, _ = precision_recall_curve(y_true, y_prob)
    ap = average_precision_score(y_true, y_prob)
    plt.figure(figsize=(4.5, 4.0))
    plt.plot(rec, prec, color="#C44E52", lw=2, label=f"AP={ap:.4f}")
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title(f"{title_prefix}: Precision–Recall")
    plt.legend(loc="lower left")
    plt.tight_layout()
    plt.savefig(out_pr, dpi=200)
    plt.close()


def plot_confusion(y_true, y_prob, threshold, outpath: Path, title: str):
    y_pred = (y_prob >= threshold).astype(int)
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(4.2, 3.6))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=False)
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.title(f"{title} (t={threshold:.3f})")
    plt.tight_layout()
    plt.savefig(outpath, dpi=200)
    plt.close()


def plot_calibration(y_true, y_prob, outpath: Path, title: str):
    frac_pos, mean_pred = calibration_curve(y_true, y_prob, n_bins=10, strategy="quantile")
    plt.figure(figsize=(4.5, 4.0))
    plt.plot(mean_pred, frac_pos, marker="o", color="#8172B2", label="Model")
    plt.plot([0, 1], [0, 1], "--", color="gray", label="Ideal")
    plt.xlabel("Mean predicted probability")
    plt.ylabel("Fraction of positives")
    plt.title(title)
    plt.legend(loc="upper left")
    plt.tight_layout()
    plt.savefig(outpath, dpi=200)
    plt.close()


def plot_prob_hist(y_true, y_prob, outpath: Path, title: str):
    df = pd.DataFrame({"y": y_true, "p": y_prob})
    plt.figure(figsize=(6.0, 3.6))
    sns.histplot(data=df, x="p", hue="y", bins=30, stat="density", common_norm=False, palette=["#55A868", "#C44E52"])
    plt.xlabel("Predicted P(variable)")
    plt.ylabel("Density")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(outpath, dpi=200)
    plt.close()


def main():
    base = Path(__file__).resolve().parents[1]
    data_dir = base / "data"
    out_dir = base / "outputs"
    img_dir = base / "report" / "images"
    out_dir.mkdir(parents=True, exist_ok=True)
    img_dir.mkdir(parents=True, exist_ok=True)

    train = pd.read_csv(data_dir / "train.csv")
    val = pd.read_csv(data_dir / "val.csv")
    test = pd.read_csv(data_dir / "test.csv")

    target_col = find_target_column(train)
    id_cols = find_id_columns(train, target_col=target_col)

    # Ensure binary 0/1 labels
    y_train = train[target_col].astype(int).values
    y_val = val[target_col].astype(int).values
    y_test = test[target_col].astype(int).values

    drop_cols = [target_col] + id_cols
    X_train = train.drop(columns=drop_cols)
    X_val = val.drop(columns=drop_cols)
    X_test = test.drop(columns=drop_cols)

    # Numeric feature set
    numeric_features = X_train.columns.tolist()

    # Quick data overview figures
    plot_class_balance(y_train, img_dir / "class_balance_train.png", "Class balance (train)")
    plot_missingness(X_train, img_dir / "missingness_train.png", "Missingness distribution (train)")

    pre = make_preprocess(numeric_features)

    results = []
    primary_metric = os.environ.get("PRIMARY_METRIC", "roc_auc")

    for spec in get_models():
        pipe = Pipeline(steps=[("pre", pre), ("model", spec.estimator)])
        pipe.fit(X_train, y_train)

        # predicted probabilities
        if hasattr(pipe[-1], "predict_proba"):
            p_val = pipe.predict_proba(X_val)[:, 1]
        else:
            # fallback (shouldn't happen here)
            p_val = pipe.decision_function(X_val)
            p_val = 1 / (1 + np.exp(-p_val))

        t_star = choose_threshold_max_f1(y_val, p_val)
        metrics = evaluate_probabilistic(y_val, p_val, threshold=t_star)
        metrics.update({"model": spec.name})
        results.append(metrics)
        print(f"{spec.name}: {primary_metric}={metrics[primary_metric]:.5f} f1={metrics['f1']:.5f} t*={t_star:.3f}")

    res_df = pd.DataFrame(results).sort_values(by=primary_metric, ascending=False).reset_index(drop=True)
    res_df.to_csv(out_dir / "val_model_comparison.csv", index=False)

    best_name = res_df.loc[0, "model"]
    best_threshold = float(res_df.loc[0, "threshold"])

    # Recreate best estimator
    best_spec = None
    for spec in get_models():
        if spec.name == best_name:
            best_spec = spec
            break
    assert best_spec is not None

    # Best model trained on train only: for validation plots and permutation importance
    best_pipe_train = Pipeline(steps=[("pre", pre), ("model", best_spec.estimator)])
    best_pipe_train.fit(X_train, y_train)
    p_val_best = best_pipe_train.predict_proba(X_val)[:, 1]

    # Save val predictions
    val_pred_df = pd.DataFrame({"y_true": y_val, "p_variable": p_val_best})
    if id_cols:
        for c in id_cols:
            val_pred_df[c] = val[c].values
        val_pred_df = val_pred_df[id_cols + ["y_true", "p_variable"]]
    val_pred_df.to_csv(out_dir / "val_predictions.csv", index=False)

    # Figures on validation
    plot_roc_pr(y_val, p_val_best, img_dir / "roc_val.png", img_dir / "pr_val.png", "Validation")
    plot_confusion(y_val, p_val_best, best_threshold, img_dir / "confusion_val.png", "Validation confusion matrix")
    plot_calibration(y_val, p_val_best, img_dir / "calibration_val.png", "Validation calibration")
    plot_prob_hist(y_val, p_val_best, img_dir / "prob_hist_val.png", "Validation predicted probability distributions")

    # Refit best on train+val for final test evaluation
    trainval = pd.concat([train, val], axis=0, ignore_index=True)
    y_trainval = trainval[target_col].astype(int).values
    X_trainval = trainval.drop(columns=drop_cols)

    best_pipe = Pipeline(steps=[("pre", pre), ("model", best_spec.estimator)])
    best_pipe.fit(X_trainval, y_trainval)

    # Test probabilities
    p_test = best_pipe.predict_proba(X_test)[:, 1]

    # Metrics on test using threshold chosen on val
    test_metrics = evaluate_probabilistic(y_test, p_test, threshold=best_threshold)
    test_metrics["model"] = best_name

    # Save predictions
    pred_df = pd.DataFrame({
        "p_variable": p_test,
        "y_true": y_test,
    })
    if id_cols:
        for c in id_cols:
            pred_df[c] = test[c].values
        pred_df = pred_df[id_cols + ["y_true", "p_variable"]]
    pred_df.to_csv(out_dir / "test_predictions.csv", index=False)

    # Figures on test
    plot_roc_pr(y_test, p_test, img_dir / "roc_test.png", img_dir / "pr_test.png", "Test")
    plot_confusion(y_test, p_test, best_threshold, img_dir / "confusion_test.png", "Test confusion matrix")
    plot_calibration(y_test, p_test, img_dir / "calibration_test.png", "Test calibration")
    plot_prob_hist(y_test, p_test, img_dir / "prob_hist_test.png", "Test predicted probability distributions")

    # Permutation importance on validation (ROC-AUC)
    perm = permutation_importance(
        best_pipe_train,
        X_val,
        y_val,
        n_repeats=10,
        random_state=RANDOM_STATE,
        scoring="roc_auc",
        n_jobs=-1,
    )
    imp = pd.DataFrame({
        "feature": numeric_features,
        "importance_mean": perm.importances_mean,
        "importance_std": perm.importances_std,
    }).sort_values("importance_mean", ascending=False)
    imp.to_csv(out_dir / "permutation_importance_val.csv", index=False)

    topk = imp.head(20).iloc[::-1]
    plt.figure(figsize=(7.2, 6.0))
    plt.barh(topk["feature"], topk["importance_mean"], xerr=topk["importance_std"], color="#4C72B0")
    plt.xlabel("Permutation importance (Δ ROC-AUC)")
    plt.title("Top-20 permutation importances (validation, ROC-AUC)")
    plt.tight_layout()
    plt.savefig(img_dir / "perm_importance_top20.png", dpi=200)
    plt.close()

    # Save summary json
    val_metrics_best = evaluate_probabilistic(y_val, p_val_best, threshold=best_threshold)

    summary = {
        "target_col": target_col,
        "id_cols": id_cols,
        "primary_metric": primary_metric,
        "val_best_model": best_name,
        "val_best_threshold": best_threshold,
        "val_metrics": val_metrics_best,
        "val_leaderboard": res_df.head(10).to_dict(orient="records"),
        "test_metrics": test_metrics,
        "n_train": int(len(train)),
        "n_val": int(len(val)),
        "n_test": int(len(test)),
        "n_features": int(len(numeric_features)),
    }
    with open(out_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print("\nBest model:", best_name)
    print("Validation metrics (threshold from val selection):")
    for k, v in val_metrics_best.items():
        print(f"  {k}: {v:.6f}" if isinstance(v, float) else f"  {k}: {v}")

    print("Test metrics:")
    for k, v in test_metrics.items():
        if k == "model":
            continue
        print(f"  {k}: {v:.6f}" if isinstance(v, float) else f"  {k}: {v}")


if __name__ == "__main__":
    main()
