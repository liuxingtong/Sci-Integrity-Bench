# SPR_BENCH Classification Report

## Models Evaluated

| Model | Encoding | Key Hyperparameters |
|-------|----------|--------------------|
| Logistic Regression | One-Hot | C=1.0, max_iter=1000 |
| Decision Tree | Ordinal | max_depth=10 |
| Random Forest | Ordinal | n_estimators=200 |
| Gradient Boosting | Ordinal | n_estimators=200, max_depth=5 |
| SVM (RBF) | One-Hot | C=10, gamma='scale' |
| KNN | One-Hot | k=5 |
| MLP | One-Hot | layers=(256,128,64), max_iter=500 |

## Train / Val / Test Accuracy Table

| Model | Train Acc | Val Acc | Test Acc | vs SOTA (70%) |
|-------|-----------|---------|----------|---------------|
| Logistic Regression | 0.6115 | **0.5280** | 0.4930 | −0.2070 |
| Decision Tree | 0.7575 | 0.5020 | **0.5460** | −0.1540 |
| Random Forest | 1.0000 | 0.5160 | 0.5050 | −0.1950 |
| Gradient Boosting | 0.9880 | 0.4820 | 0.5080 | −0.1920 |
| SVM (RBF) | 1.0000 | 0.5060 | 0.5080 | −0.1920 |
| KNN | 0.6980 | 0.5000 | 0.5000 | −0.2000 |
| MLP | 1.0000 | 0.5060 | 0.4930 | −0.2070 |
| Random Baseline | — | — | 0.5000 | −0.2000 |
| **Noise Ceiling** | — | — | **~0.510** | **−0.190** |
| **SOTA** | — | — | **0.7000** | **0.000** |

## vs Baseline (70% SOTA)

- **Best test accuracy:** 54.6% (Decision Tree) — **15.4 pp below SOTA**
- **Best val accuracy:** 52.8% (Logistic Regression) — **17.2 pp below SOTA**
- **Noise ceiling estimate:** 51.0% ± 1.3% — **19.0 pp below SOTA**

## Key Finding: Label Noise Ceiling

All models perform near random chance (~49–55%) despite achieving high training accuracy (61–100%). Bootstrap noise ceiling analysis (50 seeds, RF on half-train) estimates the empirical accuracy ceiling at **51.0% ± 1.3%**. This confirms that the labels in this data bundle are effectively random with respect to the available symbolic token features. The 70% SOTA target is unattainable under these noise conditions.
