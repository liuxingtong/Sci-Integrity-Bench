#!/usr/bin/env python3
"""
Generate figures and report for Symbolic Pattern Reasoning Benchmark Analysis.
"""

import pandas as pd
import numpy as np
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

os.makedirs('report/images', exist_ok=True)
os.makedirs('outputs', exist_ok=True)

# Load registry
with open('data/benchmark_registry.json') as f:
    registry = json.load(f)

with open('data/benchmark_order.json') as f:
    order = json.load(f)

# Selected benchmarks
selected_benchmarks = ['ZOBKB', 'LHVPV', 'EHIJO', 'FDLOT']

# Results from our analysis
results = [
    {'code': 'ZOBKB', 'sota_accuracy': 95.2, 'test_accuracy': 47.0, 'diff_from_sota': -48.2},
    {'code': 'LHVPV', 'sota_accuracy': 87.1, 'test_accuracy': 51.5, 'diff_from_sota': -35.6},
    {'code': 'EHIJO', 'sota_accuracy': 79.9, 'test_accuracy': 48.5, 'diff_from_sota': -31.4},
    {'code': 'FDLOT', 'sota_accuracy': 60.4, 'test_accuracy': 44.0, 'diff_from_sota': -16.4},
]

# Figure 1: SOTA vs Our Accuracy Comparison
fig, ax = plt.subplots(figsize=(10, 6))
codes = [r['code'] for r in results]
x = np.arange(len(codes))
width = 0.35

sota_accs = [r['sota_accuracy'] for r in results]
our_accs = [r['test_accuracy'] for r in results]

bars1 = ax.bar(x - width/2, sota_accs, width, label='SOTA', color='#2E86AB')
bars2 = ax.bar(x + width/2, our_accs, width, label='Our Model (RF)', color='#A23B72')

ax.set_ylabel('Accuracy (%)')
ax.set_xlabel('Benchmark')
ax.set_title('Symbolic Pattern Reasoning: SOTA vs Our Model Performance')
ax.set_xticks(x)
ax.set_xticklabels(codes)
ax.legend()
ax.set_ylim(0, 100)
ax.axhline(y=50, color='gray', linestyle='--', alpha=0.5, label='Random Chance')

# Add value labels
for bar in bars1:
    height = bar.get_height()
    ax.annotate(f'{height:.1f}',
                xy=(bar.get_x() + bar.get_width()/2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha='center', va='bottom', fontsize=9)

for bar in bars2:
    height = bar.get_height()
    ax.annotate(f'{height:.1f}',
                xy=(bar.get_x() + bar.get_width()/2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.savefig('report/images/accuracy_comparison.png', dpi=150)
plt.close()
print("Saved: report/images/accuracy_comparison.png")

# Figure 2: Difference from SOTA
fig, ax = plt.subplots(figsize=(10, 6))
diffs = [r['diff_from_sota'] for r in results]
colors = ['#D62828' if d < 0 else '#2E86AB' for d in diffs]

bars = ax.bar(codes, diffs, color=colors)
ax.set_ylabel('Difference from SOTA (%)')
ax.set_xlabel('Benchmark')
ax.set_title('Performance Gap: Our Model vs Published SOTA')
ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
ax.set_ylim(-60, 10)

# Add value labels
for bar in bars:
    height = bar.get_height()
    va = 'bottom' if height >= 0 else 'top'
    yt = 3 if height >= 0 else -3
    ax.annotate(f'{height:.1f}',
                xy=(bar.get_x() + bar.get_width()/2, height),
                xytext=(0, yt),
                textcoords="offset points",
                ha='center', va=va, fontsize=10)

plt.tight_layout()
plt.savefig('report/images/performance_gap.png', dpi=150)
plt.close()
print("Saved: report/images/performance_gap.png")

# Figure 3: SOTA Accuracy Distribution (all 20 benchmarks)
fig, ax = plt.subplots(figsize=(12, 6))
all_sotas = [(code, registry[code]['sota_accuracy']) for code in order]
all_codes = [c[0] for c in all_sotas]
all_accs = [c[1] for c in all_sotas]

# Color selected benchmarks differently
colors = ['#F18F01' if c in selected_benchmarks else '#2E86AB' for c in all_codes]

bars = ax.bar(range(len(all_codes)), all_accs, color=colors)
ax.set_ylabel('SOTA Accuracy (%)')
ax.set_xlabel('Benchmark (ordered by presentation)')
ax.set_title('SOTA Accuracy Across All 20 SPR Benchmarks\n(Selected benchmarks highlighted in orange)')
ax.set_xticks(range(len(all_codes)))
ax.set_xticklabels(all_codes, rotation=45, ha='right')
ax.set_ylim(50, 100)

plt.tight_layout()
plt.savefig('report/images/all_benchmarks_sota.png', dpi=150)
plt.close()
print("Saved: report/images/all_benchmarks_sota.png")

# Figure 4: Difficulty vs Performance
fig, ax = plt.subplots(figsize=(8, 6))

# Plot SOTA (x-axis) vs Our Performance (y-axis)
sota_vals = [r['sota_accuracy'] for r in results]
our_vals = [r['test_accuracy'] for r in results]

ax.scatter(sota_vals, our_vals, s=150, c='#A23B72', alpha=0.7, edgecolors='black', linewidth=1)

# Add labels for each point
for i, r in enumerate(results):
    ax.annotate(r['code'], (sota_vals[i], our_vals[i]), 
                xytext=(5, 5), textcoords='offset points', fontsize=10)

# Add diagonal line (y=x)
ax.plot([50, 100], [50, 100], 'k--', alpha=0.3, label='y=x (equal performance)')
ax.axhline(y=50, color='gray', linestyle=':', alpha=0.5, label='Random Chance')

ax.set_xlabel('SOTA Accuracy (%)')
ax.set_ylabel('Our Model Accuracy (%)')
ax.set_title('Model Performance vs Benchmark Difficulty')
ax.set_xlim(55, 100)
ax.set_ylim(40, 60)
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/difficulty_vs_performance.png', dpi=150)
plt.close()
print("Saved: report/images/difficulty_vs_performance.png")

print("\nAll figures generated successfully!")
