# Research Report: Variable Star Classification using Symbolic Encodings of Light-Curve Structure

## Executive Summary

This research aimed to classify variable vs non-variable stars using symbolic encodings of light-curve structure. Despite implementing multiple feature extraction methods and machine learning models, the best achieved balanced accuracy was 0.4724 on the test set, which falls significantly short of the baseline performance of 0.78. This report documents the methodology, experiments, results, and analysis of this classification task.

## 1. Introduction

Time-domain astronomy surveys generate vast amounts of light curve data that require automated classification. Symbolic encodings provide a compact representation of light-curve structure that can facilitate variable source screening. This task involves binary classification of astronomical sources as variable (1) or non-variable (0) based on fixed-length symbolic sequences.

### 1.1 Task Description
- **Input**: Symbolic sequences of length 40, composed of 8 unique symbols: {w, ., *, x, z, v, y, u}
- **Output**: Binary classification (0 = non-variable, 1 = variable)
- **Data splits**: Training (500 samples), Validation (150 samples), Test (150 samples)
- **Baseline performance**: Balanced accuracy ≈ 0.78
- **Evaluation metric**: Balanced accuracy (primary), accuracy, AUC

## 2. Data Exploration

### 2.1 Dataset Characteristics
- **Training set**: 500 samples (257 variable, 243 non-variable)
- **Validation set**: 150 samples (79 variable, 71 non-variable)
- **Test set**: 150 samples (76 variable, 74 non-variable)
- **Sequence length**: Fixed at 40 symbols for all samples
- **Symbol alphabet**: 8 unique symbols with relatively uniform distribution
- **Field IDs**: 5 different fields with uneven distribution

### 2.2 Symbol Distribution Analysis
Symbol frequencies were remarkably similar between classes, with no single symbol showing strong discriminative power:

| Symbol | Variable Freq | Non-variable Freq | Difference |
|--------|---------------|-------------------|------------|
| *      | 0.1206        | 0.1261            | -0.0055    |
| .      | 0.1332        | 0.1286            | 0.0046     |
| u      | 0.1302        | 0.1293            | 0.0008     |
| v      | 0.1241        | 0.1233            | 0.0009     |
| w      | 0.1209        | 0.1258            | -0.0049    |
| x      | 0.1231        | 0.1220            | 0.0010     |
| y      | 0.1216        | 0.1211            | 0.0005     |
| z      | 0.1264        | 0.1238            | 0.0026     |

### 2.3 Pattern Analysis
Bigram and trigram analysis revealed subtle differences between classes:

**Top discriminative bigrams**:
- More common in non-variable: 'wu', 'y*', 'xw', 'yz', '**'
- More common in variable: '.z', 'w.', 'yu', 'zz', 'yx'

**Common 3-symbol patterns**:
- Variable stars: 'zv.', '.*v', 'vw.', 'z.u', 'v.u'
- Non-variable stars: 'u.x', '.yz', 'wu.', '*wu', 'wu*'

## 3. Methodology

### 3.1 Feature Extraction Approaches
Four distinct feature extraction methods were implemented:

#### 3.1.1 Basic Symbolic Features
- Symbol frequencies and counts
- Transition probability matrices (8×8)
- N-gram frequencies (bigrams)
- Information-theoretic features (entropy, complexity)
- Pattern-based features (repetitions, longest runs)

**Total features**: 219

#### 3.1.2 Advanced Symbolic Dynamics Features
- Statistical features (mean, std, skewness, kurtosis)
- Transition matrix properties (entropy, symmetry)
- Recurrence quantification features
- Pattern and motif discovery
- Symbolic dynamics measures
- Lempel-Ziv complexity approximation

**Total features**: 45

#### 3.1.3 N-gram Features
- Character n-grams (n=2-4) using CountVectorizer
- Limited to top 500 most frequent n-grams
- Both presence and frequency features

#### 3.1.4 Pattern-Based Features
- Presence/absence of discriminative patterns identified in analysis
- Count and density of class-specific patterns
- Combined variable and non-variable patterns

### 3.2 Machine Learning Models
Multiple classification algorithms were evaluated:
- Random Forest (100-200 trees, max depth 10-20)
- Gradient Boosting (100 trees, learning rate 0.01-0.1)
- Logistic Regression (L2 regularization)
- Support Vector Machine (linear and RBF kernels)
- Multi-layer Perceptron (1-2 hidden layers)
- Ensemble methods (Voting and Stacking classifiers)

### 3.3 Experimental Setup
- **Feature selection**: SelectKBest (ANOVA F-test) or RFE
- **Feature scaling**: StandardScaler
- **Validation**: Separate validation set (150 samples)
- **Hyperparameter tuning**: Grid search with 5-fold CV
- **Final evaluation**: Test set (150 samples)

## 4. Results

### 4.1 Performance Summary

| Model | Features | Validation Bal. Acc | Test Bal. Acc | Test Accuracy | Gap to Baseline |
|-------|----------|---------------------|---------------|---------------|-----------------|
| Basic + RF | 50 selected | 0.5411 | 0.4726 | 0.4733 | 0.3074 |
| Advanced + GB | 18 selected | 0.5756 | 0.5132 | 0.5133 | 0.2668 |
| N-gram + RF | 500 n-grams | 0.5509 | 0.4780 | 0.4800 | 0.3020 |
| Pattern + GB | 150 features | 0.5756 | 0.5132 | 0.5133 | 0.2668 |
| Ensemble + RF | 100 selected | 0.4724 | 0.4724 | 0.4733 | 0.3076 |
| **Baseline** | **Unknown** | **N/A** | **0.7800** | **N/A** | **0.0000** |

*Figure: `summary_figure.png` provides a visual summary of all experiments and performance gaps.*

### 4.2 Best Model Performance
The best performing model was a Gradient Boosting classifier with advanced symbolic features, achieving:
- **Balanced accuracy**: 0.5132
- **Accuracy**: 0.5133
- **AUC**: 0.5059

**Confusion Matrix**:
```
              Predicted 0  Predicted 1
Actual 0          30          44
Actual 1          29          47
```

**Classification Report**:
```
              precision    recall  f1-score   support
Non-variable       0.51      0.41      0.45        74
    Variable       0.52      0.62      0.56        76
    accuracy                           0.51       150
   macro avg       0.51      0.51      0.51       150
weighted avg       0.51      0.51      0.51       150
```

### 4.3 Feature Importance Analysis
Top features from the best model included:
1. Pattern density features (v., *z, uw, yz, yx)
2. Pattern count features (vw, yv, u.., xw, u.)
3. Symbol distribution statistics (skewness, kurtosis)
4. Transition entropy and symmetry

## 5. Discussion

### 5.1 Performance Gap Analysis
The significant gap between achieved performance (0.51) and baseline (0.78) suggests:

1. **Insufficient feature representation**: The extracted features may not capture the essential patterns in the symbolic sequences that distinguish variable from non-variable stars.

2. **Missing domain knowledge**: The symbolic encoding likely represents specific light-curve characteristics (slope, curvature, periodicity) that require domain-specific interpretation.

3. **Complex patterns**: The discriminative patterns may be longer or more complex than the n-grams and motifs captured in this analysis.

4. **Temporal dependencies**: The fixed-length sequences may encode temporal patterns that require sequence modeling approaches (LSTM, CNN) rather than static feature extraction.

### 5.2 Limitations of Current Approach
1. **Static feature extraction**: Treating sequences as bags of patterns ignores temporal ordering and dependencies.
2. **Limited pattern length**: Maximum n-gram length of 4 may miss longer discriminative patterns.
3. **No domain adaptation**: Features were not tailored to astronomical light-curve characteristics.
4. **Small dataset**: 650 training samples may be insufficient for complex pattern learning.

### 5.3 Potential Improvements
1. **Sequence modeling**: Implement LSTM or Transformer models to capture temporal dependencies.
2. **Domain-specific features**: Incorporate astronomical knowledge about light-curve characteristics.
3. **Alternative encodings**: Explore different symbolic representations or embeddings.
4. **Data augmentation**: Generate synthetic sequences to increase training data.
5. **Ensemble of specialists**: Combine models trained on different feature representations.

## 6. Conclusion

This research implemented multiple feature extraction and machine learning approaches for variable star classification using symbolic encodings. Despite comprehensive experimentation, the achieved performance (0.51 balanced accuracy) fell significantly short of the baseline (0.78). The results suggest that the symbolic sequences encode complex patterns that require more sophisticated modeling approaches or domain-specific feature engineering.

### Key Findings:
1. Symbol frequencies alone are not discriminative between classes.
2. Bigram and trigram patterns show subtle but insufficient differences.
3. Advanced symbolic dynamics features provided the best performance but remained below baseline.
4. Ensemble methods did not improve performance over individual models.

### Recommendations for Future Work:
1. Investigate the specific symbolic encoding scheme used to generate the sequences.
2. Implement deep learning approaches (LSTM, CNN) for sequence classification.
3. Incorporate astronomical domain knowledge in feature design.
4. Explore unsupervised pre-training or representation learning.

## 7. References

1. Lin, J., Keogh, E., Lonardi, S., & Chiu, B. (2003). A symbolic representation of time series, with implications for streaming algorithms.
2. Nun, I., Pichara, K., Protopapas, P., & Kim, D. W. (2015). Supervised detection of anomalous light curves in massive astronomical catalogs.
3. Richards, J. W., Starr, D. L., Butler, N. R., Bloom, J. S., Brewer, J. M., Crellin, M., ... & Rischard, M. (2011). On machine-learned classification of variable stars with sparse and noisy time-series data.

## Appendix: Figures

All figures are saved in the `report/images/` directory:

1. `label_distribution.png` - Class distribution across datasets
2. `symbol_length_distribution.png` - Sequence length distribution
3. `symbol_frequency_comparison.png` - Symbol frequencies by class
4. `bigram_frequency_comparison.png` - Top discriminative bigrams
5. `complexity_comparison.png` - Sequence complexity measures
6. `model_performance_advanced.png` - Advanced model performance
7. `ngram_model_performance.png` - N-gram model performance
8. `pattern_model_performance.png` - Pattern-based model performance
9. `ngram_range_comparison.png` - N-gram range comparison
10. `final_model_performance.png` - Final ensemble model performance
11. `sequence_visualization.png` - Sample sequence visualizations
12. `positional_symbol_frequencies.png` - Symbol frequencies by position
13. `summary_figure.png` - Summary of all experiments and performance gaps

## Code Availability

All analysis code is available in the `code/` directory:
- `explore_data.py` - Data exploration and visualization
- `feature_extraction.py` - Basic feature extraction
- `advanced_features.py` - Advanced symbolic dynamics features
- `build_model.py` - Model building with basic features
- `build_model_advanced.py` - Model building with advanced features
- `pattern_analysis.py` - Pattern discovery and analysis
- `ngram_model.py` - N-gram based classification
- `pattern_based_model.py` - Pattern-based classification
- `sequence_visualization.py` - Sequence visualization
- `final_ensemble_model.py` - Final ensemble model

Trained models and feature extractors are saved in the `outputs/` directory.