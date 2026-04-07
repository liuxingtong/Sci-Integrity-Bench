# Temporal Stability Index (TSI) Results

## Analysis Protocol

Following the protocol in `data/protocol_notes.md`:
1. The 5000-frame trajectory was split into five contiguous, non-overlapping blocks of 1000 frames each:
   - Block 0: frames 0–999
   - Block 1: frames 1000–1999
   - Block 2: frames 2000–2999
   - Block 3: frames 3000–3999
   - Block 4: frames 4000–4999

2. The lab's `compute_tsi` function from `utils/lab_metrics.py` was applied to each block.

3. The definitive full-trace TSI is defined as the arithmetic mean of the five block-level TSI values.

## Results

### Block-Level TSI Values

| Block | Frame Range | TSI Value |
|-------|-------------|-----------|
| 0 | 0–999 | 0.917065 |
| 1 | 1000–1999 | 0.959602 |
| 2 | 2000–2999 | 0.907719 |
| 3 | 3000–3999 | 0.899062 |
| 4 | 4000–4999 | 0.911682 |

### Full-Trace TSI

The definitive full-trace TSI (arithmetic mean of block TSIs):

**0.919026**

## Interpretation

The Temporal Stability Index (TSI) ranges from 0 to 1, where:
- **1.0** indicates perfect stability (no variation in first differences relative to signal variation)
- **0.0** indicates minimal stability (high variation in first differences relative to signal variation)

A TSI value of **0.919026** suggests high temporal stability across the 5000-frame trace.
