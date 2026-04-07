"""
Create visualizations for the benchmark experiment results
"""

import json
import os
import matplotlib.pyplot as plt
import numpy as np

# Load results
with open('outputs/experiment_results_v6.json', 'r') as f:
    results = json.load(f)

# Create output directory
os.makedirs('report/images', exist_ok=True)

# Prepare data
codes = list(results.keys())
sota = [results[c]['sota_accuracy'] for c in codes]
test_acc = [results[c]['test_accuracy'] * 100 for c in codes]
gaps = [test_acc[i] - sota[i] for i in range(len(codes))]
models = [results[c]['model_name'] for c in codes]
encodings = [results[c]['encoding'] for c in codes]

# Figure 1: Test Accuracy vs SOTA Comparison
fig, ax = plt.subplots(figsize=(10, 6))

x = np.arange(len(codes))
width = 0.35

bars1 = ax.bar(x - width/2, sota, width, label='SOTA', color='steelblue', alpha=0.8)
bars2 = ax.bar(x + width/2, test_acc, width, label='Our Model', color='coral', alpha=0.8)

ax.set_ylabel('Accuracy (%)', fontsize=12)
ax.set_xlabel('Benchmark Code', fontsize=12)
ax.set_title('Test Accuracy vs Published SOTA', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(codes, fontsize=11)
ax.legend(fontsize=11)
ax.set_ylim(0, 100)

# Add value labels on bars
for bar in bars1:
    height = bar.get_height()
    ax.annotate(f'{height:.1f}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha='center', va='bottom', fontsize=9)

for bar in bars2:
    height = bar.get_height()
    ax.annotate(f'{height:.1f}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.savefig('report/images/accuracy_comparison.png', dpi=150, bbox_inches='tight')
plt.close()

# Figure 2: Gap Analysis
fig, ax = plt.subplots(figsize=(10, 6))

colors = ['green' if g >= 0 else 'red' for g in gaps]
bars = ax.bar(codes, gaps, color=colors, alpha=0.7, edgecolor='black')

ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
ax.set_ylabel('Gap (Test - SOTA) %', fontsize=12)
ax.set_xlabel('Benchmark Code', fontsize=12)
ax.set_title('Performance Gap: Our Model vs SOTA', fontsize=14, fontweight='bold')

# Add value labels
for bar, gap in zip(bars, gaps):
    height = bar.get_height()
    ax.annotate(f'{gap:.1f}%',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3 if height >= 0 else -15),
                textcoords="offset points",
                ha='center', va='bottom' if height >= 0 else 'top',
                fontsize=10, fontweight='bold')

plt.tight_layout()
plt.savefig('report/images/gap_analysis.png', dpi=150, bbox_inches='tight')
plt.close()

# Figure 3: Model and Encoding Summary
fig, ax = plt.subplots(figsize=(12, 5))

# Create a summary table as a figure
ax.axis('off')

table_data = [
    ['Code', 'SOTA (%)', 'Test (%)', 'Gap (%)', 'Best Model', 'Encoding'],
]
for code in codes:
    r = results[code]
    gap = r['test_accuracy'] * 100 - r['sota_accuracy']
    table_data.append([
        code,
        f"{r['sota_accuracy']:.1f}",
        f"{r['test_accuracy']*100:.1f}",
        f"{gap:+.1f}",
        r['model_name'],
        r['encoding']
    ])

table = ax.table(cellText=table_data[1:], colLabels=table_data[0],
                  loc='center', cellLoc='center',
                  colColours=['lightblue']*6)
table.auto_set_font_size(False)
table.set_fontsize(11)
table.scale(1.2, 1.5)

ax.set_title('Experiment Results Summary', fontsize=14, fontweight='bold', pad=20)

plt.tight_layout()
plt.savefig('report/images/results_table.png', dpi=150, bbox_inches='tight')
plt.close()

# Figure 4: SOTA vs Test Accuracy Scatter
fig, ax = plt.subplots(figsize=(8, 6))

ax.scatter(sota, test_acc, s=150, c='steelblue', alpha=0.7, edgecolors='black', linewidths=1.5)

# Add diagonal line (perfect match)
ax.plot([0, 100], [0, 100], 'k--', alpha=0.5, label='Perfect Match')

# Add labels for each point
for i, code in enumerate(codes):
    ax.annotate(code, (sota[i], test_acc[i]), 
                xytext=(5, 5), textcoords='offset points', fontsize=10)

ax.set_xlabel('SOTA Accuracy (%)', fontsize=12)
ax.set_ylabel('Our Test Accuracy (%)', fontsize=12)
ax.set_title('SOTA vs Our Test Accuracy', fontsize=14, fontweight='bold')
ax.legend(fontsize=10)
ax.set_xlim(50, 100)
ax.set_ylim(40, 70)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/scatter_comparison.png', dpi=150, bbox_inches='tight')
plt.close()

print("Visualizations created successfully!")
print("Files saved to report/images/")