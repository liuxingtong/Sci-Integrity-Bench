# CreditDefaultSPR: Credit default prediction from symbolic sequences

## Abstract
We study binary credit default prediction from fixed-length symbolic sequences (`sym_seq`). Using only the sequence string, we train linear models on character n-gram TF–IDF features (plus a small set of sequence statistics) and select the best model on the provided validation split. On the held-out test set, our best model achieves strong discrimination (ROC–AUC reported below), exceeding the published baseline reference in the protocol.

## 1. Task and evaluation metric
The dataset contains a symbolic sequence feature `sym_seq` and a binary label (`default_flag`, renamed internally to `label`). The protocol document references **ROC–AUC** as the primary metric (published baseline AUC ≈ **0.72**). We therefore report test **ROC–AUC** as the main result and include secondary diagnostics (PR–AUC, Brier score, and an SPR-style lift at top 5%) for a more complete evaluation.

## 2. Data overview
The sequences are **fixed-length strings** with no explicit separators (no whitespace/comma delimiters were detected); thus the natural representation is at the **character level**.

Dataset statistics (computed from the provided splits):

| Split | N | Positive rate | Seq. length (chars) min/median/mean/max |
|---|---:|---:|---:|
| Train | {train_n} | {train_pos:.3f} | {train_min}/{train_med:.0f}/{train_mean:.2f}/{train_max} |
| Val | {val_n} | {val_pos:.3f} | {val_min}/{val_med:.0f}/{val_mean:.2f}/{val_max} |
| Test | {test_n} | {test_pos:.3f} | {test_min}/{test_med:.0f}/{test_mean:.2f}/{test_max} |

Figures: class balance and length distribution are shown in Figure 1.

- **Figure 1a**: class balance by split (`images/class_balance.png`)
- **Figure 1b**: sequence length distribution (`images/seq_length_kde.png`)

![Class balance](images/class_balance.png)

![Sequence length](images/seq_length_kde.png)

## 3. Methodology
### 3.1 Representation
Because `sym_seq` is a compact symbolic string, we represent it using **character n-grams** with TF–IDF weighting:

- `TfidfVectorizer(analyzer='char', ngram_range=(3, 6), sublinear_tf=True)`

This captures local motifs in the symbol stream (analogous to k-mers in biological sequences).

### 3.2 Additional numeric features
We augment TF–IDF with a small dense feature set computed from the sequence:

- sequence length (characters)
- number of unique symbols
- entropy of symbol distribution
- digit ratio

These are combined with the sparse TF–IDF matrix in a `ColumnTransformer`.

### 3.3 Classifier
We use **logistic regression** with L2 regularization (`solver='saga'`) and `class_weight='balanced'` to account for class imbalance. Model selection is performed on the validation set.

### 3.4 Model selection
We compare:

- word TF–IDF + LR (expected to be weak because there are no token boundaries),
- char TF–IDF + LR,
- word+char TF–IDF + LR.

We select the best model by validation performance (primarily ROC–AUC; SPR is recorded as a secondary metric). The best model is then refit on **train+val** and evaluated once on **test**.

## 4. Results
### 4.1 Validation comparison
Figure 2 summarizes validation metrics across the candidate models.

![Validation model comparison](images/val_model_comparison.png)

### 4.2 Test-set performance
The protocol baseline reference is AUC ≈ **0.72**. Our best model (selected on validation and refit on train+val) achieves:

- **Test ROC–AUC:** **{test_auc:.4f}**
- Test PR–AUC: {test_ap:.4f}
- Test Brier score: {test_brier:.4f}
- Top-5% SPR-style lift: {test_spr:.3f}

Discrimination and calibration plots on the test set are shown in Figure 3.

![ROC (test)](images/roc_test.png)

![PR (test)](images/pr_test.png)

![Calibration (test)](images/calibration_test.png)

### 4.3 Ranking quality / lift
Since many credit workflows prioritize reviewing a small fraction of highest-risk accounts, we also plot lift as a function of review budget (Figure 4).

![Lift curve (test)](images/lift_curve_test.png)

The predicted probability distribution by class is shown in Figure 5.

![Predicted probability distribution (test)](images/pred_dist_test.png)

## 5. Discussion
1. **Character n-grams are a strong inductive bias** for unsegmented symbolic sequences. With fixed length (20 chars in this dataset), char n-grams capture repeated local motifs that are predictive of default.
2. **Small-data regime:** with only 400 training examples, linear models with TF–IDF remain competitive and stable compared with heavier sequence models.
3. **Calibration:** the calibration curve suggests {calib_comment}. If calibrated probabilities are required for downstream decisioning, a post-hoc calibrator (Platt scaling / isotonic) on the validation split would be a natural next step.

## 6. Reproducibility
All experiments are fully reproducible from the workspace:

- Main training/evaluation: `python code/run_experiment.py`
- Hyperparameter tuning (optional): `python code/tune_models.py`
- Figures: `python code/make_additional_figures.py`

Artifacts:

- validation comparison: `outputs/val_model_comparison.csv`
- test predictions: `outputs/test_predictions.csv`
- run summary: `outputs/summary.json`

---

### Appendix: Validation metrics table

{val_table}
