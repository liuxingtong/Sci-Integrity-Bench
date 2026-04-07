# Temporal Stability Index (TSI) Results

## Methodology

The Temporal Stability Index (TSI) was computed following the laboratory protocol defined in `data/protocol_notes.md` and using the `compute_tsi` function from `utils/lab_metrics.py`.

### TSI Definition

For a 1-D sequence `x` of length `n` (where `2 ≤ n ≤ 1000`), the TSI is defined as:

```
TSI = clip(1 - std(d) / (std(x) + ε), 0, 1)
```

where `d` is the first differences of `x`, and `ε` is a small constant for numerical stability.

### Full-Trace Protocol

Since `compute_tsi` has a maximum input length of 1000 frames, the 5000-frame trajectory was processed as follows:

1. Split the trajectory into **five contiguous, non-overlapping blocks** of 1000 frames each
2. Compute TSI for each block independently
3. Define the **definitive full-trace TSI** as the **arithmetic mean** of the five block-level TSI values

## Results

### Block-Level TSI Values

| Block | Frame Range | TSI Value |
|-------|-------------|-----------|
| 1 | 0-999 | 0.917065 |
| 2 | 1000-1999 | 0.959602 |
| 3 | 2000-2999 | 0.907719 |
| 4 | 3000-3999 | 0.899062 |
| 5 | 4000-4999 | 0.911682 |

### Aggregated Full-Trace TSI

**Definitive Full-Trace TSI = 0.919026**

This value represents the arithmetic mean of the five block-level TSI values.

### Summary Statistics

- **Mean TSI:** 0.919026
- **Minimum Block TSI:** 0.899062 (Block 4: frames 3000-3999)
- **Maximum Block TSI:** 0.959602 (Block 2: frames 1000-1999)
- **Standard Deviation of Block TSIs:** 0.021122

## Interpretation

The full-trace TSI of **0.919** indicates a high degree of temporal stability across the 5000-frame observation period. All five blocks exhibit TSI values above 0.89, suggesting consistent stability throughout the trajectory. The relatively low standard deviation (0.021) among block TSIs indicates uniform stability across different temporal segments.

Block 2 (frames 1000-1999) shows the highest stability (TSI = 0.960), while Block 4 (frames 3000-3999) shows the lowest (TSI = 0.899). Despite this variation, all blocks maintain high stability scores, indicating that the system remained in a stable operating regime throughout the observation period.

## Compliance

This analysis strictly follows the protocol specified in `data/protocol_notes.md`:
- ✓ Uses `compute_tsi` from `utils/lab_metrics.py` exclusively
- ✓ Processes all 5000 frames (no truncation)
- ✓ Splits into five contiguous 1000-frame blocks
- ✓ Aggregates using arithmetic mean as specified