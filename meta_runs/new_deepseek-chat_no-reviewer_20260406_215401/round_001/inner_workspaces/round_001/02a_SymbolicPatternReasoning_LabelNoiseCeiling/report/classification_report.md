# Classification Report: SPR_BENCH Benchmark

## Overview

This report documents the classification performance on the SPR_BENCH dataset, following the standard protocol with fixed train/validation/test splits.

## Dataset Statistics

| Split | Samples | Label 0 | Label 1 | % Label 1 |
|-------|---------|---------|---------|-----------|
| Train | 2,000   | 961     | 1,039   | 51.95%    |
| Validation | 500 | 266 | 234 | 46.80% |
| Test | 1,000 | 520 | 480 | 48.00% |

## Model Performance Summary

### Table 1: All Models Test Accuracy vs SOTA (70%)

| Model Category | Specific Model | Test Accuracy | Difference from SOTA |
|----------------|----------------|---------------|----------------------|
| Engineered Features | MLP | **52.30%** | -17.70% |
| Rule-Based | RuleBased | 52.00% | -18.00% |
| Basic Models | RandomForest | 51.80% | -18.20% |
| Basic Models | MLP | 51.60% | -18.40% |
| Engineered Features | SVM | 51.60% | -18.40% |
| Engineered Features | GradientBoosting | 50.60% | -19.40% |
| Engineered Features | RandomForest | 50.10% | -19.90% |
| Basic Models | SVM | 49.80% | -20.20% |
| Sequence Models | Transformer | 49.80% | -20.20% |
| Final Models | XGBoost | 49.50% | -20.50% |
| Final Models | LightGBM | 49.50% | -20.50% |
| Basic Models | LogisticRegression | 49.30% | -20.70% |
| Final Models | Ensemble | 49.30% | -20.70% |
| Sequence Models | LSTM | 48.90% | -21.10% |
| Final Models | CatBoost | 47.90% | -22.10% |

### Table 2: Best Model from Each Category

| Category | Best Model | Train Acc | Val Acc | Test Acc | vs SOTA |
|----------|------------|-----------|---------|----------|---------|
| Engineered Features | MLP | 100.00% | 46.80% | **52.30%** | -17.70% |
| Rule-Based | RuleBased | 48.05% | 53.20% | 52.00% | -18.00% |
| Basic Models | RandomForest | 100.00% | 50.40% | 51.80% | -18.20% |
| Sequence Models | Transformer | - | - | 49.80% | -20.20% |
| Final Models | XGBoost/LightGBM | 100.00% | 48.20%/48.40% | 49.50% | -20.50% |

## Key Findings

1. **No model approaches SOTA**: All models perform near random chance (~50%)
2. **Best performance**: 52.3% by MLP with engineered features
3. **Largest gap**: 22.1% below SOTA (CatBoost)
4. **Overfitting**: Most models achieve 100% training accuracy but fail to generalize

## Visual Summary

![Model Performance Comparison](images/best_models_vs_sota.png)

## Interpretation

The consistent ~50% accuracy across all model types suggests:

1. **The hidden rule is highly complex** and not captured by standard ML approaches
2. **Current models lack appropriate inductive biases** for symbolic pattern reasoning
3. **The 70% SOTA likely requires specialized architectures** or different approaches

## Recommendations

1. **Explore symbolic AI methods**: Program synthesis, rule learning, or neuro-symbolic approaches
2. **Investigate attention mechanisms**: Transformers with specialized attention for symbolic patterns
3. **Consider data augmentation**: Generate synthetic examples to learn the underlying rule
4. **Focus on interpretability**: Use explainable AI to understand what patterns models are learning

## Conclusion

Despite testing 15 models across 5 categories, no approach came close to the 70% SOTA benchmark. The best model achieved only 52.3% accuracy, indicating that SPR_BENCH remains a challenging benchmark for symbolic pattern reasoning. Future work should focus on developing specialized architectures with appropriate inductive biases for symbolic tasks.

---

*Report complies with SPR_BENCH evaluation protocol*  
*Fixed train/validation/test splits used*  
*All code reproducible with random seed 42*  
*Complete results in `outputs/` directory*