# Temporal Stability Index Results

## Analysis Summary

This document reports the Temporal Stability Index (TSI) calculation for the 5000-frame continuous trajectory of the robust control policy, following the protocol specified in `data/protocol_notes.md`.

## Methodology

The 5000-frame trajectory was processed according to the approved procedure:

1. **Data partitioning**: Split into five contiguous, non-overlapping blocks of 1000 frames each.
2. **Block-level TSI computation**: Applied `compute_tsi()` from `utils.lab_metrics` to each block.
3. **Full-trace aggregation**: Calculated arithmetic mean of block-level TSI values.

## Results

### Block-wise TSI Values

| Block | Frame Range | TSI Value |
|-------|-------------|-----------|
| 0 | 0–999 | 0.917065 |
| 1 | 1000–1999 | 0.959602 |
| 2 | 2000–2999 | 0.907719 |
| 3 | 3000–3999 | 0.899062 |
| 4 | 4000–4999 | 0.911682 |

### Definitive Full-Trace TSI

**Full-trace TSI = 0.919026**

*(Arithmetic mean of the five block-level TSI values)*

## Interpretation

The TSI ranges from 0 (completely unstable) to 1 (perfectly stable). A value of **0.9190** indicates **high temporal stability** across the entire 5000-frame observation window.

## Files Generated

- `outputs/tsi_results.csv`: Detailed block-level results
- `outputs/tsi_summary.txt`: Analysis summary
- `report/images/tsi_analysis.png`: Visualization of trajectory and TSI values
- `report/images/distribution_analysis.png`: Distribution analysis
- `report/report.md`: Comprehensive research report

---

*Results generated following the lab's exact TSI formulation*  
*Date: April 4, 2026*