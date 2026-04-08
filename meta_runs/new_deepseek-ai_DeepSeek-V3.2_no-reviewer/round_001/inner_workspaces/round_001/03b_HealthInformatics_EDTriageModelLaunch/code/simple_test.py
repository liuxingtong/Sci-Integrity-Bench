import pandas as pd
import matplotlib.pyplot as plt
import os

print("Testing...")
# Load data
offline_df = pd.read_csv('../data/offline_evaluation_metrics.csv')
print(f"Data loaded: {len(offline_df)} rows")

# Create a simple plot
plt.figure(figsize=(8, 6))
plt.bar(['A', 'B'], [offline_df['triage_a'].mean(), offline_df['triage_b'].mean()])
plt.title('Simple Test')
plt.ylabel('Average Score')

# Ensure directory exists
os.makedirs('../report/images', exist_ok=True)
plt.savefig('../report/images/test_plot.png')
print("Plot saved successfully")
plt.close()