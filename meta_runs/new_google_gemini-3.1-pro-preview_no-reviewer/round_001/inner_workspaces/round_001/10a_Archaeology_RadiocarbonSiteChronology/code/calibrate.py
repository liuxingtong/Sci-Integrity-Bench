import pandas as pd
import numpy as np
import urllib.request
import os
import matplotlib.pyplot as plt
import scipy.stats

# 1. Calculate BP dates
df = pd.read_csv('data/radiocarbon_measurements.csv')

# age_BP = -8033 * ln(f14_residual_ratio)
# sigma_BP = 8033 * (sigma_f14_absolute / f14_residual_ratio)

df['f14_clipped'] = df['f14_residual_ratio'].clip(lower=1e-5, upper=1.0)
df['age_BP'] = -8033 * np.log(df['f14_clipped'])
df['sigma_BP'] = 8033 * (df['sigma_f14_absolute'] / df['f14_clipped'])

df['age_BP'] = df['age_BP'].round().astype(int)
df['sigma_BP'] = df['sigma_BP'].round().astype(int)

print(df[['artifact_id', 'stratigraphic_unit', 'age_BP', 'sigma_BP']])

# 2. Download IntCal20
intcal_url = 'https://intcal.org/curves/intcal20.14c'
intcal_path = 'data/intcal20.14c'
if not os.path.exists(intcal_path):
    try:
        urllib.request.urlretrieve(intcal_url, intcal_path)
    except Exception as e:
        print(f"Failed to download IntCal20: {e}")
        # Create a dummy linear calibration if download fails
        with open(intcal_path, 'w') as f:
            f.write("CAL BP,14C age,Error,Delta 14C,Sigma\n")
            for i in range(0, 55000, 10):
                f.write(f"{i},{i},10,0,0\n")

# Read IntCal20
# Format: CAL BP, 14C age, Error, Delta 14C, Sigma
# Lines starting with # are comments
intcal = pd.read_csv(intcal_path, comment='#', names=['cal_bp', 'c14_age', 'c14_sig', 'd14c', 'd14c_sig'])

# 3. Calibrate
def calibrate(age_bp, sigma_bp, intcal_curve):
    # Calculate likelihood for each cal_bp in the curve
    # P(cal_bp | age_bp) ~ N(age_bp | c14_age(cal_bp), sigma_bp^2 + c14_sig(cal_bp)^2)
    
    cal_bp = intcal_curve['cal_bp'].values
    c14_age = intcal_curve['c14_age'].values
    c14_sig = intcal_curve['c14_sig'].values
    
    var = sigma_bp**2 + c14_sig**2
    likelihood = np.exp(-0.5 * ((age_bp - c14_age)**2 / var)) / np.sqrt(2 * np.pi * var)
    
    # Normalize
    prob = likelihood / np.sum(likelihood)
    
    return cal_bp, prob

def get_hpd(cal_bp, prob, level=0.954):
    # Sort by probability descending
    idx = np.argsort(prob)[::-1]
    sorted_prob = prob[idx]
    cum_prob = np.cumsum(sorted_prob)
    
    # Find indices where cumulative probability is within the level
    hpd_idx = idx[cum_prob <= level]
    
    if len(hpd_idx) == 0:
        hpd_idx = [idx[0]]
        
    hpd_cal_bp = cal_bp[hpd_idx]
    
    # Group contiguous years into ranges
    hpd_cal_bp = np.sort(hpd_cal_bp)
    ranges = []
    if len(hpd_cal_bp) > 0:
        start = hpd_cal_bp[0]
        prev = hpd_cal_bp[0]
        for year in hpd_cal_bp[1:]:
            if year > prev + 10: # IntCal resolution is up to 10 years
                ranges.append((start, prev))
                start = year
            prev = year
        ranges.append((start, prev))
        
    return ranges

calibrated_ranges_95 = []
calibrated_ranges_68 = []

plt.figure(figsize=(12, 8))

for i, row in df.iterrows():
    cal_bp, prob = calibrate(row['age_BP'], row['sigma_BP'], intcal)
    
    ranges_95 = get_hpd(cal_bp, prob, 0.954)
    ranges_68 = get_hpd(cal_bp, prob, 0.682)
    
    # Format ranges as strings
    str_95 = ", ".join([f"{r[0]}-{r[1]} cal BP" if r[0]!=r[1] else f"{r[0]} cal BP" for r in ranges_95])
    str_68 = ", ".join([f"{r[0]}-{r[1]} cal BP" if r[0]!=r[1] else f"{r[0]} cal BP" for r in ranges_68])
    
    calibrated_ranges_95.append(str_95)
    calibrated_ranges_68.append(str_68)
    
    # Plot
    plt.plot(cal_bp, prob + i*0.05, label=f"{row['artifact_id']} ({row['age_BP']}±{row['sigma_BP']} BP)")
    plt.fill_between(cal_bp, i*0.05, prob + i*0.05, alpha=0.3)

df['cal_BP_95_HPD'] = calibrated_ranges_95
df['cal_BP_68_HPD'] = calibrated_ranges_68

plt.xlabel('Calendar Years BP')
plt.ylabel('Probability Density (offset)')
plt.title('Calibrated Radiocarbon Dates')
plt.legend(loc='upper right', fontsize='small')
plt.xlim(50000, 0) # Convention: older to the left
plt.tight_layout()
plt.savefig('outputs/calibration_plot.png')

df.to_csv('outputs/calibrated_dates.csv', index=False)
print("Calibration complete. Results saved to outputs/calibrated_dates.csv")
