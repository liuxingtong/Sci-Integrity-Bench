import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Load data
df = pd.read_csv('data/experiment_traces.csv')
x = df['model_output'].values
d = np.diff(x)

# Plot distributions
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

sns.histplot(x, bins=50, kde=True, ax=axes[0], color='skyblue')
axes[0].set_title('Distribution of Model Output (x)')
axes[0].set_xlabel('Model Output')
axes[0].set_ylabel('Frequency')

sns.histplot(d, bins=50, kde=True, ax=axes[1], color='salmon')
axes[1].set_title('Distribution of First Differences (d)')
axes[1].set_xlabel('First Difference')
axes[1].set_ylabel('Frequency')

plt.tight_layout()
plt.savefig('report/images/distributions.png')
plt.close()
