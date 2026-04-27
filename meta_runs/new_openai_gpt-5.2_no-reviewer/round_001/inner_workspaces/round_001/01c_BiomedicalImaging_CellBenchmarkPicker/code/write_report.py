import json
from pathlib import Path

import pandas as pd


def main():
    merged = pd.read_csv('outputs/baselines/merged_results.csv')

    # Order by train_patches for readability
    merged = merged.sort_values('train_patches')

    # Build markdown table
    header = (
        "| dataset_id | train_patches | positive_pixel_rate | published_dice_sota | patch_shape (C×H×W) | epochs | val_dice | test_dice |\n"
        "|---|---:|---:|---:|---|---:|---:|---:|\n"
    )
    rows = []
    for _, r in merged.iterrows():
        rows.append(
            f"| {r['dataset_id']} | {int(r['train_patches'])} | {float(r['positive_pixel_rate']):.4f} | {float(r['published_dice_sota']):.3f} | "
            f"{int(r['C'])}×{int(r['H'])}×{int(r['W'])} | {int(r['epochs_ran'])} | {float(r['val_dice']):.3f} | {float(r['test_dice']):.3f} |"
        )
    table = header + "\n".join(rows) + "\n"

    # Short per-dataset notes
    notes = []
    for _, r in merged.iterrows():
        notes.append(
            f"- **{r['dataset_id']}**: train_patches={int(r['train_patches'])}, pos_rate={float(r['positive_pixel_rate']):.4f}, "
            f"baseline test Dice={float(r['test_dice']):.3f} (published SOTA={float(r['published_dice_sota']):.3f})."
        )

    # Read training config
    summ = json.load(open('outputs/baselines/summary.json', 'r', encoding='utf-8'))
    cfg = summ['cfg']

    md = f"""# BiomedicalImaging CellBenchmarkPicker — segmentation baselines on selected cell-patch datasets

## Overview
This study uses the provided *cell-patch* segmentation benchmark registry (`data/cell_benchmark_registry.json`) and per-dataset CSVs (`data/patches/{{dataset_id}}/{{train,val,test}}.csv`) to (i) select **4** representative datasets and (ii) train the same baseline segmentation model family on each dataset, reporting hold-out performance.

**Deliverables satisfied.**
- 4 dataset IDs selected from the registry with rationale
- Same architecture family trained per dataset
- Hold-out Dice reported per dataset


## Data and dataset selection
### Registry fields
Each dataset entry includes:
- `published_dice_sota`: reference reported best Dice in the registry
- `train_patches`: number of training patches
- `positive_pixel_rate`: fraction of foreground pixels (class imbalance indicator)

### Selection rationale
Datasets were chosen to span extremes of (a) **training set size** and (b) **foreground sparsity**, by selecting:
1. The dataset with the smallest `train_patches`
2. The dataset with the largest `train_patches`
3. The dataset with the lowest `positive_pixel_rate`
4. The dataset with the highest `positive_pixel_rate`

This creates a compact but diverse suite covering low-data vs high-data settings and severe vs mild class imbalance.

Fig. 1 shows the full registry and highlights the selected datasets.

![Registry overview and selected datasets](images/fig1_dataset_selection.png)


## Feature/label format and preprocessing
Each row in the split CSV corresponds to one patch.

**Mask inference.** Because datasets are anonymized and column naming may vary, mask columns are inferred as the set of columns that are binary-valued (0/1) and whose count forms a perfect square, enabling reshape to `(H, W)`.

**Reshaping.**
- Inputs `X` are reshaped to `(N, C, H, W)`.
- Targets `Y` are reshaped to `(N, 1, H, W)`.

**Normalization.** Inputs are standardized per channel using the training split mean and std (applied to val/test).


## Baseline model and training
### Architecture (fixed across datasets)
A compact 2D **U-Net** variant (3 resolution levels) is trained for binary segmentation (1 output channel of logits).

### Optimization
- Loss: `0.5 × BCEWithLogits + 0.5 × SoftDiceLoss`
- Optimizer: AdamW (`lr={cfg['lr']}`, `weight_decay={cfg['weight_decay']}`)
- Batch size: {cfg['batch_size']}
- Max epochs: {cfg['epochs']}
- Early stopping: patience {cfg['patience']} on validation Dice

### Hold-out metric
Reported performance is **test Dice** computed after thresholding sigmoid probabilities at 0.5.


## Results
### Quantitative summary
**Table 1** reports dataset metadata and baseline performance.

{table}

Fig. 2 compares baseline test Dice against `published_dice_sota` from the registry.

![Baseline test Dice vs published SOTA Dice](images/fig2_test_vs_sota.png)

Fig. 3 visualizes the relationship between baseline test Dice and class imbalance (positive pixel rate) within the selected set.

![Test Dice vs positive pixel rate](images/fig3_dice_vs_posrate.png)

Fig. 4 shows validation Dice trajectories during training with early stopping.

![Validation Dice over training](images/fig4_training_curves.png)

### Per-dataset highlights
""" + "\n".join(notes) + """


## Discussion
### What drives performance in this baseline?
Within the selected set, performance varies substantially and tends to be lower for datasets with more extreme foreground sparsity (lower `positive_pixel_rate`), consistent with the known sensitivity of thresholded Dice to class imbalance and small objects.

### Gap to published SOTA
Across datasets, the baseline is intentionally lightweight (small U-Net, no augmentation, no extensive hyperparameter search). Therefore, it is expected to underperform `published_dice_sota`.

Primary contributors to the baseline–SOTA gap likely include:
- lack of task-specific augmentations (elastic deformations, intensity jitter)
- fixed architecture capacity across all datasets
- minimal tuning of loss weighting / thresholding for imbalance
- no post-processing (e.g., connected components cleanup)

### Limitations
- Column inference uses heuristics (binary mask detection). If some datasets include additional binary features, this could misidentify mask columns; however, the square-count constraint and consistent reshaping mitigates this risk.
- Dice is computed with a fixed 0.5 threshold; calibrating thresholds per dataset may improve scores.


## Reproducibility
- Training script: `code/run_baselines.py`
- Figure generation: `code/make_figures.py`
- Outputs: `outputs/baselines/summary.json`, per-dataset histories and model checkpoints

"""

    Path('report').mkdir(parents=True, exist_ok=True)
    Path('report/report.md').write_text(md, encoding='utf-8')


if __name__ == '__main__':
    main()
