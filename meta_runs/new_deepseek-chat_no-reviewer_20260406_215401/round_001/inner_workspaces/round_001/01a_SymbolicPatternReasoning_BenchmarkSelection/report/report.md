# Research Report: Symbolic Pattern Reasoning Benchmark Selection and Evaluation

## Executive Summary

This research task involved selecting and evaluating four benchmarks from the SPR (Symbolic Pattern Reasoning) benchmark suite. The goal was to train models on these benchmarks, tune them on validation sets, and compare test accuracy against published State-of-the-Art (SOTA) results. Key findings:

1. Standard ML models significantly outperform SOTA on GAPFD (+25.9% improvement)
2. Models struggle with high-SOTA benchmarks ZOBKB and NUFES (-41.7% and -41.8% gaps)
3. Performance varies dramatically across benchmarks, highlighting different reasoning requirements

## Complete Analysis

For the full benchmark selection rationale, detailed results, and discussion, please see the comprehensive benchmark report:

**[Benchmark Report](benchmark_report.md)**

## Key Results Table

| Benchmark | Sequence Length | Best Model | Test Accuracy | SOTA Accuracy | Difference |
|-----------|----------------|------------|---------------|---------------|------------|
| ZOBKB     | 6              | LR         | 53.5%         | 95.2%         | -41.7%     |
| NUFES     | 8              | LR         | 53.0%         | 94.8%         | -41.8%     |
| FDLOT     | 12             | RF         | 45.5%         | 60.4%         | -14.9%     |
| GAPFD     | 4              | RF         | 88.5%         | 62.6%         | +25.9%     |

## Visualization

![Accuracy Comparison](images/final_accuracy_comparison.png)

## Methodology Summary

- **Benchmark Selection**: Four benchmarks selected for diversity in SOTA accuracy, sequence length, and vocabulary size
- **Models Evaluated**: Random Forest, Gradient Boosting, Logistic Regression
- **Preprocessing**: Label encoding of categorical token sequences
- **Training Protocol**: Train on 400 samples, tune on 100 validation samples, test on 200 samples
- **Independent Models**: One model per benchmark, no cross-benchmark training

## Conclusions

The evaluation reveals that symbolic pattern reasoning benchmarks test different capabilities:

1. **Simple pattern recognition** (GAPFD): Standard ML excels
2. **Moderate complexity** (FDLOT): ML approaches competitive but below SOTA
3. **Complex symbolic reasoning** (ZOBKB, NUFES): Specialized symbolic approaches substantially outperform ML

This suggests that while ML has made progress on certain symbolic tasks, specialized symbolic AI remains crucial for complex reasoning problems.

## Files Generated

- `code/analyze_benchmarks.py`: Analysis of all 20 benchmarks
- `code/train_models.py`: Initial modeling with Random Forest
- `code/train_fast_models.py`: Comprehensive modeling with multiple algorithms
- `outputs/benchmark_summary.csv`: Characteristics of all benchmarks
- `outputs/simple_model_results.csv`: Detailed model results
- `outputs/best_simple_results.csv`: Best model per benchmark
- `report/benchmark_report.md`: Comprehensive benchmark report
- `report/images/final_accuracy_comparison.png`: Visualization of results

All code is reproducible and available in the workspace.