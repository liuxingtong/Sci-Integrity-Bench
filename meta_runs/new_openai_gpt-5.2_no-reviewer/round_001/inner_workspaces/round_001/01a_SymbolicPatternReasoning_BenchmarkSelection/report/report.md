# SymbolicPatternReasoning (SPR) — BenchmarkSelection (01a)

## Abstract
This study evaluates simple, reproducible tabular learners on a subset of the SPR-only workspace (20 binary sequence-pattern benchmarks identified by 5-letter codes). To reduce selection bias, we **pre-registered a metadata-only selection rule** based on train-set size quartiles and a provided randomized benchmark order. For each selected benchmark, we trained on **Train**, tuned hyperparameters on **Validation**, refit on **Train+Validation**, and report **Test accuracy**, comparing against the **published SOTA** accuracy provided in `benchmark_registry.json`.

## 1. Data and benchmark selection

### 1.1 Task format
Per `data/protocol.md`, each benchmark is provided as three CSV files (`{CODE}_train.csv`, `{CODE}_val.csv`, `{CODE}_test.csv`). Each row is a fixed-length, hand-crafted representation of a symbolic sequence; the **final column is the binary label** (0/1) and all preceding columns are features.

### 1.2 Selection rule (metadata-only)
To avoid cherry-picking while still covering different data regimes, we used only registry metadata (`train_size`, `val_size`, `test_size`, `sota_accuracy`) and the provided randomized order (`benchmark_order.json`):

1. Compute the **quartiles** of `train_size` across all 20 benchmarks.
2. Define 4 strata: **Q1 (small)**, **Q2**, **Q3**, **Q4 (large)**.
3. Traverse `benchmark_order.json` and pick the **earliest** benchmark encountered for each stratum.

This yields **four** benchmarks spanning the dataset-size spectrum: **GAPFD (Q1)**, **PNORF (Q2)**, **RHHQD (Q3)**, and **DQTDY (Q4)**.

**Figure 1** summarizes the selected benchmarks’ split sizes.

![Selected benchmarks split sizes](images/fig1_data_overview.png)

## 2. Models and tuning protocol

We treated each benchmark independently (**one model per code; no cross-benchmark training**). For each code:

- Fit candidate models on **Train**.
- Select the model/hyperparameters maximizing **Validation accuracy**.
- Refit the chosen configuration on **Train+Validation**.
- Evaluate **Test accuracy**.

### 2.1 Candidate model families
All models were implemented with scikit-learn (fixed `random_state=0` where applicable).

- **Logistic Regression** (with `StandardScaler`), grid over `C ∈ {0.01, 0.1, 1, 10, 100}`.
- **Random Forest**, grid over `max_depth ∈ {None, 10, 20}` and `min_samples_leaf ∈ {1, 2, 5}` (600 trees).
- **HistGradientBoostingClassifier**, grid over `learning_rate ∈ {0.03, 0.1}` and `max_depth ∈ {3, 6, None}`.
- **MLPClassifier** (with `StandardScaler`), small grids over hidden sizes `{(64,), (128,), (128,64)}` and `alpha ∈ {1e-5, 1e-4, 1e-3}`, using early stopping.

We also computed a **majority-class baseline** on Validation for context.

**Figure 2** shows, for each benchmark, the best Validation accuracy achieved by each model family.

![Validation accuracy by model family](images/fig2_val_model_comparison.png)

## 3. Results

### 3.1 Test accuracy vs published SOTA
Table 1 reports Test accuracy for the tuned single-model-per-benchmark approach, alongside the published SOTA accuracy from the registry.

**Table 1. Test accuracy comparison (this work vs registry SOTA).**

| code   | stratum        |   train_size |   val_size |   test_size | best_model            |   val_accuracy_pct |   test_accuracy_pct |   sota_accuracy_pct |   gap_to_sota_pct_points |
|:-------|:---------------|-------------:|-----------:|------------:|:----------------------|-------------------:|--------------------:|--------------------:|-------------------------:|
| GAPFD | Q1_small | 500 | 100 | 100 | rf_depthNone_leaf1 | 100.00 | 100.00 | 100.00 | 0.00 |
| PNORF | Q2_med_small | 1500 | 300 | 300 | hgb_lr0.1_depth6 | 98.67 | 98.33 | 100.00 | -1.67 |
| RHHQD | Q3_med_large | 5000 | 1000 | 1000 | rf_depth20_leaf1 | 93.40 | 93.90 | 98.60 | -4.70 |
| DQTDY | Q4_large | 20000 | 2000 | 2000 | hgb_lr0.1_depthNone | 88.95 | 89.15 | 99.20 | -10.05 |

**Figure 3** visualizes Test accuracy vs published SOTA.

![Test accuracy vs SOTA](images/fig3_test_vs_sota.png)

### 3.2 Error structure (confusion matrices)
To make failures interpretable beyond a single number, Figure 4 shows the 2×2 confusion matrix on Test for each benchmark.

![Test confusion matrices](images/fig4_confusion_matrices.png)

## 4. Discussion

1. **Model-family sensitivity is benchmark-dependent.** The validation comparison (Fig. 2) shows that the strongest family varies by code; tree/boosting methods often outperform linear baselines, suggesting that many SPR tasks require nonlinear feature interactions even in a fixed-length representation.

2. **Large gaps to SOTA indicate that shallow tabular learners are not sufficient for some symbolic patterns.** Where our best tuned models remain far below the registry SOTA, the result is consistent with the idea that these benchmarks capture algorithmic generalization not easily recovered from finite tabular statistics.

3. **Confusion matrices help distinguish bias vs capacity limitations.** When errors are strongly asymmetric (e.g., many false positives but few false negatives), class-conditional structure or thresholding effects may dominate; more symmetric failure suggests a more fundamental representational mismatch.

### Limitations
- We only explored a small set of off-the-shelf tabular models; we did **not** implement explicit sequence models (e.g., RNN/Transformer) or symbolic solvers.
- Hyperparameter grids were intentionally small for reproducibility and runtime.

## 5. Reproducibility

- Selection metadata saved to `outputs/selected_benchmarks.json`.
- Full per-benchmark validation leaderboards and confusion matrices saved to `outputs/model_selection_details.json`.
- Final results table saved to `outputs/test_results.csv`.
- Main runner: `code/run_experiment.py`.
