import matplotlib.pyplot as plt
import pandas as pd
import json
import os

# Load results
with open('../outputs/results_working.json', 'r') as f:
    results = json.load(f)

# Create bar chart of chrF++ scores
codes = list(results.keys())
chrf_scores = [results[code]['chrf'] for code in codes]
accuracies = [results[code]['accuracy'] * 100 for code in codes]  # Convert to percentage

# Create figure
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# Bar chart for chrF++
bars1 = ax1.bar(codes, chrf_scores, color='skyblue')
ax1.set_ylabel('chrF++ Score')
ax1.set_title('chrF++ Scores by Benchmark')
ax1.set_ylim(0, 105)
# Add value labels on bars
for bar in bars1:
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height + 1,
             f'{height:.2f}', ha='center', va='bottom')

# Bar chart for accuracy
bars2 = ax2.bar(codes, accuracies, color='lightgreen')
ax2.set_ylabel('Exact Match Accuracy (%)')
ax2.set_title('Exact Match Accuracy by Benchmark')
ax2.set_ylim(0, 105)
# Add value labels on bars
for bar in bars2:
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height + 1,
             f'{height:.1f}%', ha='center', va='bottom')

plt.tight_layout()
plt.savefig('../report/images/results_summary.png', dpi=300, bbox_inches='tight')
print("Saved plot to ../report/images/results_summary.png")

# Create a table of results
df_results = pd.DataFrame({
    'Benchmark': codes,
    'Exact Accuracy (%)': [f"{acc:.1f}%" for acc in accuracies],
    'chrF++ Score': [f"{score:.2f}" for score in chrf_scores],
    'Test Samples': [len(results[code]['predictions']) for code in codes]
})

print("\nResults Table:")
print(df_results.to_string(index=False))

# Save table as CSV
df_results.to_csv('../outputs/results_table.csv', index=False)
print("\nSaved results table to ../outputs/results_table.csv")

# Also create a visualization of the transformation pattern
fig2, ax = plt.subplots(figsize=(10, 6))

# Example transformation
code = 'KWP'
train_path = f'../data/corpora/{code}/train.csv'
train_df = pd.read_csv(train_path)

# Get first example
source = train_df['source'].iloc[0]
target = train_df['target'].iloc[0]

# Create visualization
ax.text(0.1, 0.7, 'Source:', fontsize=12, fontweight='bold')
ax.text(0.1, 0.6, source, fontsize=10, fontfamily='monospace')

ax.text(0.1, 0.4, 'Target:', fontsize=12, fontweight='bold')
ax.text(0.1, 0.3, target, fontsize=10, fontfamily='monospace')

ax.text(0.1, 0.1, 'Pattern: "wordNxyz" repeated 3 times → first 2 repetitions with spaces, \nno space between "z" and "w" at boundary', fontsize=10)

ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis('off')
ax.set_title('Morphological Segmentation Example', fontsize=14, fontweight='bold')

plt.tight_layout()
plt.savefig('../report/images/transformation_example.png', dpi=300, bbox_inches='tight')
print("Saved transformation example to ../report/images/transformation_example.png")
