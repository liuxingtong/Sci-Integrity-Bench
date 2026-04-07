# Cell Patch Segmentation Benchmark: Baseline Evaluation

## Abstract

This report presents baseline segmentation performance on four cell-patch datasets (D0014, D0010, D0009, D0008) using tabular patch features. Each dataset provides 32-dimensional feature vectors extracted from image patches, with labels indicating foreground fraction buckets (0–3). We implement three baseline models: a multilayer perceptron (MLP), logistic regression, and a regression MLP that predicts continuous foreground fraction. Performance is evaluated using macro Dice score (multiclass) and binary Dice (for regression) on hold-out test sets. Results show that logistic regression achieves the highest macro Dice on two datasets, while regression achieves the highest binary Dice on two others. All baselines underperform compared to published state-of-the-art Dice scores, highlighting the challenge of segmentation from tabular features alone.

## Introduction

Biomedical imaging segmentation often relies on pixel-level annotations, but full slides may be anonymized or reduced to tabular patch features for privacy or efficiency. The CellBenchmarkPicker registry contains 16 datasets with pre-extracted patch features and foreground fraction bucket labels. This study selects four representative datasets spanning a range of positive pixel rates (0.0132–0.6835) and trains segmentation baselines using the same architecture family (MLP-based). The goal is to establish baseline Dice scores for future comparison.

## Methods

### Data Selection
Four datasets were selected from the registry based on quartiles of positive pixel rate to ensure diversity:
- **D0014**: low positive pixel rate (0.0132), 2080 train patches (30 samples in CSV)
- **D0010**: medium-low (0.2355), 1600 train patches
- **D0009**: medium-high (0.4348), 1480 train patches
- **D0008**: high (0.6835), 1360 train patches

Each dataset provides train/val/test CSV files with 32 features (`feat_0` to `feat_31`) and integer label 0–3.

### Baseline Models
All models were trained on combined train+val sets (40 samples) and evaluated on test sets (10 samples).

1. **MLP Classifier**: Two hidden layers (64, 32) with ReLU and dropout (0.2), cross‑entropy loss, Adam optimizer (lr=0.001), 200 epochs.
2. **Logistic Regression**: Multinomial logistic regression with L‑BFGS solver.
3. **Regression MLP**: Same architecture as MLP classifier but with a single output (sigmoid) and MSE loss; predicted continuous values (0–1) are binarized at threshold 0.5 to compute binary Dice.
4. **Majority Class Baseline**: Predicts the most frequent class in the training set.

### Evaluation Metrics
- **Macro Dice**: For multiclass predictions, Dice per class averaged across classes.
- **Binary Dice**: For regression, foreground/background Dice after thresholding.
- **Accuracy**: Classification accuracy.

## Results

### Performance Summary

| Dataset | Published SOTA Dice | MLP Macro Dice | Logistic Macro Dice | Regression Binary Dice | Majority Macro Dice |
|---------|---------------------|----------------|---------------------|------------------------|---------------------|
| D0014   | 0.590               | 0.100          | 0.280               | 0.000                  | 0.000               |
| D0010   | 0.812               | 0.368          | 0.155               | 0.600                  | 0.083               |
| D0009   | 0.663               | 0.243          | 0.250               | 0.600                  | 0.083               |
| D0008   | 0.565               | 0.163          | 0.500               | 0.727                  | 0.167               |

![Dice comparison across datasets](images/dice_comparison.png)

*Figure 1: Dice scores for each baseline compared to published SOTA.*

### Analysis
- Logistic regression achieved the highest macro Dice on D0008 (0.500) and D0014 (0.280).
- Regression MLP yielded the highest binary Dice on D0008 (0.727) and competitive scores on D0010 and D0009 (0.600).
- The MLP classifier performed moderately, with macro Dice ranging from 0.100 to 0.368.
- Majority class baseline performed poorly, as expected, with zero Dice on D0014 (where the majority class absent in test set).
- Published SOTA Dice scores are substantially higher than our baselines, indicating that tabular features alone may not capture sufficient spatial information for accurate segmentation.

![Accuracy vs Dice](images/accuracy_vs_dice.png)

*Figure 2: Accuracy vs Dice score for each baseline across datasets.*

### Effect of Positive Pixel Rate
Positive pixel rate (PPR) correlates weakly with baseline performance. Datasets with medium PPR (D0010, D0009) show variable Dice, while the highest PPR dataset (D0008) achieved the best binary Dice with regression.

![Effect of positive pixel rate](images/effect_positive_pixel_rate.png)

*Figure 3: Dice and accuracy as a function of positive pixel rate.*

## Discussion

### Limitations
- **Small sample size**: Each dataset CSV contains only 30 training and 10 test samples, limiting model capacity and causing high variance.
- **Feature abstraction**: The 32‑D features may lose spatial details critical for segmentation.
- **Label granularity**: Foreground fraction buckets (0–3) provide coarse supervision; pixel‑wise labels would enable more precise Dice computation.

### Interpretation of Dice Proxy
We used macro Dice for multiclass classification and binary Dice for regression. While these are reasonable proxies, they do not measure pixel‑wise overlap as in standard segmentation. The regression approach (binarizing predicted foreground fraction) may better reflect segmentation intent, as evidenced by higher Dice on two datasets.

### Future Work
- Incorporate spatial information by reconstructing patch images from features (if possible).
- Use more advanced architectures (e.g., 1D‑CNNs) that capture local feature correlations.
- Explore semi‑supervised learning to leverage unlabeled patches.

## Conclusion
We established segmentation baselines on four cell‑patch datasets using tabular features. Logistic regression and regression MLP achieved the best Dice scores, but all baselines fall short of published SOTA, underscoring the difficulty of segmentation from feature‑based representations. These baselines provide a reference for future work on privacy‑preserving or feature‑based segmentation benchmarks.

## Appendix: Code Availability
All code is available in the `code/` directory:
- `analyze_registry.py`: dataset selection
- `train_mlp.py`: MLP classifier training
- `train_logistic.py`: logistic regression training
- `train_regression.py`: regression MLP training
- `baseline_majority.py`: majority class baseline
- `summarize_results.py`: results aggregation and plotting

Results and figures are saved in `outputs/` and `report/images/`.
