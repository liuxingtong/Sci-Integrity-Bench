import pandas as pd
import numpy as np
from datetime import datetime
np.random.seed(42)
assets = ["PUMP-001", "PUMP-002", "PUMP-003", "MOTOR-001", "MOTOR-002", "FAN-001", "FAN-002", "COMP-001"]
asset_zone_map = {"PUMP-001": "Zone-A", "PUMP-002": "Zone-A", "PUMP-003": "Zone-B", "MOTOR-001": "Zone-B", "MOTOR-002": "Zone-C", "FAN-001": "Zone-C", "FAN-002": "Zone-A", "COMP-001": "Zone-B"}
asset_params = {"PUMP": {"base_vibration": 2.5, "base_temp": 55, "base_rpm": 1750, "base_load": 70}, "MOTOR": {"base_vibration": 1.8, "base_temp": 65, "base_rpm": 1800, "base_load": 75}, "FAN": {"base_vibration": 3.2, "base_temp": 45, "base_rpm": 1200, "base_load": 60}, "COMP": {"base_vibration": 4.0, "base_temp": 70, "base_rpm": 3000, "base_load": 85}}
start_date = datetime(2025, 10, 1)
end_date = datetime(2025, 10, 31, 23, 0, 0)
timestamps = pd.date_range(start=start_date, end=end_date, freq="H")
degradation_assets = ["PUMP-002", "COMP-001"]
trend_start_day = 15
rows = []
for ts in timestamps:
    dom = ts.day
    hod = ts.hour
    for asset_id in assets:
        zone = asset_zone_map[asset_id]
        atype = asset_id.split("-")[0]
        p = asset_params[atype]
        tc = 5 * np.sin((hod - 6) * np.pi / 12)
        lf = 1.1 if 8 <= hod <= 18 else 0.85
        vn = np.random.normal(0, p["base_vibration"] * 0.15)
        tn = np.random.normal(0, 3)
        rn = np.random.normal(0, p["base_rpm"] * 0.02)
        ln = np.random.normal(0, 5)
        if asset_id in degradation_assets and dom > trend_start_day:
            df = 1 + (dom - trend_start_day) * 0.08
            vn += p["base_vibration"] * 0.5 * (df - 1)
            tn += 2 * (df - 1)
        vr = max(0.1, p["base_vibration"] * lf + vn)
        pa = vr * np.random.uniform(2.5, 4.0)
        bt = p["base_temp"] + tc + tn
        rpm = max(100, p["base_rpm"] * lf + rn)
        lp = max(10, min(100, p["base_load"] * lf + ln))
        qf = "GOOD" if np.random.random() < 0.95 else ("WARNING" if np.random.random() < 0.7 else "ERROR")
        rows.append({"timestamp_utc": ts.strftime("%Y-%m-%d %H:%M:%S"), "asset_id": asset_id, "zone": zone, "vibration_rms_mm_s": round(vr, 3), "peak_accel_g": round(pa, 3), "bearing_temp_c": round(bt, 1), "rpm": round(rpm, 0), "load_pct": round(lp, 1), "quality_flag": qf})
df = pd.DataFrame(rows)
df.to_csv("data/sensor_panel_timeseries.csv", index=False)
print("Generated", len(df), "rows")
