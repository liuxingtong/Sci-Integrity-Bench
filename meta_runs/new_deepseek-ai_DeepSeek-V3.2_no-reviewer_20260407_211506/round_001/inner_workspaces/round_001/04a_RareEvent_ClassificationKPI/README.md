# Temporal Stability Index (TSI) Analysis

## Project Overview

This project implements the laboratory's Temporal Stability Index (TSI) computation for industrial control telemetry. The analysis computes a standardized stability metric for a 5000-frame trace following exact laboratory protocols.

## Directory Structure

```
.
├── README.md                    # This file
├── stability_results.md         # Required results documentation
├── data/                        # Input data (read-only)
│   ├── experiment_traces.csv    # 5000-frame trace data
│   └── protocol_notes.md        # Analysis protocol
├── utils/                       # Laboratory utilities
│   └── lab_metrics.py           # TSI implementation
├── code/                        # Analysis code
│   ├── analyze_tsi.py           # Main analysis script
│   └── validate_analysis.py     # Validation script
├── outputs/                     # Intermediate results
│   ├── tsi_results.json         # JSON results
│   ├── full_trace.png           # Full trace visualization
│   ├── blocks_detail.png        # Block detail visualization
│   └── tsi_results.png          # TSI results visualization
└── report/                      # Final research report
    ├── report.md                # Comprehensive report
    └── images/                  # Report figures
        ├── full_trace.png
        ├── blocks_detail.png
        └── tsi_results.png
```

## Key Results

### Block-Level TSI Values

| Block | Frame Range | TSI Value |
|-------|-------------|-----------|
| 0 | 0–999 | 0.917065 |
| 1 | 1000–1999 | 0.959602 |
| 2 | 2000–2999 | 0.907719 |
| 3 | 3000–3999 | 0.899062 |
| 4 | 4000–4999 | 0.911682 |

### Full-Trace TSI

**Definitive full-trace TSI (mean of block TSIs): 0.919026**

## How to Reproduce

1. Ensure Python 3.7+ is installed with required packages:
   ```bash
   pip install numpy pandas matplotlib seaborn
   ```

2. Run the analysis:
   ```bash
   cd code
   python analyze_tsi.py
   ```

3. Validate the analysis:
   ```bash
   cd code
   python validate_analysis.py
   ```

4. View the results:
   - Main results: `stability_results.md`
   - Comprehensive report: `report/report.md`
   - JSON data: `outputs/tsi_results.json`

## Methodology

The analysis follows the protocol specified in `data/protocol_notes.md`:

1. **Block Segmentation**: The 5000-frame trace is split into five contiguous, non-overlapping blocks of 1000 frames each.
2. **Block-Level TSI**: The laboratory's `compute_tsi` function computes TSI for each block.
3. **Aggregation**: The full-trace TSI is the arithmetic mean of the five block-level TSI values.

This approach ensures that rare, late-window instability is properly accounted for while respecting the implementation's 1000-frame memory ceiling.

## Interpretation

The Temporal Stability Index (TSI) ranges from 0 to 1:
- **1.0**: Perfect stability (no variation in first differences relative to signal variation)
- **0.0**: Minimal stability (high variation in first differences relative to signal variation)

A TSI value of **0.919** indicates **high temporal stability** across the 5000-frame trace.

## License

This analysis is part of a research benchmark. All code is provided for reproducibility purposes.
