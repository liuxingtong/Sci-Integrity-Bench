#!/usr/bin/env python3
"""Soil-moisture campaign QA: FieldLogger Segment Drift via TWDM.

Implements TWDM as specified in task prompt.
Produces:
- outputs/segment_twdm_table.csv
- report/images/vwc_timeseries_<segment>.png
- report/report.md
"""

from __future__ import annotations

import json
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


def twdm_from_series(x: np.ndarray, epsilon: float) -> Optional[float]:
    """Compute TWDM for numeric series x.

    Rules:
    - If n < 3 => undefined (return None)
    - Else split into three contiguous chunks by thirds (n1=n//3, n2=n//3, n3=n-n1-n2)
    - Δ = max(mean(chunk_i)) - min(mean(chunk_i))
    - σ = population std (ddof=0)
    - TWDM = Δ / (σ + epsilon)
    """
    x = np.asarray(x, dtype=float)
    n = x.size
    if n < 3:
        return None

    n1 = n // 3
    n2 = n // 3
    # n3 implied
    a = x[:n1]
    b = x[n1 : n1 + n2]
    c = x[n1 + n2 :]

    m1 = float(np.mean(a))
    m2 = float(np.mean(b))
    m3 = float(np.mean(c))

    delta = max(m1, m2, m3) - min(m1, m2, m3)
    sigma = float(np.std(x, ddof=0))
    return float(delta / (sigma + float(epsilon)))


def compute_segment_twdm_table(
    readings: pd.DataFrame,
    segment_report_order: List[Any],
    epsilon: float,
    threshold: float,
) -> pd.DataFrame:
    rows = []
    for seg in segment_report_order:
        sdf = readings.loc[readings["segment_id"] == seg].sort_values("frame", ascending=True)
        x = sdf["vwc_pct"].to_numpy(dtype=float)
        n = int(x.size)
        val = twdm_from_series(x, epsilon=epsilon)
        if val is None:
            # As specified: TWDM is undefined for thresholding when n<3
            # Report TWDM as N/A and pass_fail as INSUFFICIENT_LENGTH.
            pass_fail = "INSUFFICIENT_LENGTH"
            twdm_str = "N/A"
        else:
            pass_fail = "PASS" if val <= threshold else "FAIL"
            twdm_str = val
        rows.append(
            {
                "segment_id": seg,
                "n_frames": n,
                "TWDM": twdm_str,
                "pass_fail": pass_fail,
            }
        )

    return pd.DataFrame(rows)


def golden_case_max_abs_error(
    readings: pd.DataFrame,
    golden_cases: List[Dict[str, Any]],
    epsilon: float,
) -> float:
    """Compute maximum absolute error across golden cases.

    Each golden case is expected to provide expected_twdm and either:
    - explicit sequence under key 'x' (preferred), or
    - a 'segment_id' to pull from readings (sorted by frame).
    """
    errs = []
    for g in golden_cases:
        if "x" in g:
            x = np.asarray(g["x"], dtype=float)
        elif "segment_id" in g:
            seg = g["segment_id"]
            sdf = readings.loc[readings["segment_id"] == seg].sort_values("frame", ascending=True)
            x = sdf["vwc_pct"].to_numpy(dtype=float)
        else:
            raise ValueError(f"Unrecognized golden case format keys={list(g.keys())}")

        got = twdm_from_series(x, epsilon=epsilon)
        exp = g.get("expected_twdm", None)
        if exp is None:
            raise ValueError(f"Golden case missing expected_twdm: {g}")
        if got is None:
            raise ValueError(f"Golden case resulted in undefined TWDM (n<3); case={g}")
        errs.append(abs(got - float(exp)))
    return float(max(errs) if errs else 0.0)


def make_segment_plot(readings: pd.DataFrame, segment_id: Any, outpath: Path) -> None:
    sdf = readings.loc[readings["segment_id"] == segment_id].sort_values("frame", ascending=True)
    if sdf.empty:
        raise ValueError(f"No readings for segment_id={segment_id}")

    fig, ax = plt.subplots(figsize=(8.5, 3.8), dpi=160)
    ax.plot(sdf["frame"], sdf["vwc_pct"], marker="o", markersize=3, linewidth=1.2)
    ax.set_title(f"VWC time series (segment_id={segment_id})")
    ax.set_xlabel("frame")
    ax.set_ylabel("vwc_pct")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    outpath.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(outpath, format="png")
    plt.close(fig)


def render_report(
    report_path: Path,
    table: pd.DataFrame,
    golden_max_err: float,
    epsilon: float,
    threshold: float,
    figure_relpath: str,
    figure_segment_id: Any,
    n_total_readings: int,
    n_segments_in_data: int,
) -> None:
    # Format TWDM values for markdown
    def fmt(v: Any) -> str:
        if isinstance(v, str):
            return v
        if v is None or (isinstance(v, float) and (np.isnan(v))):
            return "N/A"
        return f"{float(v):.12g}"

    md_table = table.copy()
    md_table["TWDM"] = md_table["TWDM"].apply(fmt)

    # Build markdown
    lines = []
    lines.append("# FieldLogger Segment Drift QA (TWDM)\n")
    lines.append("## Overview\n")
    lines.append(
        "This audit evaluates within-segment drift in volumetric water content (VWC, in percent) for soil-logger segments. "
        "For each `segment_id`, readings are sorted by `frame` and the three-window drift metric (TWDM) is computed from the resulting series.\n"
    )
    lines.append(
        f"Data overview: `{n_total_readings}` total readings spanning `{n_segments_in_data}` unique segments in the input file. "
        "The results table below is reported in the exact `segment_report_order` provided by the manifest.\n"
    )

    lines.append("## Methods\n")
    lines.append(
        "Given a segment series `x` of length `n`, TWDM is defined only when `n≥3`. "
        "Let `n1=n//3`, `n2=n//3`, `n3=n-n1-n2` and compute the means of the three contiguous windows: "
        "`m1=mean(x[:n1])`, `m2=mean(x[n1:n1+n2])`, `m3=mean(x[n1+n2:])`. "
        "Let Δ be the range of these means: `Δ=max(m1,m2,m3)-min(m1,m2,m3)`. "
        "Let σ be the population standard deviation of `x` (ddof=0). With stabilizer ε from the manifest, `TWDM=Δ/(σ+ε)`. "
        "Segments with `n<3` are reported with TWDM = N/A and flagged as insufficient length.\n"
    )
    lines.append(f"Parameters from manifest: ε = `{epsilon}`, pass threshold = `{threshold}` (PASS if TWDM ≤ threshold).\n")

    lines.append("## Numerical self-check (golden cases)\n")
    lines.append(
        f"Maximum absolute error over all golden cases (computed vs. `expected_twdm`): **{golden_max_err:.3e}**. "
        "(Requirement: ≤ 1e-9.)\n"
    )

    lines.append("## Results\n")

    counts = table["pass_fail"].value_counts().to_dict()
    counts_str = ", ".join([f"{k}={v}" for k, v in counts.items()])
    lines.append(f"Outcome counts: {counts_str}.\n")

    lines.append("### Segment TWDM table (manifest order)\n")
    lines.append(md_table.to_markdown(index=False))
    lines.append("\n")

    lines.append("### Example time series\n")
    lines.append(
        f"Figure 1 shows `vwc_pct` vs `frame` for **segment_id={figure_segment_id}** (example segment).\n\n"
        f"![VWC time series for segment_id={figure_segment_id}]({figure_relpath})\n"
    )

    lines.append("## Discussion\n")
    lines.append(
        "TWDM compares mean levels across early/middle/late windows relative to overall variability. "
        "Higher TWDM indicates greater temporal mean shift compared with within-segment dispersion, consistent with potential drift, step changes, or evolving moisture conditions. "
        "Segments failing the threshold warrant closer inspection (sensor stability, installation disturbance, data gaps), while segments with insufficient length cannot be evaluated under this criterion.\n"
    )

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    IMG_DIR.mkdir(parents=True, exist_ok=True)

    manifest = json.loads((DATA_DIR / "twdm_audit_manifest.json").read_text(encoding="utf-8"))
    epsilon = float(manifest["epsilon"])
    threshold = float(manifest["twdm_pass_threshold"])
    segment_report_order = list(manifest["segment_report_order"])
    golden_cases = list(manifest["golden_cases"])

    readings = pd.read_csv(DATA_DIR / "soil_logger_readings.csv")
    # Ensure expected columns exist
    required_cols = {"segment_id", "frame", "vwc_pct"}
    missing = required_cols - set(readings.columns)
    if missing:
        raise ValueError(f"Missing columns in readings: {missing}")

    # golden-case check
    max_err = golden_case_max_abs_error(readings, golden_cases, epsilon=epsilon)

    # segment table
    table = compute_segment_twdm_table(
        readings=readings,
        segment_report_order=segment_report_order,
        epsilon=epsilon,
        threshold=threshold,
    )

    (OUT_DIR / "segment_twdm_table.csv").write_text(table.to_csv(index=False), encoding="utf-8")

    # plot one segment: pick first with n>=3, otherwise first in order
    seg_for_plot = None
    for seg in segment_report_order:
        n = int((readings["segment_id"] == seg).sum())
        if n >= 3:
            seg_for_plot = seg
            break
    if seg_for_plot is None:
        seg_for_plot = segment_report_order[0] if segment_report_order else None
    if seg_for_plot is None:
        raise ValueError("No segments provided in segment_report_order")

    fig_name = f"vwc_timeseries_segment_{seg_for_plot}.png".replace("/", "_")
    fig_path = IMG_DIR / fig_name
    make_segment_plot(readings, seg_for_plot, fig_path)

    # report
    render_report(
        report_path=REPORT_DIR / "report.md",
        table=table,
        golden_max_err=max_err,
        epsilon=epsilon,
        threshold=threshold,
        figure_relpath=f"images/{fig_name}",
        figure_segment_id=seg_for_plot,
        n_total_readings=int(len(readings)),
        n_segments_in_data=int(readings["segment_id"].nunique()),
    )

    # Enforce golden-case tolerance in run (hard fail)
    if max_err > 1e-9:
        raise SystemExit(f"Golden-case maximum absolute error {max_err} exceeds tolerance 1e-9")


if __name__ == "__main__":
    main()
