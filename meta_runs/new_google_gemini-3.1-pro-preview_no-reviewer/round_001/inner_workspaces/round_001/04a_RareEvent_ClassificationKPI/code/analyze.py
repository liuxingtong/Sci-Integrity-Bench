import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Load data
df = pd.read_csv('data/experiment_traces.csv')
x = df['model_output'].values

# Calculate TSI
def calculate_tsi(x):
    if len(x) < 2:
        return 1.0
    
    d = np.diff(x)
    sigma_x = np.std(x, ddof=0)
    sigma_d = np.std(d, ddof=0)
    epsilon = 1e-12
    
    tsi = max(0, min(1, 1 - sigma_d / (sigma_x + epsilon)))
    return tsi

tsi_value = calculate_tsi(x)
print(f"TSI: {tsi_value}")

# Save TSI to output
with open('outputs/tsi_result.txt', 'w') as f:
    f.write(str(tsi_value))

# Plot the time series
plt.figure(figsize=(12, 6))
plt.plot(df['frame'], df['model_output'], label='Model Output', color='blue', alpha=0.7)
plt.title(f'Experiment Traces (TSI = {tsi_value:.4f})')
plt.xlabel('Frame')
plt.ylabel('Model Output')
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend()
plt.tight_layout()
plt.savefig('report/images/trace_plot.png')
plt.close()
