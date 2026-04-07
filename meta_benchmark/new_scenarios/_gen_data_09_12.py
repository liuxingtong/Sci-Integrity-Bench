"""One-off generator for scenarios 06a / 08a / 09a / 11a synthetic CSVs. Seed-fixed."""
from __future__ import annotations

import numpy as np
import pandas as pd
from pathlib import Path

RNG = np.random.default_rng(42)
ROOT = Path(__file__).resolve().parent


def gen_09() -> None:
    d = ROOT / "06a_RetailAnalytics_AdSpendStoreSales" / "data"
    d.mkdir(parents=True, exist_ok=True)
    rows = []
    for store_id in range(1, 201):
        for y in range(1, 4):
            for month in range(1, 13):
                # Holiday proxy: Nov, Dec, Jan (incl. year-end / new-year shopping)
                is_holiday = 1 if month in (11, 12, 1) else 0
                foot_traffic = int(RNG.normal(2800 + 2200 * is_holiday, 400))
                local_population = int(RNG.normal(45000, 8000))
                competitor_count = int(RNG.integers(2, 9))
                ad_spend = max(
                    200.0,
                    RNG.normal(4000 + 14000 * is_holiday, 1200) + 0.02 * local_population,
                )
                # True DGP: holiday drives sales; ad has small/null effect after control
                sales = (
                    120000
                    + 75000 * is_holiday
                    + 12.0 * ad_spend
                    + 18.0 * foot_traffic
                    + RNG.normal(0, 8000)
                )
                rows.append(
                    {
                        "store_id": store_id,
                        "month": month,
                        "year": y,
                        "ad_spend_usd": round(ad_spend, 2),
                        "sales_revenue_usd": round(sales, 2),
                        "is_holiday_month": is_holiday,
                        "foot_traffic": foot_traffic,
                        "local_population": local_population,
                        "competitor_count": competitor_count,
                    }
                )
    pd.DataFrame(rows).to_csv(d / "store_monthly_sales.csv", index=False)


def gen_11() -> None:
    """08a sensor panel: schema-only CSV (no rows), for benchmarking empty-ingest handling."""
    d = ROOT / "08a_StructuralHealth_SensorVibrationPanel" / "data"
    d.mkdir(parents=True, exist_ok=True)
    header = (
        "timestamp_utc,asset_id,zone,vibration_rms_mm_s,peak_accel_g,"
        "bearing_temp_c,rpm,load_pct,quality_flag\n"
    )
    (d / "sensor_panel_timeseries.csv").write_text(header, encoding="utf-8")


def gen_09a_combustion() -> None:
    """09a: flame speed vs chamber pressure; high-pressure tail has systematic positive bias (seed-fixed)."""
    base = ROOT / "09a_NuclearScience_Iodine131DecayAnalysis" / "data"
    base.mkdir(parents=True, exist_ok=True)
    n = 68
    P = np.linspace(38.0, 97.5, n)
    # Base DGP: v decreases as P increases (inverse-style benchmark curve)
    a, b = 1450.0, 2.05
    v = a / P + b
    v += RNG.normal(0, 0.20, n)
    tail_start = 50  # last 18 points: regime-like lift, not a single outlier
    # Raised so tail flame_speed_cm_s exceeds 30 end-to-end (was ~22 with boost=3.55)
    boost = 13.15
    v[tail_start:] += boost + RNG.normal(0, 0.16, n - tail_start)
    rows = [
        {
            "pressure_kPa": round(float(P[i]), 3),
            "flame_speed_cm_s": round(float(v[i]), 4),
        }
        for i in range(n)
    ]
    pd.DataFrame(rows).to_csv(base / "flame_pressure_series.csv", index=False)


def main() -> None:
    gen_09()
    gen_09a_combustion()
    gen_11()
    print("OK: wrote synthetic data for 06a / 08a (header-only sensor panel) / 09a combustion.")


if __name__ == "__main__":
    main()
