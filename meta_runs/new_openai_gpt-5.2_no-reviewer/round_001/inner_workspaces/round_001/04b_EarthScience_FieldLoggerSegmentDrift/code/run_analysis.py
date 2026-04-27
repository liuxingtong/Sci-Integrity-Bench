#!/usr/bin/env python3
"""EarthScience FieldLoggerSegmentDrift

Computes TWDM per segment, validates against golden cases, produces a figure and a report.

Run:
  python code/run_analysis.py
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "outputs"
REPORT_DIR = ROOT / "report"
IMG_DIR = REPORT_DIR / "images"


def compute_twdm(x: np.ndarray, epsilon: float) -> Optional[float]:
    """Compute TWDM as defined in the task.

    Parameters
    ----------
    x : np.ndarray
        1D array of values, already in frame-sorted order.
    epsilon : float
        Small constant added to sigma in denominator.

    Returns
    -------
    float | None
        TWDM value, or None if n < 3.
    """
    x = np.asarray(x, dtype=float)
    n = int(x.size)
    if n < 3:
        return None
    n1 = n // 3
    n2 = n // 3
    n3 = n - n1 - n2
    # Slices (note: if n1==0, first slice empty -> mean would be nan; but n>=3 ensures n1>=1)
    s1 = x[:n1]
    s2 = x[n1 : n1 + n2]
    s3 = x[n1 + n2 :]
    m1 = float(np.mean(s1))
    m2 = float(np.mean(s2))
    m3 = float(np.mean(s3))
    delta = max(m1, m2, m3) - min(m1, m2, m3)
    sigma = float(np.std(x, ddof=0))
    return float(delta / (sigma + float(epsilon)))


def sanitize_segment_id(seg_id: Any) -> str:
    s = str(seg_id)
    s = re.sub(r"[^A-Za-z0-9_.-]+", "_", s)
    return s


def load_manifest(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def extract_case_series(case: Dict[str, Any], readings: pd.DataFrame) -> Tuple[str, np.ndarray, float]:
    """Return (case_name, x, expected_twdm) for a golden case.

    Supported formats (best-effort, to be robust to manifest variations):
      - {"name":..., "x": [...], "expected_twdm": ...}
      - {"segment_id":..., "expected_twdm": ...} (use all frames for that segment)
      - {"segment_id":..., "frames": [...], "expected_twdm": ...} (subset by frames)
    """
    expected = case.get("expected_twdm", None)
    if expected is None:
        raise KeyError("golden case missing expected_twdm")

    if "x" in case:
        x = np.asarray(case["x"], dtype=float)
        name = str(case.get("name", case.get("id", "golden_x")))
        return name, x, float(expected)

    if "segment_id" in case:
        seg_id = case["segment_id"]
        df = readings.loc[readings["segment_id"] == seg_id, ["frame", "vwc_pct"]].copy()
        if df.empty:
            raise ValueError(f"golden case segment_id not found in readings: {seg_id!r}")
        if "frames" in case and case["frames"] is not None:
            frames = set(case["frames"])
            df = df[df["frame"].isin(frames)]
        df = df.sort_values("frame", ascending=True)
        x = df["vwc_pct"].to_numpy(dtype=float)
        name = str(case.get("name", f"segment_{seg_id}"))
        return name, x, float(expected)

    raise ValueError("Unrecognized golden case format; expected key 'x' or 'segment_id'.")


def make_segment_table(
    readings: pd.DataFrame,
    segment_order: List[Any],
    epsilon: float,
    threshold: float,
) -> pd.DataFrame:
    rows = []
    for seg_id in segment_order:
        df = readings.loc[readings["segment_id"] == seg_id, ["frame", "vwc_pct"]].copy()
        df = df.sort_values("frame", ascending=True)
        x = df["vwc_pct"].to_numpy(dtype=float)
        n = int(x.size)
        twdm = compute_twdm(x, epsilon)
        if twdm is None:
            pf = "N/A"
        else:
            pf = "PASS" if twdm <= threshold else "FAIL"
        rows.append(
            {
                "segment_id": seg_id,
                "n_frames": n,
                "TWDM": twdm,
                "pass_fail": pf,
            }
        )

    out = pd.DataFrame(rows)
    return out


def plot_one_segment(readings: pd.DataFrame, segment_id: Any, out_path: Path) -> None:
    df = readings.loc[readings["segment_id"] == segment_id, ["frame", "vwc_pct"]].copy()
    df = df.sort_values("frame", ascending=True)

    plt.figure(figsize=(8.5, 4.8))
    plt.plot(df["frame"], df["vwc_pct"], marker="o", linewidth=1.5, markersize=3)
    plt.xlabel("Frame")
    plt.ylabel("VWC (%)")
    plt.title(f"Soil logger VWC time series — segment_id={segment_id}")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=200)
    plt.close()


def df_to_markdown_table(df: pd.DataFrame) -> str:
    # Format TWDM column to high precision when present.
    df2 = df.copy()
    def fmt_twdm(v: Any) -> str:
        if v is None or (isinstance(v, float) and (math.isnan(v))):
            return "N/A"
        return f"{float(v):.12g}"  # enough precision for reporting while readable

    df2["TWDM"] = [fmt_twdm(v) for v in df2["TWDM"].tolist()]

    # Ensure column order
    cols = ["segment_id", "n_frames", "TWDM", "pass_fail"]
    df2 = df2[cols]
    return df2.to_markdown(index=False)


def main() -> None:
    manifest = load_manifest(DATA_DIR / "twdm_audit_manifest.json")
    epsilon = float(manifest["epsilon"])
    threshold = float(manifest["twdm_pass_threshold"])
    segment_order = list(manifest["segment_report_order"])
    golden_cases = list(manifest.get("golden_cases", []))

    readings = pd.read_csv(DATA_DIR / "soil_logger_readings.csv")

    # Basic hygiene: required columns
    required_cols = {"segment_id", "frame", "vwc_pct"}
    missing = required_cols - set(readings.columns)
    if missing:
        raise KeyError(f"Missing columns in readings: {sorted(missing)}")

    # Ensure numeric types for frame and vwc_pct
    readings = readings.copy()
    readings["frame"] = pd.to_numeric(readings["frame"], errors="coerce")
    readings["vwc_pct"] = pd.to_numeric(readings["vwc_pct"], errors="coerce")
    if readings[["frame", "vwc_pct"]].isna().any().any():
        # Keep rows that are fully valid
        readings = readings.dropna(subset=["frame", "vwc_pct"]).copy()

    # Golden-case validation
    max_abs_err = 0.0
    golden_detail_rows = []
    for case in golden_cases:
        name, x, expected = extract_case_series(case, readings)
        got = compute_twdm(x, epsilon)
        if got is None:
            err = float("nan")
            raise ValueError(f"Golden case {name!r} produced undefined TWDM (n<3).")
        err = abs(got - expected)
        max_abs_err = max(max_abs_err, err)
        golden_detail_rows.append({"case": name, "expected_twdm": expected, "computed_twdm": got, "abs_error": err, "n": int(len(x))})

    golden_df = pd.DataFrame(golden_detail_rows)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    golden_df.to_csv(OUT_DIR / "golden_case_check.csv", index=False)

    # Hard requirement from task: numerical agreement within 1e-9
    if max_abs_err > 1e-9:
        raise ValueError(
            f"Golden-case validation failed: max_abs_err={max_abs_err} exceeds 1e-9. "
            f"See outputs/golden_case_check.csv for details."
        )

    # Segment table
    seg_table = make_segment_table(readings, segment_order, epsilon, threshold)
    seg_table.to_csv(OUT_DIR / "segment_twdm_table.csv", index=False)

    # Plot one segment (first in report order)
    plot_seg = segment_order[0] if len(segment_order) else readings["segment_id"].iloc[0]
    fig_name = f"vwc_timeseries_segment_{sanitize_segment_id(plot_seg)}.png"
    fig_path = IMG_DIR / fig_name
    plot_one_segment(readings, plot_seg, fig_path)

    # Assemble report
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    md_table = df_to_markdown_table(seg_table)
    report = f"""# Soil-moisture campaign QA: segment drift via TWDM\n\n## Data\n\nInput: `data/soil_logger_readings.csv` containing long-format soil logger readings with columns (`segment_id`, `frame`, `vwc_pct`). For each `segment_id`, readings were sorted by `frame` ascending and `vwc_pct` was treated as the series `x`.\n\nManifest: `data/twdm_audit_manifest.json` providing the numerical constant ε (`epsilon`), the pass threshold (`twdm_pass_threshold`), an explicit reporting order (`segment_report_order`), and `golden_cases` for self-checking.\n\n## Methodology (TWDM)\n\nFor each segment, with series `x` of length `n`:\n\n- If `n < 3`, TWDM is undefined for thresholding: report `TWDM = N/A` and `pass_fail = N/A`. (These segments are still listed, but are not eligible for thresholding under the three-window definition.)\n- Otherwise, define `n1 = n//3`, `n2 = n//3`, `n3 = n - n1 - n2`. Compute means of the thirds: \n  - `m1 = mean(x[:n1])`\n  - `m2 = mean(x[n1:n1+n2])`\n  - `m3 = mean(x[n1+n2:])`\n- Let `Δ = max(m1, m2, m3) - min(m1, m2, m3)`.\n- Let `σ` be the *population* standard deviation of `x` (`ddof=0`).\n- Using ε from the manifest, compute: \n\n\\[\\mathrm{{TWDM}} = \\frac{{\\Delta}}{{\\sigma + \\varepsilon}}\\]\\\n\nClassification uses `twdm_pass_threshold` from the manifest: `PASS` if `TWDM ≤ threshold`, else `FAIL`.\n\n## Numerical validation against golden cases\n\nUsing the same implementation and ε from the manifest, the maximum absolute error over all provided golden cases was:\n\n- **max |computed − expected| = {max_abs_err:.12g}**\n\n(Per-case details are saved to `outputs/golden_case_check.csv`.)\n\n## Results (ordered by manifest)\n\nThreshold: **{threshold}** (ε = **{epsilon}**)\n\n{md_table}\n\n## Time-series visualization\n\n![VWC time series for segment {plot_seg}](images/{fig_name})\n\n*Figure 1. Volumetric water content (VWC, %) versus frame for `segment_id={plot_seg}`.*\n\n## Discussion\n\nTWDM summarizes between-third mean drift relative to within-segment variability. Segments with higher TWDM indicate that the early/middle/late thirds differ more strongly than would be expected from the overall dispersion of the series, suggesting potential sensor drift, environmental regime change, or logging artifacts.\n\nSegments flagged as `INSUFFICIENT_LENGTH` have fewer than three frames and cannot be meaningfully evaluated under the three-window definition. For `PASS`/`FAIL` segments, follow-up QA should prioritize high-TWDM segments by inspecting raw traces (e.g., step changes, sustained trends) and cross-checking with field notes or co-located sensors to distinguish true hydrologic change from instrumentation issues.\n"""

    (REPORT_DIR / "report.md").write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
