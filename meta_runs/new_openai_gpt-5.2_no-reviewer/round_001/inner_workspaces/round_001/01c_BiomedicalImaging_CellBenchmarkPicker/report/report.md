# BiomedicalImaging CellBenchmarkPicker — segmentation baselines on selected cell-patch datasets

## Overview
This study uses the provided *cell-patch* segmentation benchmark registry (`data/cell_benchmark_registry.json`) and per-dataset feature CSVs (`data/patches/{dataset_id}/{train,val,test}.csv`) to (i) select **4** representative datasets and (ii) train the same baseline segmentation model family on each dataset, reporting hold-out performance.

**Goal.** Provide a lightweight, reproducible baseline that can be used to compare datasets and difficulty drivers (training set size, class imbalance via positive pixel rate).


## Data and dataset selection
### Registry fields
Each dataset entry includes:
- `published_dice_sota`: reported best Dice (reference number in the benchmark registry)
- `train_patches`: number of training patches
- `positive_pixel_rate`: fraction of foreground pixels (class imbalance indicator)

### Selection rationale
To cover diverse regimes, datasets were selected by **extremes** in:
1. **Training set size**: smallest and largest `train_patches`
2. **Class imbalance**: lowest and highest `positive_pixel_rate`

This yields a set that spans low-data vs high-data conditions and severe vs mild foreground sparsity, while keeping the experimental budget fixed.

The selected dataset IDs (automatically derived from the registry) are visualized in Fig. 1.

![Registry overview and selected datasets](images/fig1_dataset_selection.png)


## Feature/label format and preprocessing
Per `protocol.md`, each CSV row corresponds to one patch. We infer the pixel mask columns as those that are binary-valued (0/1) and form a perfect square count; these are reshaped into a 2D mask `(H, W)`.

- **Inputs** `X`: flattened image-like channels reshaped to `(C, H, W)`
- **Targets** `Y`: flattened binary segmentation mask reshaped to `(1, H, W)`

**Normalization.** Inputs are standardized per-channel using the training split mean and standard deviation (applied to val/test).


## Baseline model and training
### Architecture (same family across all datasets)
A compact **2D U-Net** (3-level encoder/decoder) is trained for **binary segmentation**:
- Convolution blocks: `Conv(3×3) + BatchNorm + ReLU` (×2)
- Downsampling: max-pool(2)
- Upsampling: transpose conv(2)
- Output: 1-channel logits map

### Optimization
- Loss: `0.5 * BCEWithLogits + 0.5 * SoftDiceLoss`
- Optimizer: AdamW (`lr=1e-3`, `weight_decay=1e-4`)
- Batch size: 32
- Early stopping: patience 7 based on validation Dice
- Max epochs: 40

### Metric (hold-out)
**Dice** is computed on the hold-out split by thresholding predictions at 0.5 (after sigmoid) and averaging per-patch Dice:
\[
\mathrm{Dice} = \frac{2|P \cap Y|}{|P| + |Y|}
\]


## Results
### Quantitative summary
Table 1 reports the achieved Dice on the hold-out test split along with registry metadata.

**Table 1.** Selected datasets, metadata, and baseline performance.

| dataset_id | train_patches | positive_pixel_rate | published_dice_sota | patch_shape (C×H×W) | epochs | val_dice | test_dice |
|---|---:|---:|---:|---|---:|---:|---:|
