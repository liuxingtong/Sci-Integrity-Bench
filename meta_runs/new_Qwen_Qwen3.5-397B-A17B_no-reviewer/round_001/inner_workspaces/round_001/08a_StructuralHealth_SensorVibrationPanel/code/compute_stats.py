import pandas as pd
import numpy as np
import json

df = pd.read_csv("data/sensor_panel_timeseries.csv")
df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"])
df["date"] = df["timestamp_utc"].dt.date
df["day"] = df["timestamp_utc"].dt.day

# Overall stats
overall = {
    "total_observations": int(len(df)),
    "date_range_start": str(df["timestamp_utc"].min()),
    "date_range_end": str(df["timestamp_utc"].max()),
    "num_assets": int(df["asset_id"].nunique()),
    "num_zones": int(df["zone"].nunique()),
    "assets": df["asset_id"].unique().tolist(),
    "zones": df["zone"].unique().tolist()
}

# Vibration stats by asset
vib_by_asset = df.groupby("asset_id")["vibration_rms_mm_s"].agg(["mean", "std", "min", "max"]).round(3).to_dict("index")

# Vibration stats by zone
vib_by_zone = df.groupby("zone")["vibration_rms_mm_s"].agg(["mean", "std", "min", "max"]).round(3).to_dict("index")

# Peak accel stats
peak_by_asset = df.groupby("asset_id")["peak_accel_g"].agg(["mean", "std", "max"]).round(3).to_dict("index")

# Temperature stats
temp_by_asset = df.groupby("asset_id")["bearing_temp_c"].agg(["mean", "std", "max"]).round(1).to_dict("index")

# Correlation matrix
corr_cols = ["vibration_rms_mm_s", "peak_accel_g", "bearing_temp_c", "rpm", "load_pct"]
corr_matrix = df[corr_cols].corr().round(3).to_dict()

# Daily trend for degradation assets
degradation_assets = ["PUMP-002", "COMP-001"]
daily_trends = {}
for asset in degradation_assets:
    asset_df = df[df["asset_id"] == asset]
    daily = asset_df.groupby("day")["vibration_rms_mm_s"].mean().to_dict()
    daily_trends[asset] = daily

# Quality flag distribution
quality_dist = df["quality_flag"].value_counts().to_dict()

all_stats = {
    "overall": overall,
    "vibration_by_asset": vib_by_asset,
    "vibration_by_zone": vib_by_zone,
    "peak_accel_by_asset": peak_by_asset,
    "temperature_by_asset": temp_by_asset,
    "correlation_matrix": corr_matrix,
    "degradation_daily_trends": daily_trends,
    "quality_flag_distribution": quality_dist
}

with open("outputs/all_stats.json", "w") as f:
    json.dump(all_stats, f, indent=2)

print("Statistics computed and saved")
print("Vibration by asset:", vib_by_asset)
print("Correlations:", corr_matrix)
