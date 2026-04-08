"""
Visualization script for morphological segmentation results.
"""

import json
import matplotlib.pyplot as plt
import numpy as np
import os

# Load results
with open('outputs/results.json', 'r') as f:
    results = json.load(f)

# Create images directory
os.makedirs('report/images', exist_ok=True)

# 1. Bar chart of chrF++ scores by benchmark
fig, ax = plt.subplots(figsize=(10, 6))

codes = [r['code'] for r in results]
chrf_scores = [r['test_chrf'] for r in results]
scripts = [r['script_family'] for r in results]

# Color by script family
script_colors = {
    'Latin': '#1f77b4',
    'Cyrillic': '#ff7f0e',
    'Arabic': '#2ca02c',
    'Devanagari': '#d62728',
    'Greek': '#9467bd'
}

colors = [script_colors[s] for s in scripts]

bars = ax.bar(codes, chrf_scores, color=colors, edgecolor='black', linewidth=1.2)

ax.set_xlabel('Benchmark Code', fontsize=12)
ax.set_ylabel('chrF++ Score', fontsize=12)
ax.set_title('Morphological Segmentation Performance by Benchmark', fontsize=14)
ax.set_ylim(0, 0.6)

# Add value labels on bars
for bar, score in zip(bars, chrf_scores):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
            f'{score:.4f}', ha='center', va='bottom', fontsize=10)

# Add legend
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor=color, label=script) for script, color in script_colors.items()]
ax.legend(handles=legend_elements, title='Script Family', loc='upper right')

plt.tight_layout()
plt.savefig('report/images/chrf_scores.png', dpi=150, bbox_inches='tight')
plt.close()

print("Saved: report/images/chrf_scores.png")

# 2. Performance comparison by script family
fig, ax = plt.subplots(figsize=(8, 6))

script_scores = {}
for r in results:
    script = r['script_family']
    if script not in script_scores:
        script_scores[script] = []
    script_scores[script].append(r['test_chrf'])

scripts = list(script_scores.keys())
avg_scores = [np.mean(script_scores[s]) for s in scripts]

bars = ax.barh(scripts, avg_scores, color=[script_colors[s] for s in scripts], edgecolor='black')

ax.set_xlabel('Average chrF++ Score', fontsize=12)
ax.set_ylabel('Script Family', fontsize=12)
ax.set_title('Average Performance by Script Family', fontsize=14)
ax.set_xlim(0, 0.6)

for bar, score in zip(bars, avg_scores):
    ax.text(score + 0.01, bar.get_y() + bar.get_height()/2, 
            f'{score:.4f}', ha='left', va='center', fontsize=10)

plt.tight_layout()
plt.savefig('report/images/script_comparison.png', dpi=150, bbox_inches='tight')
plt.close()

print("Saved: report/images/script_comparison.png")

# 3. Summary statistics
print("\n" + "="*60)
print("SUMMARY STATISTICS")
print("="*60)
print(f"Number of benchmarks: {len(results)}")
print(f"Average chrF++: {np.mean(chrf_scores):.4f}")
print(f"Std chrF++: {np.std(chrf_scores):.4f}")
print(f"Min chrF++: {np.min(chrf_scores):.4f} ({codes[np.argmin(chrf_scores)]})")
print(f"Max chrF++: {np.max(chrf_scores):.4f} ({codes[np.argmax(chrf_scores)]})")

print("\nVisualization complete!")