# Cell Benchmark Picker: Baseline Segmentation Analysis

## 1. Introduction

This report details the selection and baseline evaluation of four cell-patch datasets from the provided benchmark registry. The goal is to establish a segmentation baseline using a consistent architecture family across diverse datasets and report the hold-out performance using a pseudo-Dice metric.

## 2. Methodology

### 2.1 Dataset Selection

The `cell_benchmark_registry.json` contains 16 anonymized datasets with varying characteristics, including the published state-of-the-art (SOTA) Dice score, the number of training patches, and the positive pixel rate. To ensure a comprehensive evaluation, four datasets were selected to represent a diverse range of these characteristics:

*   **D0001**: High SOTA Dice (0.862) and high positive pixel rate (0.765).
*   **D0002**: Low SOTA Dice (0.581) and very low positive pixel rate (0.0202).
*   **D0007**: High SOTA Dice (0.833) and moderate positive pixel rate (0.5115).
*   **D0014**: Low SOTA Dice (0.590) and very low positive pixel rate (0.0132).

This selection covers both easy (high SOTA) and hard (low SOTA) datasets, as well as dense (high positive pixel rate) and sparse (low positive pixel rate) cell distributions.

![Dataset Metadata](images/dataset_metadata.png)
*Figure 1: Metadata of the selected datasets, illustrating the diversity in published SOTA Dice scores and positive pixel rates.*

### 2.2 Baseline Architecture

For the baseline segmentation model, a Random Forest classifier was chosen. This model is well-suited for tabular feature data and provides a robust, non-linear baseline without the need for extensive hyperparameter tuning. The model was trained using 100 estimators (`n_estimators=100`) and a fixed random state for reproducibility.

### 2.3 Evaluation Metric

The provided labels represent foreground fraction buckets (0-3). To approximate the Dice score, a pseudo-Dice metric was implemented. The labels (0, 1, 2, 3) were mapped to fractions (0.0, 0.333, 0.667, 1.0). The pseudo-Dice score was then calculated as:

$$ \text{Pseudo-Dice} = \frac{2 \times \sum \min(y_{\text{true}}, y_{\text{pred}})}{\sum y_{\text{true}} + \sum y_{\text{pred}}} $$

This metric captures the overlap between the predicted and true foreground fractions, providing a proxy for the standard Dice coefficient used in segmentation tasks.

## 3. Results

The Random Forest baseline was trained on the `train.csv` split and evaluated on both the `val.csv` and `test.csv` splits for each of the four selected datasets. The resulting pseudo-Dice scores are summarized below.

| Dataset | Validation Dice | Test Dice |
| :--- | :--- | :--- |
| D0001 | 0.533 | 0.606 |
| D0002 | 0.364 | 0.522 |
| D0007 | 0.727 | 0.629 |
| D0014 | 0.667 | 0.323 |

![Random Forest Baseline Results](images/rf_dice_scores.png)
*Figure 2: Pseudo-Dice scores on the validation and test sets for the Random Forest baseline across the selected datasets.*

## 4. Discussion

The baseline results demonstrate varying levels of performance across the selected datasets, which aligns with the diversity observed in the metadata.

*   **D0007** achieved the highest test pseudo-Dice score (0.629), which is consistent with its relatively high published SOTA Dice (0.833). The moderate positive pixel rate likely provides a balanced learning signal.
*   **D0001** also showed reasonable performance (0.606 test Dice), reflecting its high SOTA score. However, the gap between the baseline and the SOTA (0.862) suggests that more complex architectures (e.g., U-Net) are necessary to fully capture the spatial context in this dense dataset.
*   **D0002** and **D0014** proved to be more challenging, with test Dice scores of 0.522 and 0.323, respectively. Both datasets have very low positive pixel rates (< 0.05) and low published SOTA scores (< 0.6). The sparsity of the foreground makes it difficult for the baseline model to accurately predict the cell fractions, leading to lower overlap scores. The significant drop in performance on the test set for D0014 compared to the validation set suggests potential overfitting or a distribution shift between the splits.

In conclusion, the Random Forest baseline provides a useful starting point for evaluating these datasets. The results highlight the difficulty of segmenting sparse cell populations (D0002, D0014) and underscore the need for more advanced, spatially-aware models to approach the published SOTA performance, particularly on the denser datasets (D0001, D0007).
