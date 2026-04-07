# Symbolic Pattern Reasoning Benchmark Selection: Evaluation Report

## 1. Introduction

This report details the selection, evaluation, and comparison of four symbolic pattern reasoning benchmarks from the SPR suite. The task is to develop a high-performance method for binary classification of symbolic sequences, using only the provided train/validation/test splits. Benchmarks are identified by opaque five-letter codes, with published SOTA accuracies given in the registry.

## 2. Benchmark Selection Rationale

We selected four benchmarks to cover a diverse range of difficulty, sequence length, and vocabulary size. The selection was based on analysis of `benchmark_registry.json` and exploratory data analysis of CSV files. The chosen benchmarks are:

- **FDLOT**: Low SOTA (60.4%), long sequence (12 tokens), large vocabulary (16 unique tokens). Represents a challenging benchmark.
- **RHHQD**: Medium SOTA (70.5%), medium sequence (8 tokens), medium vocabulary (9 tokens).
- **ILULR**: Medium SOTA (78.0%), short sequence (4 tokens), small vocabulary (4 tokens). Allows testing on simple patterns.
- **ZOBKB**: High SOTA (95.2%), medium sequence (6 tokens), medium vocabulary (8 tokens). Represents a benchmark where near-perfect performance is possible.

This selection spans the quartiles of SOTA accuracy and provides variation in sequence length and vocabulary size, enabling a robust evaluation of our method.

## 3. Methodology

We implemented several modeling approaches, each trained independently per benchmark (no cross-benchmark training). All models used the train set for training, validation set for hyperparameter tuning, and test set for final evaluation.

### 3.1 Data Preprocessing
Token sequences were treated as categorical variables. We experimented with two encoding schemes:
1. **One‑hot encoding** of each token position.
2. **Shape–color decomposition**: each token (e.g., `Sr`) was split into shape (`S`) and color (`r`) components, which were then one‑hot encoded. Additional engineered features included counts of each shape/color, equality between adjacent positions, and parity of counts.

### 3.2 Models
- **Random Forest** (RF) with one‑hot encoding.
- **XGBoost** with one‑hot encoding and simple engineered features (adjacent equality, uniqueness).
- **Random Forest with shape–color features** (RF‑SC).
- **LSTM** (attempted but not pursued due to long training times and overfitting on small data).

Hyperparameters (number of trees, max depth, learning rate) were tuned on the validation set via grid search. The best configuration was retrained on the combined train+validation set before evaluating on the held‑out test set.

### 3.3 Evaluation Metric
Accuracy on the test split, compared to the published SOTA accuracy (%).

## 4. Results

Table 1 summarizes the best test accuracy achieved by our method versus the published SOTA for each selected benchmark.

**Table 1: Test accuracy comparison**
| Benchmark | Sequence Length | Vocabulary Size | Our Accuracy (%) | SOTA Accuracy (%) | Difference (Our – SOTA) |
|-----------|----------------|-----------------|------------------|-------------------|------------------------|
| FDLOT     | 12             | 16              | 55.5             | 60.4              | –4.9                   |
| RHHQD     | 8              | 9               | 56.0             | 70.5              | –14.5                  |
| ILULR     | 4              | 4               | 93.0             | 78.0              | +15.0                  |
| ZOBKB     | 6              | 8               | 52.5             | 95.2              | –42.7                  |

![Accuracy Comparison](images/accuracy_comparison.png)

![Performance Difference](images/difference_plot.png)

## 5. Discussion

### 5.1 Performance Analysis
- **ILULR**: Our method significantly outperforms the SOTA (+15.0%). This benchmark has a short sequence length and small vocabulary; the shape–color feature set likely captured the underlying pattern effectively. The deterministic mapping (each unique sequence maps to a unique label) may be learned well by tree‑based models.
- **FDLOT & RHHQD**: Our accuracy lags behind SOTA by 4.9% and 14.5%, respectively. These benchmarks have longer sequences and larger vocabularies, suggesting more complex patterns that our generic feature engineering could not fully capture.
- **ZOBKB**: The largest gap (–42.7%) indicates that the published SOTA method exploits a pattern that our approaches miss entirely. The near‑perfect SOTA (95.2%) implies a simple rule (e.g., a parity check, a specific token at a specific position, or a global property of the sequence) that our models failed to discover.

### 5.2 Limitations of Our Approach
- **Feature engineering** was heuristic and may not match the true generative process of the benchmarks.
- **Small dataset sizes** (400 training samples) limit the capacity of complex models (e.g., LSTM) and encourage overfitting, as seen in ZOBKB where validation accuracy (59%) dropped sharply on test (41%).
- **Lack of domain knowledge**: The tokens likely represent shapes and colors, but the exact semantics are unknown. Without understanding the intended pattern, designing optimal features is challenging.

### 5.3 Insights on Benchmark Design
The wide variation in SOTA accuracies (60–95%) across benchmarks indicates that the suite contains tasks of fundamentally different difficulty. The high SOTA on ZOBKB suggests that some benchmarks are “toy” problems with trivial solutions, while others (FDLOT, RHHQD) are genuinely hard. This underscores the importance of benchmark selection when evaluating general‑purpose reasoning methods.

## 6. Conclusion

We selected four symbolic pattern reasoning benchmarks representing a spectrum of difficulty and scale. Our best method, based on shape–color feature engineering and Random Forests, achieved competitive performance on ILULR (outperforming SOTA by 15%) but fell short on the longer‑sequence benchmarks and especially on ZOBKB. The results highlight that generic machine‑learning models struggle to capture the precise symbolic rules underlying some of these tasks, while they can excel when the pattern aligns with the engineered features.

Future work could explore **program synthesis**, **rule‑learning algorithms**, or **attention‑based architectures** that might better capture the compositional patterns. Nevertheless, the SPR suite provides a valuable testbed for isolating benchmark choice from confounds such as popularity or data leakage, enabling a cleaner assessment of reasoning capabilities.

## Appendix: Code and Data
All analysis code is available in the `code/` directory. Intermediate results are stored in `outputs/`. The data files are read‑only in `data/`.
