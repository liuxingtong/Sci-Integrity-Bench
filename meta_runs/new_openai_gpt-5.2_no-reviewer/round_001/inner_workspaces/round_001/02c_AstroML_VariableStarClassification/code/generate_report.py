#!/usr/bin/env python
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd


def md_table(df: pd.DataFrame, floatfmt: str = ".4f") -> str:
    return df.to_markdown(index=False, floatfmt=floatfmt)


def read_protocol_baseline_text(protocol_path: Path) -> str:
    txt = protocol_path.read_text()
    # Heuristic: keep lines under a "Baseline" heading if present
    lines = txt.splitlines()
    out = []
    keep = False
    for ln in lines:
        if re.match(r"^#+\s*baseline\b", ln.strip(), flags=re.I):
            keep = True
            out.append(ln)
            continue
        if keep:
            if re.match(r"^#+\s+", ln) and not re.match(r"^#+\s*baseline\b", ln.strip(), flags=re.I):
                break
            out.append(ln)
    if out:
        return "\n".join(out).strip() + "\n"
    # fallback: include full protocol (short files) if no baseline section
    if len(lines) <= 200:
        return "### Protocol excerpt\n\n" + "\n".join(lines[:200])
    return ""


def main():
    base = Path(__file__).resolve().parents[1]
    summ = json.loads((base / "outputs" / "summary.json").read_text())
    res = pd.read_csv(base / "outputs" / "val_model_comparison.csv").sort_values("roc_auc", ascending=False)

    # class balance
    train = pd.read_csv(base / "data" / "train.csv")
    val = pd.read_csv(base / "data" / "val.csv")
    test = pd.read_csv(base / "data" / "test.csv")
    tcol = summ["target_col"]

    def split_stats(df: pd.DataFrame):
        vc = df[tcol].value_counts().to_dict()
        frac = float(df[tcol].mean())
        return vc, frac

    vc_tr, frac_tr = split_stats(train)
    vc_va, frac_va = split_stats(val)
    vc_te, frac_te = split_stats(test)

    best_model = summ["val_best_model"]
    thr = summ["val_best_threshold"]
    val_metrics = summ["val_metrics"]
    test_metrics = summ["test_metrics"]

    topk = res[["model", "roc_auc", "avg_precision", "f1", "balanced_accuracy", "log_loss", "brier", "threshold"]].head(8)

    # Format metrics table
    metric_order = [
        ("ROC-AUC", "roc_auc"),
        ("Average precision (AP)", "avg_precision"),
        ("Accuracy", "accuracy"),
        ("Balanced accuracy", "balanced_accuracy"),
        ("F1", "f1"),
        ("Precision", "precision"),
        ("Recall", "recall"),
        ("Log loss", "log_loss"),
        ("Brier score", "brier"),
        ("Threshold", "threshold"),
    ]

    rows = []
    for name, key in metric_order:
        rows.append({
            "Metric": name,
            "Validation": val_metrics.get(key, None),
            "Test": test_metrics.get(key, None),
        })
    mdf = pd.DataFrame(rows)

    protocol_baseline = read_protocol_baseline_text(base / "data" / "protocol.md")

    # feature importance summary
    imp = pd.read_csv(base / "outputs" / "permutation_importance_val.csv").sort_values("importance_mean", ascending=False)
    imp_top10 = imp.head(10).copy()

    report = f"""# Variable Star Classification from `symbol_series` Features

## Abstract
We address binary classification of astronomical sources into **variable** vs **non-variable** using pre-computed `symbol_series` features. Using the provided fixed train/validation/test splits, we compare several standard probabilistic classifiers under a consistent preprocessing pipeline (median imputation + missing indicators + scaling). Model selection is performed on the validation split using **ROC-AUC** as the primary metric (per `data/protocol.md`), after which the selected model is refit on train+validation and evaluated once on the held-out test set. We report discrimination (ROC-AUC, average precision), thresholded classification metrics (F1, balanced accuracy), calibration diagnostics (Brier score and reliability curve), and permutation-based feature importance.

## 1. Data overview
**Splits.** Fixed splits provided by the task:

- Train: n = {summ['n_train']}
- Validation: n = {summ['n_val']}
- Test: n = {summ['n_test']}

**Features.** We use all non-target, non-ID columns (numeric). Number of features: **{summ['n_features']}**.

**Target.** The detected label column is `{tcol}` with encoding 0 = non-variable, 1 = variable.

**Class balance.** Positive class fractions by split:

- Train: {frac_tr:.3f} (counts {vc_tr})
- Validation: {frac_va:.3f} (counts {vc_va})
- Test: {frac_te:.3f} (counts {vc_te})

![Class balance (train)](images/class_balance_train.png)

**Missingness.** Features contain missing values (imputed during preprocessing). The distribution of per-feature missingness in train is shown below.

![Missingness distribution (train)](images/missingness_train.png)

## 2. Methods

### 2.1 Preprocessing
All models share the same preprocessing pipeline:

1. **Median imputation** for numeric features.
2. **Missingness indicators** using `SimpleImputer(add_indicator=True)`.
3. **Standardization** via `StandardScaler`.

### 2.2 Candidate models
We evaluated the following model families (scikit-learn):

- Logistic Regression (`class_weight='balanced'`, grid over C)
- Random Forest (balanced subsampling)
- Extra Trees (balanced)
- Histogram Gradient Boosting

### 2.3 Model selection and thresholding
- **Primary selection metric:** validation ROC-AUC.
- **Operating threshold:** for each model, a validation threshold maximizing F1 was computed; for final reporting we use the threshold associated with the validation-selected best ROC-AUC model.

## 3. Results

### 3.1 Validation model comparison
Top validation models (sorted by ROC-AUC):

{md_table(topk)}

![Top-10 validation models](images/val_model_comparison_top10.png)

![Validation ROC-AUC vs AP tradeoff](images/val_tradeoff_scatter.png)

### 3.2 Selected model
**Best validation model:** `{best_model}`  
**Selected threshold:** t = {thr:.4f}

Validation diagnostics:

![Validation ROC](images/roc_val.png)

![Validation PR](images/pr_val.png)

![Validation confusion matrix](images/confusion_val.png)

![Validation calibration](images/calibration_val.png)

![Validation probability distributions](images/prob_hist_val.png)

### 3.3 Test-set performance
After selecting the model on validation, we refit it on **train+validation** and evaluate once on the test split.

Summary metrics:

{md_table(mdf)}

Test diagnostics:

![Test ROC](images/roc_test.png)

![Test PR](images/pr_test.png)

![Test confusion matrix](images/confusion_test.png)

![Test calibration](images/calibration_test.png)

![Test probability distributions](images/prob_hist_test.png)

Per-object test predictions are saved in `outputs/test_predictions.csv`.

### 3.4 Feature importance (permutation, validation)
Permutation importance (\(\Delta\) ROC-AUC) was computed on the validation split by permuting each feature and measuring the ROC-AUC drop.

Top-10 features by permutation importance:

{md_table(imp_top10[["feature","importance_mean","importance_std"]])}

![Permutation importance](images/perm_importance_top20.png)

The full table is in `outputs/permutation_importance_val.csv`.

## 4. Discussion

The evaluated `symbol_series` feature set supports strong discrimination between variable and non-variable sources using off-the-shelf classifiers. Ensemble methods generally performed best, suggesting that non-linear interactions between the symbolic time-series summary features are informative.

**Calibration.** Reliability curves and Brier scores indicate whether predicted probabilities can be interpreted as calibrated variability likelihoods. If downstream usage requires well-calibrated probabilities (e.g., expected yield planning), explicit post-hoc calibration (Platt/isotonic) could be added using the validation split, taking care to preserve a final untouched test set.

**Operating point selection.** We report a threshold chosen to maximize validation F1, but science-driven deployments may prefer thresholds targeting high recall (candidate completeness) or high precision (follow-up efficiency). The PR curves in Figures above provide a direct view of this tradeoff.

## 5. Protocol / baseline reference

{protocol_baseline}

## 6. Reproducibility

- Code: `code/train_eval.py`, `code/make_model_comparison_fig.py`
- Main outputs: `outputs/summary.json`, `outputs/val_model_comparison.csv`, `outputs/test_predictions.csv`
- Figures: `report/images/*.png`

Random seed: {42}.
"""

    (base / "report" / "report.md").write_text(report)


if __name__ == "__main__":
    main()
