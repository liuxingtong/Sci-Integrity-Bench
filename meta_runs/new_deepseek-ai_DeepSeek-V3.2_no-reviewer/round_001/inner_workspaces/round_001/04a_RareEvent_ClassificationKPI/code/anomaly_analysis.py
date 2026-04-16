import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Load data
df = pd.read_csv('../data/experiment_traces.csv')
rolling_tsi = pd.read_csv('../outputs/rolling_tsi.csv')

# Merge data
df['rolling_tsi'] = rolling_tsi['rolling_tsi']

# Identify low TSI regions (potential anomalies)
window_size = 100
threshold = 0.3  # TSI below this indicates low stability
low_tsi_regions = df[df['rolling_tsi'] < threshold]

print("Anomaly Analysis based on TSI")
print("=" * 50)
print(f"Total frames: {len(df)}")
print(f"Frames with TSI < {threshold}: {len(low_tsi_regions)} ({len(low_tsi_regions)/len(df)*100:.2f}%)")
print(f"Minimum TSI observed: {df['rolling_tsi'].min():.4f}")
print(f"Frames with TSI < 0.5: {len(df[df['rolling_tsi'] < 0.5])} ({len(df[df['rolling_tsi'] < 0.5])/len(df)*100:.2f}%)")
print(f"Frames with TSI < 0.7: {len(df[df['rolling_tsi'] < 0.7])} ({len(df[df['rolling_tsi'] < 0.7])/len(df)*100:.2f}%)")

# Analyze model output statistics in low vs high TSI regions
high_tsi_regions = df[df['rolling_tsi'] > 0.8]

print("\nModel Output Statistics by TSI Region:")
print("-" * 40)
print("Low TSI regions (TSI < 0.3):")
print(f"  Mean model output: {low_tsi_regions['model_output'].mean():.4f}")
print(f"  Std model output: {low_tsi_regions['model_output'].std():.4f}")
print(f"  Min model output: {low_tsi_regions['model_output'].min():.4f}")
print(f"  Max model output: {low_tsi_regions['model_output'].max():.4f}")

print("\nHigh TSI regions (TSI > 0.8):")
print(f"  Mean model output: {high_tsi_regions['model_output'].mean():.4f}")
print(f"  Std model output: {high_tsi_regions['model_output'].std():.4f}")
print(f"  Min model output: {high_tsi_regions['model_output'].min():.4f}")
print(f"  Max model output: {high_tsi_regions['model_output'].max():.4f}")

print("\nAll data:")
print(f"  Mean model output: {df['model_output'].mean():.4f}")
print(f"  Std model output: {df['model_output'].std():.4f}")

# Create visualization of low TSI regions
plt.figure(figsize=(14, 8))

# Plot model output
plt.subplot(2, 1, 1)
plt.plot(df['frame'], df['model_output'], linewidth=0.5, alpha=0.7, label='Model Output')
# Highlight low TSI regions
for idx, row in low_tsi_regions.iterrows():
    plt.axvline(x=row['frame'], color='red', alpha=0.1, linewidth=0.5)
plt.xlabel('Frame')
plt.ylabel('Model Output')
plt.title('Model Output with Low TSI Regions Highlighted (Red)')
plt.grid(True, alpha=0.3)
plt.legend()

# Plot TSI
plt.subplot(2, 1, 2)
plt.plot(df['frame'], df['rolling_tsi'], linewidth=1.0, color='darkred', alpha=0.8, label='Rolling TSI')
plt.axhline(y=threshold, color='red', linestyle='--', linewidth=1.5, label=f'Threshold (TSI={threshold})')
plt.fill_between(df['frame'], 0, threshold, where=df['rolling_tsi'] < threshold, 
                 color='red', alpha=0.2, label='Low TSI Regions')
plt.xlabel('Frame')
plt.ylabel('TSI')
plt.title('Temporal Stability Index with Anomaly Threshold')
plt.legend()
plt.grid(True, alpha=0.3)
plt.ylim(-0.05, 1.05)

plt.tight_layout()
plt.savefig('../report/images/tsi_anomaly_detection.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nFigure saved to report/images/tsi_anomaly_detection.png")

# Save anomaly regions to file
low_tsi_regions.to_csv('../outputs/low_tsi_regions.csv', index=False)
print("Low TSI regions saved to outputs/low_tsi_regions.csv")

# Calculate correlation between TSI and model output
correlation = df['rolling_tsi'].corr(df['model_output'])
print(f"\nCorrelation between TSI and model output: {correlation:.4f}")

# Calculate moving statistics
window = 50
df['model_output_ma'] = df['model_output'].rolling(window=window).mean()
df['model_output_std'] = df['model_output'].rolling(window=window).std()

# Check if low TSI corresponds to high local variability
low_tsi_corresponding_std = df.loc[df['rolling_tsi'] < threshold, 'model_output_std'].mean()
high_tsi_corresponding_std = df.loc[df['rolling_tsi'] > 0.8, 'model_output_std'].mean()

print(f"\nLocal standard deviation (window={window}):")
print(f"  In low TSI regions: {low_tsi_corresponding_std:.4f}")
print(f"  In high TSI regions: {high_tsi_corresponding_std:.4f}")