import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
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

# Figure 1: Vibration RMS over time by asset
plt.figure(figsize=(14, 8))
for asset in df["asset_id"].unique():
    asset_df = df[df["asset_id"] == asset].sort_values("timestamp_utc")
    plt.plot(asset_df["timestamp_utc"], asset_df["vibration_rms_mm_s"], label=asset, alpha=0.7, linewidth=0.8)
plt.xlabel("Date")
plt.ylabel("Vibration RMS (mm/s)")
plt.title("Vibration RMS Over Time by Asset")
plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left", fontsize=8)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("report/images/vibration_time_series.png", dpi=150)
plt.close()
print("Figure 1 saved: vibration_time_series.png")

# Figure 2: Box plot of vibration by asset
plt.figure(figsize=(12, 6))
sns.boxplot(data=df, x="asset_id", y="vibration_rms_mm_s")
plt.xlabel("Asset ID")
plt.ylabel("Vibration RMS (mm/s)")
plt.title("Vibration Distribution by Asset")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("report/images/vibration_by_asset.png", dpi=150)
plt.close()
print("Figure 2 saved: vibration_by_asset.png")

# Figure 3: Box plot of vibration by zone
plt.figure(figsize=(10, 6))
sns.boxplot(data=df, x="zone", y="vibration_rms_mm_s")
plt.xlabel("Zone")
plt.ylabel("Vibration RMS (mm/s)")
plt.title("Vibration Distribution by Zone")
plt.tight_layout()
plt.savefig("report/images/vibration_by_zone.png", dpi=150)
plt.close()
print("Figure 3 saved: vibration_by_zone.png")

# Figure 4: Correlation heatmap
plt.figure(figsize=(10, 8))
corr_cols = ["vibration_rms_mm_s", "peak_accel_g", "bearing_temp_c", "rpm", "load_pct"]
corr_matrix = df[corr_cols].corr()
sns.heatmap(corr_matrix, annot=True, cmap="coolwarm", center=0, fmt=".2f")
plt.title("Correlation Matrix: Vibration, Temperature, RPM, Load")
plt.tight_layout()
plt.savefig("report/images/correlation_heatmap.png", dpi=150)
plt.close()
print("Figure 4 saved: correlation_heatmap.png")

# Figure 5: Vibration vs Temperature scatter
plt.figure(figsize=(10, 6))
for asset in df["asset_id"].unique()[:4]:  # First 4 assets for clarity
    asset_df = df[df["asset_id"] == asset]
    plt.scatter(asset_df["bearing_temp_c"], asset_df["vibration_rms_mm_s"], label=asset, alpha=0.3, s=10)
plt.xlabel("Bearing Temperature (C)")
plt.ylabel("Vibration RMS (mm/s)")
plt.title("Vibration vs Bearing Temperature")
plt.legend()
plt.tight_layout()
plt.savefig("report/images/vibration_vs_temp.png", dpi=150)
plt.close()
print("Figure 5 saved: vibration_vs_temp.png")

# Figure 6: Daily trend for degrading assets
plt.figure(figsize=(12, 6))
degradation_assets = ["PUMP-002", "COMP-001"]
for asset in degradation_assets:
    daily = df[df["asset_id"] == asset].groupby("day")["vibration_rms_mm_s"].mean()
    plt.plot(daily.index, daily.values, marker="o", label=asset, linewidth=2)
plt.xlabel("Day of Month")
plt.ylabel("Mean Vibration RMS (mm/s)")
plt.title("Daily Vibration Trend for Assets Showing Degradation")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("report/images/degradation_trend.png", dpi=150)
plt.close()
print("Figure 6 saved: degradation_trend.png")

# Figure 7: Peak acceleration distribution
plt.figure(figsize=(10, 6))
sns.histplot(data=df, x="peak_accel_g", hue="asset_id", bins=30, alpha=0.5, element="step")
plt.xlabel("Peak Acceleration (g)")
plt.ylabel("Count")
plt.title("Peak Acceleration Distribution by Asset")
plt.tight_layout()
plt.savefig("report/images/peak_accel_distribution.png", dpi=150)
plt.close()
print("Figure 7 saved: peak_accel_distribution.png")

print("All figures generated successfully!")
