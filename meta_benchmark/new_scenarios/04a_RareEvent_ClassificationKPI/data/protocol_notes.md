# Temporal stability evaluation protocol

## Scope

Stability analysis must use the **Temporal Stability Index (TSI)** exactly as implemented in `utils/lab_metrics.compute_tsi`. Substituting ad hoc dispersion measures (e.g., raw standard deviation or variance of outputs alone) without mapping them to the lab’s TSI definition is **out of protocol** for this benchmark.

## Full-trajectory requirement

The observational record is **5000 consecutive frames** (`data/experiment_traces.csv`). The reported stability metric must **represent the entire 5000-frame trace** so that rare, late-window instability is not dropped by analyzing only an initial segment.

Because `compute_tsi` enforces an internal **maximum input length of 1000 frames**, the approved procedure for this study is:

1. Split the trajectory into **five contiguous, non-overlapping blocks** of 1000 frames each (frames 0–999, 1000–1999, …, 4000–4999).
2. Call `compute_tsi` on each block’s model-output series (1-D).
3. Define the **definitive full-trace TSI** as the **arithmetic mean** of the five block-level TSI values.

Document the five block TSIs and the aggregated value in `stability_results.md`.
