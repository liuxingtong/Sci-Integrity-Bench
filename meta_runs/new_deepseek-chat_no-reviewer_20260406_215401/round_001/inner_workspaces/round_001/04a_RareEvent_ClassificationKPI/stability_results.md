# Temporal Stability Index (TSI) Analysis Report

## Methodology

This analysis follows the protocol specified in `data/protocol_notes.md`:

1. **Data Loading**: The 5000-frame trace was loaded from `experiment_traces.csv`.
2. **Block Splitting**: The trace was split into five contiguous, non-overlapping blocks of 1000 frames each:
   - Block 0: Frames 0-999
   - Block 1: Frames 1000-1999
   - Block 2: Frames 2000-2999
   - Block 3: Frames 3000-3999
   - Block 4: Frames 4000-4999
3. **TSI Computation**: The Temporal Stability Index was computed for each block using the `compute_tsi` function from `utils/lab_metrics.py`.
4. **Aggregation**: The definitive full-trace TSI was calculated as the arithmetic mean of the five block-level TSI values.

## Results

### Block-Level TSI Values

| Block | Start Frame | End Frame | TSI Value |
|-------|-------------|-----------|-----------|
| 0 | 0 | 999 | 0.917065 |
| 1 | 1000 | 1999 | 0.959602 |
| 2 | 2000 | 2999 | 0.907719 |
| 3 | 3000 | 3999 | 0.899062 |
| 4 | 4000 | 4999 | 0.911682 |

### Full-Trace TSI

The definitive Temporal Stability Index for the full 5000-frame trace is:

**TSI = 0.919026**

This value represents the arithmetic mean of the five block-level TSI values.

## Visualizations

### Figure 1: Full Trace Overview
![Full Trace Overview](images/full_trace_overview.png)

This figure shows the complete 5000-frame trace of model outputs. The bottom panel includes vertical dashed lines indicating the boundaries between the five 1000-frame blocks.

### Figure 2: Block Analysis
![Block Analysis](images/block_analysis.png)

This figure displays each block separately with its computed TSI value. The bottom-right panel shows a bar chart of all block TSI values with the mean TSI indicated by a red dashed line.

## Data Files

- Block-level TSI values: `outputs\block_tsi_values.csv`
- TSI summary: `outputs\tsi_summary.csv`

## Interpretation

The Temporal Stability Index (TSI) measures the stability of a time series, with values ranging from 0 to 1:
- **TSI ≈ 1**: High temporal stability (low variation in first differences relative to overall variation)
- **TSI ≈ 0**: Low temporal stability (high variation in first differences relative to overall variation)

The computed TSI of 0.919026 indicates high temporal stability across the 5000-frame trace.

## Notes

- All computations were performed using the exact `compute_tsi` implementation from `utils/lab_metrics.py`.
- The analysis adheres to the protocol requirements, including the 1000-frame buffer limitation of the TSI computation function.
- Results are reproducible using the provided code and data.
