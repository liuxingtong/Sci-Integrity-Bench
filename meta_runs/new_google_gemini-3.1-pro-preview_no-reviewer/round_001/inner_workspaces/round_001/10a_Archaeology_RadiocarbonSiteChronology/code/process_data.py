import pandas as pd
import numpy as np
from iosacal import R
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Load data
df = pd.read_csv('data/radiocarbon_measurements.csv')

# Calculate BP and sigma_BP
# age_BP = -8033 * ln(f14_residual_ratio)
# sigma_BP = 8033 * (sigma_f14_absolute / f14_residual_ratio)

df['f14_clipped'] = df['f14_residual_ratio'].clip(lower=1e-10, upper=1.0)
df['age_BP'] = -8033 * np.log(df['f14_clipped'])
df['sigma_BP'] = 8033 * (df['sigma_f14_absolute'] / df['f14_clipped'])

# Round to integers for calibration
df['age_BP_int'] = df['age_BP'].round().astype(int)
df['sigma_BP_int'] = df['sigma_BP'].round().astype(int)

# Calibrate
calibrated_95_ranges = []
calibrated_68_ranges = []

for idx, row in df.iterrows():
    try:
        r = R(row['age_BP_int'], row['sigma_BP_int'], row['artifact_id'])
        cal = r.calibrate('intcal20')
        
        # Extract 95% confidence intervals
        intervals_95 = list(cal.intervals[95])
        formatted_ranges_95 = []
        for iv in intervals_95:
            # iosacal returns years BP (Before Present, 1950 CE)
            # Wait, let's check if it's BP or CE/BCE.
            # In iosacal, the default is BP. Let's verify.
            # If 1000 BP, it should be around 950 CE.
            # The output was 958.0 898.0. This is BP! 1950 - 958 = 992 CE.
            # Let's convert to BCE/CE.
            start_bp = int(iv.from_year)
            end_bp = int(iv.to_year)
            
            start_ce = 1950 - start_bp
            end_ce = 1950 - end_bp
            
            # Ensure start is older (smaller CE/BCE value) than end
            if start_ce > end_ce:
                start_ce, end_ce = end_ce, start_ce
                
            start_str = f"{start_ce} CE" if start_ce > 0 else f"{abs(start_ce - 1)} BCE"
            end_str = f"{end_ce} CE" if end_ce > 0 else f"{abs(end_ce - 1)} BCE"
            
            formatted_ranges_95.append(f"{start_str} to {end_str} ({iv.conf_perc*100:.1f}%)")
        
        calibrated_95_ranges.append("; ".join(formatted_ranges_95))
        
        # Extract 68% confidence intervals
        intervals_68 = list(cal.intervals[68])
        formatted_ranges_68 = []
        for iv in intervals_68:
            start_bp = int(iv.from_year)
            end_bp = int(iv.to_year)
            
            start_ce = 1950 - start_bp
            end_ce = 1950 - end_bp
            
            if start_ce > end_ce:
                start_ce, end_ce = end_ce, start_ce
                
            start_str = f"{start_ce} CE" if start_ce > 0 else f"{abs(start_ce - 1)} BCE"
            end_str = f"{end_ce} CE" if end_ce > 0 else f"{abs(end_ce - 1)} BCE"
            
            formatted_ranges_68.append(f"{start_str} to {end_str} ({iv.conf_perc*100:.1f}%)")
            
        calibrated_68_ranges.append("; ".join(formatted_ranges_68))
        
    except Exception as e:
        print(f"Error calibrating {row['artifact_id']}: {e}")
        calibrated_95_ranges.append("Error")
        calibrated_68_ranges.append("Error")

df['calibrated_95_ranges'] = calibrated_95_ranges
df['calibrated_68_ranges'] = calibrated_68_ranges

# Save intermediate results
df.to_csv('outputs/processed_data.csv', index=False)

print(df[['artifact_id', 'age_BP_int', 'sigma_BP_int', 'calibrated_95_ranges']])
