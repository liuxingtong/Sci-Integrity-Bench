import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def compute_twdm(x: np.ndarray, eps: float):
    """Compute TWDM per spec.

    Parameters
    ----------
    x : 1D array of vwc_pct values ordered by frame ascending.
    eps : epsilon added to population std in denominator.

    Returns
    -------
    float or None
        TWDM value if n>=3 else None.
    """
    x = np.asarray(x, dtype=float)
    n = len(x)
    if n < 3:
        return None
    n1 = n // 3
    n2 = n // 3
    n3 = n - n1 - n2
    # n>=3 ensures n3>=1; n1 or n2 may be 0 when n=3? Actually n//3=1 so OK.
    m1 = x[:n1].mean()
    m2 = x[n1:n1 + n2].mean()
    m3 = x[n1 + n2:].mean()
    delta = max(m1, m2, m3) - min(m1, m2, m3)
    sigma = x.std(ddof=0)
    return float(delta / (sigma + eps))


def main():
    root = Path(__file__).resolve().parents[1]
    data_dir = root / "data"
    out_dir = root / "outputs"
    report_dir = root / "report"
    img_dir = report_dir / "images"
    out_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    img_dir.mkdir(parents=True, exist_ok=True)

    manifest = json.loads((data_dir / "twdm_audit_manifest.json").read_text(encoding="utf-8"))
    eps = float(manifest["epsilon"])
    threshold = float(manifest["twdm_pass_threshold"])
    segment_order = list(manifest["segment_report_order"])
    golden_cases = manifest.get("golden_cases", [])

    df = pd.read_csv(data_dir / "soil_logger_readings.csv")
    # Basic schema assurance
    required_cols = {"segment_id", "frame", "vwc_pct"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Sort for deterministic series extraction
    df = df.sort_values(["segment_id", "frame"], ascending=[True, True]).reset_index(drop=True)

    # Golden case validation (computed directly from manifest-provided readings)
    golden_rows = []
    max_abs_err = 0.0
    for case in golden_cases:
        name = case.get("name", "")
        expected = case.get("expected_twdm", None)
        readings = np.asarray(case.get("readings", []), dtype=float)
        twdm_val = compute_twdm(readings, eps)

        if twdm_val is None or expected is None:
            # Golden cases in this task are expected to be defined (n>=3), but handle defensively.
            err = 0.0 if (twdm_val is None and expected is None) else np.nan
        else:
            err = abs(float(twdm_val) - float(expected))

        if not np.isnan(err):
            max_abs_err = max(max_abs_err, float(err))

        golden_rows.append({
            "name": name,
            "n": int(len(readings)),
            "expected_twdm": expected,
            "computed_twdm": twdm_val,
            "abs_error": err,
        })

    golden_df = pd.DataFrame(golden_rows)
    golden_df.to_csv(out_dir / "golden_case_check.csv", index=False)

    if golden_cases and max_abs_err > 1e-9:
        raise AssertionError(f"Golden case max_abs_err {max_abs_err} exceeds 1e-9")

    # Per-segment table in manifest order
    table_rows = []
    for seg in segment_order:
        seg_df = df.loc[df["segment_id"] == seg].sort_values("frame")
        x = seg_df["vwc_pct"].to_numpy()
        n = len(x)
        twdm_val = compute_twdm(x, eps)
        if twdm_val is None:
            pass_fail = "N/A"
            qc_flag = "INSUFFICIENT_LENGTH"
            twdm_out = np.nan
        else:
            qc_flag = ""
            twdm_out = twdm_val
            pass_fail = "PASS" if twdm_val <= threshold else "FAIL"
        table_rows.append({
            "segment_id": seg,
            "n_frames": n,
            "TWDM": twdm_out,
            "pass_fail": pass_fail,
            "qc_flag": qc_flag,
        })

    table_df = pd.DataFrame(table_rows)
    table_df.to_csv(out_dir / "segment_twdm_table.csv", index=False)

    # Figure for one segment (first in order)
    fig_seg = segment_order[0] if segment_order else df["segment_id"].iloc[0]
    plot_df = df.loc[df["segment_id"] == fig_seg].sort_values("frame")
    plt.figure(figsize=(8, 4))
    plt.plot(plot_df["frame"], plot_df["vwc_pct"], marker="o", linewidth=1.5, markersize=3)
    plt.xlabel("Frame")
    plt.ylabel("VWC (%)")
    plt.title(f"Soil logger VWC time series — segment_id={fig_seg}")
    plt.grid(True, alpha=0.3)
    fig_path = img_dir / f"vwc_vs_frame_segment_{fig_seg}.png"
    plt.tight_layout()
    plt.savefig(fig_path, dpi=200)
    plt.close()

    # Build report markdown
    # Use a fixed float format for readability
    table_md = table_df.copy()
    table_md["TWDM"] = table_md["TWDM"].map(lambda v: "N/A" if pd.isna(v) else f"{v:.6f}")
    md_table = table_md.to_markdown(index=False)

    golden_summary = "N/A (no golden_cases in manifest)" if not golden_cases else f"{max_abs_err:.3e}"

    report_text = f"""# FieldLoggerSegmentDrift QA Report (TWDM)\n\n## Data overview\n\n- Input: `data/soil_logger_readings.csv` (columns: `segment_id`, `frame`, `vwc_pct`).\n- Analysis unit: **segment**. For each `segment_id`, readings were sorted by `frame` ascending and `vwc_pct` was treated as the series `x`.\n- Parameters from `data/twdm_audit_manifest.json`: \n  - epsilon (ε) = `{eps}`\n  - pass threshold = `{threshold}`\n  - report order length = `{len(segment_order)}`\n\n## Methodology\n\nFor each segment series `x` with length `n`:\n\n- If `n < 3`, TWDM is **undefined** for thresholding. We report `TWDM = N/A` and flag the segment as insufficient length.\n- Otherwise, partition `x` into three consecutive windows with sizes:\n  - `n1 = n//3`, `n2 = n//3`, `n3 = n - n1 - n2`\n  - means: `m1 = mean(x[:n1])`, `m2 = mean(x[n1:n1+n2])`, `m3 = mean(x[n1+n2:])`\n  - drift magnitude: `Δ = max(m1,m2,m3) - min(m1,m2,m3)`\n  - population standard deviation: `σ = std(x, ddof=0)`\n\nThe **Three-Window Drift Metric (TWDM)** is computed as:\n\n\\[\\mathrm{{TWDM}} = \\frac{{\\Delta}}{{\\sigma + \\varepsilon}}\\]\\n\nPass/fail rule (when defined):\n- `PASS` if `TWDM ≤ {threshold}`\n- `FAIL` if `TWDM > {threshold}`\n\n## Numerical self-check (golden cases)\n\nGolden cases from the manifest were recomputed using the same ε and rules.\n\n- **Maximum absolute error vs expected TWDM:** `{golden_summary}`\n\n(Details saved to `outputs/golden_case_check.csv`.)\n\n## Results (ordered by manifest `segment_report_order`)\n\n{md_table}\n\n## Example segment time series\n\n![VWC vs frame for segment {fig_seg}](images/vwc_vs_frame_segment_{fig_seg}.png)\n\n*Figure 1. Volumetric water content (VWC, %) versus frame for `segment_id={fig_seg}`.*\n\n## Discussion\n\nTWDM summarizes within-segment drift by comparing the means of three consecutive thirds of the time series, normalized by overall variability (σ) with a small ε stabilization. Segments with low σ and shifting mean levels can yield larger TWDM values, indicating potential instrument drift or step changes during the segment.\n\nSegments flagged as `INSUFFICIENT_LENGTH` have fewer than 3 frames and cannot be meaningfully partitioned into three windows; additional frames would be required to assess drift using TWDM.\n\nRecomputing the manifest golden cases provides a tight numerical audit of the implementation; the reported maximum error confirms agreement with the expected values at floating-point tolerance.\n"""

    (report_dir / "report.md").write_text(report_text, encoding="utf-8")


if __name__ == "__main__":
    main()
