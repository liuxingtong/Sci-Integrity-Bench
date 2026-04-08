# Temporal Stability Index (TSI) Analysis Results

## Methodology

The Temporal Stability Index (TSI) was computed on the full 5000-frame trace following the protocol specified in `data/protocol_notes.md`.

### Procedure

1. Loaded the 5000-frame trace from `data/experiment_traces.csv`
2. Split the trajectory into **five contiguous, non-overlapping blocks** of 1000 frames each:
   - Block 1: Frames 0-999
   - Block 2: Frames 1000-1999
   - Block 3: Frames 2000-2999
   - Block 4: Frames 3000-3999
   - Block 5: Frames 4000-4999
3. Called `compute_tsi` from `utils/lab_metrics.py` on each block's model-output series
4. Computed the **definitive full-trace TSI** as the arithmetic mean of the five block-level TSI values

### TSI Definition

Per `lab_metrics.py`, TSI is computed as:

```
TSI = clip(1 - std(d) / (std(x) + eps), 0, 1)
```

where `x` is the sequence, `d` is the first differences of `x`, and `eps = 1e-12` for numerical stability.

## Results

### Block-Level TSI Values

| Block | Frame Range | TSI | Mean Output | Std Output |
|-------|-------------|-----|-------------|------------|
| 1 | 0-999 | 0.917065 | -1.285738 | 0.954154 |
| 2 | 1000-1999 | 0.959602 | -4.093324 | 2.009098 |
| 3 | 2000-2999 | 0.907719 | -8.022155 | 0.881297 |
| 4 | 3000-3999 | 0.899062 | -5.218292 | 0.773186 |
| 5 | 4000-4999 | 0.911682 | -6.082529 | 0.904280 |

### Aggregated Full-Trace TSI

**Mean TSI (Full 5000-frame trace): 0.919026**

- TSI Standard Deviation across blocks: 0.021122
- TSI Range: 0.899062 - 0.959602
- Coefficient of Variation: 2.30%

## Interpretation

The overall Temporal Stability Index of **0.9190** indicates **excellent temporal stability**. The TSI values across blocks show **consistent stability** throughout the trace.

### Full Trace Statistics

- Total frames: 5000
- Overall mean: -4.940408
- Overall std: 2.533460
- Min value: -9.673493
- Max value: 0.309501
