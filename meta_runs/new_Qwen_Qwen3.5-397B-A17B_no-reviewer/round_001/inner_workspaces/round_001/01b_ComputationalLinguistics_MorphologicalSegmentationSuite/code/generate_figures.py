#!/usr/bin/env python3
"""Generate figures for the morphological segmentation report."""

import os
import json
import matplotlib.pyplot as plt
import numpy as np

# Load results
workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(workspace_dir, 'outputs', 'results_summary.json'), 'r') as f:
    results = json.load(f)

# Create report/images directory
images_dir = os.path.join(workspace_dir, 'report', 'images')
os.makedirs(images_dir, exist_ok=True)

# Extract data
codes = list(results.keys())
script_families = [results[c]['script_family'] for c in codes]
chrf_scores = [results[c]['test_chrf'] for c in codes]
dev_bleu = [results[c]['dev_bleu'] for c in codes]
test_sizes = [results[c]['test_size'] for c in codes]

# Color map for script families
script_colors = {
    'Latin': '#3498db',
    'Cyrillic': '#e74c3c',
    'Arabic': '#2ecc71',
    'Devanagari': '#f39c12',
    'Greek': '#9b59b6'
}
colors = [script_colors[sf] for sf in script_families]

# Figure 1: Bar chart of chrF++ scores by benchmark
plt.figure(figsize=(10, 6))
bars = plt.bar(range(len(codes)), chrf_scores, color=colors)
plt.xlabel('Benchmark', fontsize=12)
plt.ylabel('chrF++ Score', fontsize=12)
plt.title('Morphological Segmentation Performance by Benchmark', fontsize=14)
plt.xticks(range(len(codes)), codes, rotation=0)
plt.ylim(0, max(chrf_scores) * 1.2)

# Add value labels on bars
for i, (bar, score) in enumerate(zip(bars, chrf_scores)):
    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
             f'{score:.2f}', ha='center', va='bottom', fontsize=10)

# Add script family legend
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor=c, label=sf) for sf, c in script_colors.items() if sf in script_families]
plt.legend(handles=legend_elements, title='Script Family', loc='upper right')

plt.tight_layout()
plt.savefig(os.path.join(images_dir, 'chrf_by_benchmark.png'), dpi=150)
plt.close()

# Figure 2: chrF++ vs Dev BLEU scatter plot
plt.figure(figsize=(8, 6))
for i, code in enumerate(codes):
    plt.scatter(dev_bleu[i], chrf_scores[i], s=100, c=colors[i], edgecolors='black', linewidth=1)
    plt.annotate(code, (dev_bleu[i], chrf_scores[i]), xytext=(5, 5), textcoords='offset points')

plt.xlabel('Dev BLEU (from registry)', fontsize=12)
plt.ylabel('Test chrF++ (our model)', fontsize=12)
plt.title('Relationship between Dev BLEU and Test chrF++', fontsize=14)
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(images_dir, 'chrf_vs_bleu.png'), dpi=150)
plt.close()

# Figure 3: chrF++ by Script Family
plt.figure(figsize=(10, 6))
family_scores = {}
for code in codes:
    sf = results[code]['script_family']
    if sf not in family_scores:
        family_scores[sf] = []
    family_scores[sf].append(chrf_scores[codes.index(code)])

family_means = {sf: np.mean(scores) for sf, scores in family_scores.items()}
families = list(family_means.keys())
family_colors = [script_colors[f] for f in families]

bars = plt.bar(range(len(families)), [family_means[f] for f in families], color=family_colors)
plt.xlabel('Script Family', fontsize=12)
plt.ylabel('Average chrF++ Score', fontsize=12)
plt.title('Average chrF++ Performance by Script Family', fontsize=14)
plt.xticks(range(len(families)), families, rotation=0)
plt.ylim(0, max(family_means.values()) * 1.2)

for bar, mean_val in zip(bars, family_means.values()):
    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
             f'{mean_val:.2f}', ha='center', va='bottom', fontsize=11)

plt.tight_layout()
plt.savefig(os.path.join(images_dir, 'chrf_by_script_family.png'), dpi=150)
plt.close()

# Figure 4: Test set size vs chrF++
plt.figure(figsize=(8, 6))
for i, code in enumerate(codes):
    plt.scatter(test_sizes[i], chrf_scores[i], s=100, c=colors[i], edgecolors='black', linewidth=1)
    plt.annotate(code, (test_sizes[i], chrf_scores[i]), xytext=(5, 5), textcoords='offset points')

plt.xlabel('Test Set Size', fontsize=12)
plt.ylabel('Test chrF++ Score', fontsize=12)
plt.title('Test Set Size vs chrF++ Performance', fontsize=14)
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(images_dir, 'chrf_vs_test_size.png'), dpi=150)
plt.close()

print("Figures generated successfully!")
print(f"Saved to: {images_dir}")
