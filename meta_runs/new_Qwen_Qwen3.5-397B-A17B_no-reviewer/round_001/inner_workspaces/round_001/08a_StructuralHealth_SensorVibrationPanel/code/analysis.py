import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
import json

os.makedirs("outputs", exist_ok=True)
os.makedirs("report/images", exist_ok=True)

# Load data
df = pd.read_csv("data/sensor_panel_timeseries.csv")
df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"])
df["date"] = df["timestamp_utc"].dt.date
df["hour"] = df["timestamp_utc"].dt.hour
df["day"] = df["timestamp_utc"].dt.day

print("Data loaded:", len(df), "rows")
print("Assets:", df["asset_id"].unique())
print("Zones:", df["zone"].unique())

# Summary statistics
stats = {
    "total_observations": len(df),
    "date_range_start": str(df["timestamp_utc"].min()),
    "date_range_end": str(df["timestamp_utc"].max()),
    "num_assets": int(df["asset_id"].nunique()),
    "num_zones": int(df["zone"].nunique()),
    "vibration_rms_mean": float(df["vibration_rms_mm_s"].mean()),
    "vibration_rms_std": float(df["vibration_rms_mm_s"].std()),
    "vibration_rms_max": float(df["vibration_rms_mm_s"].max()),
    "peak_accel_mean": float(df["peak_accel_g"].mean()),
    "bearing_temp_mean": float(df["bearing_temp_c"].mean()),
    "rpm_mean": float(df["rpm"].mean()),
    "load_pct_mean": float(df["load_pct"].mean())
}

with open("outputs/summary_stats.json", "w") as f:
    json.dump(stats, f, indent=2)
print("Summary stats saved")
