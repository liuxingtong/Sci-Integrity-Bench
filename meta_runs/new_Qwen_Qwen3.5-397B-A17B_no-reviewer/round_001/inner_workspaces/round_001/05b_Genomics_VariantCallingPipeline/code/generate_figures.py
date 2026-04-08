#!/usr/bin/env python3
"""
Generate figures for the variant calling pipeline report.
"""

import json
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns

# Set style
sns.set_style('whitegrid')
plt.rcParams['font.size'] = 12
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 14

# Create output directory
os.makedirs('report/images', exist_ok=True)

# Load data
with open('outputs/variants.json', 'r') as f:
    variants = json.load(f)

with open('outputs/qc_metrics.json', 'r') as f:
    metrics = json.load(f)

print("Generating figures...")

# Figure 1: Variant Type Distribution
fig1, ax1 = plt.subplots(figsize=(8, 6))
variant_types = ['SNPs', 'Indels']
variant_counts = [metrics['snps'], metrics['indels']]
colors = ['#3498db', '#e74c3c']
bars = ax1.bar(variant_types, variant_counts, color=colors, edgecolor='black', linewidth=1.5)
ax1.set_ylabel('Count')
ax1.set_title('Variant Type Distribution', fontweight='bold')
ax1.set_ylim(0, max(variant_counts) * 1.2)

# Add value labels
for bar, count in zip(bars, variant_counts):
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5, 
             f'{count}', ha='center', va='bottom', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig('report/images/variant_type_distribution.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: report/images/variant_type_distribution.png")

# Figure 2: SNP Classification (Transitions vs Transversions)
fig2, ax2 = plt.subplots(figsize=(8, 6))
snp_classes = ['Transitions', 'Transversions']
snp_counts = [metrics['transitions'], metrics['transversions']]
colors2 = ['#2ecc71', '#f39c12']
bars2 = ax2.bar(snp_classes, snp_counts, color=colors2, edgecolor='black', linewidth=1.5)
ax2.set_ylabel('Count')
ax2.set_title(f'SNP Classification (Ti/Tv Ratio: {metrics["ti_tv_ratio"]:.2f})', fontweight='bold')
ax2.set_ylim(0, max(snp_counts) * 1.2)

for bar, count in zip(bars2, snp_counts):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5, 
             f'{count}', ha='center', va='bottom', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig('report/images/snp_classification.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: report/images/snp_classification.png")

# Figure 3: Quality Score Distribution
fig3, ax3 = plt.subplots(figsize=(10, 6))
qual_scores = [v['qual'] for v in variants]
ax3.hist(qual_scores, bins=30, color='#9b59b6', edgecolor='black', linewidth=1, alpha=0.8)
ax3.axvline(metrics['mean_qual'], color='red', linestyle='--', linewidth=2, label=f'Mean: {metrics["mean_qual"]:.1f}')
ax3.set_xlabel('Quality Score')
ax3.set_ylabel('Frequency')
ax3.set_title('Variant Quality Score Distribution', fontweight='bold')
ax3.legend()
plt.tight_layout()
plt.savefig('report/images/quality_distribution.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: report/images/quality_distribution.png")

# Figure 4: Depth Distribution
fig4, ax4 = plt.subplots(figsize=(10, 6))
depths = [v['depth'] for v in variants]
ax4.hist(depths, bins=30, color='#1abc9c', edgecolor='black', linewidth=1, alpha=0.8)
ax4.axvline(metrics['mean_depth'], color='red', linestyle='--', linewidth=2, label=f'Mean: {metrics["mean_depth"]:.1f}x')
ax4.set_xlabel('Read Depth')
ax4.set_ylabel('Frequency')
ax4.set_title('Read Depth Distribution', fontweight='bold')
ax4.legend()
plt.tight_layout()
plt.savefig('report/images/depth_distribution.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: report/images/depth_distribution.png")

# Figure 5: Chromosome Distribution
fig5, ax5 = plt.subplots(figsize=(12, 6))
chrom_counts = {}
for v in variants:
    chrom = v['chrom']
    chrom_counts[chrom] = chrom_counts.get(chrom, 0) + 1

# Sort chromosomes naturally
chrom_order = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', 
               '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', 'X', 'Y']
chrom_labels = []
chrom_values = []
for c in chrom_order:
    if c in chrom_counts:
        chrom_labels.append(f'chr{c}')
        chrom_values.append(chrom_counts[c])

x_pos = np.arange(len(chrom_labels))
ax5.bar(x_pos, chrom_values, color='#34495e', edgecolor='black', linewidth=1)
ax5.set_xticks(x_pos)
ax5.set_xticklabels(chrom_labels, rotation=45, ha='right')
ax5.set_xlabel('Chromosome')
ax5.set_ylabel('Variant Count')
ax5.set_title('Variant Distribution Across Chromosomes', fontweight='bold')
plt.tight_layout()
plt.savefig('report/images/chromosome_distribution.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: report/images/chromosome_distribution.png")

# Figure 6: dbSNP Annotation
fig6, ax6 = plt.subplots(figsize=(8, 6))
dbsnp_labels = ['In dbSNP', 'Novel']
dbsnp_counts = [metrics['in_dbsnp'], metrics['novel']]
colors3 = ['#16a085', '#c0392b']
bars3 = ax6.pie(dbsnp_counts, labels=dbsnp_labels, colors=colors3, autopct='%1.1f%%',
                startangle=90, explode=(0.05, 0.05), shadow=True)
ax6.set_title('dbSNP Annotation Status', fontweight='bold', pad=20)
plt.tight_layout()
plt.savefig('report/images/dbsnp_annotation.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: report/images/dbsnp_annotation.png")

# Figure 7: Genotype Quality vs Depth Scatter
fig7, ax7 = plt.subplots(figsize=(10, 6))
gq_scores = [v['gq'] for v in variants]
depth_vals = [v['depth'] for v in variants]
ax7.scatter(depth_vals, gq_scores, alpha=0.5, c='#8e44ad', s=30, edgecolors='black', linewidth=0.5)
ax7.set_xlabel('Read Depth')
ax7.set_ylabel('Genotype Quality')
ax7.set_title('Genotype Quality vs Read Depth', fontweight='bold')
ax7.set_ylim(0, 100)
plt.tight_layout()
plt.savefig('report/images/gq_vs_depth.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: report/images/gq_vs_depth.png")

# Figure 8: Indel Classification
fig8, ax8 = plt.subplots(figsize=(8, 6))
indel_types = ['Insertions', 'Deletions']
indel_counts = [metrics['insertions'], metrics['deletions']]
colors4 = ['#e67e22', '#9b59b6']
bars4 = ax8.bar(indel_types, indel_counts, color=colors4, edgecolor='black', linewidth=1.5)
ax8.set_ylabel('Count')
ax8.set_title('Indel Classification', fontweight='bold')
ax8.set_ylim(0, max(indel_counts) * 1.2)

for bar, count in zip(bars4, indel_counts):
    ax8.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, 
             f'{count}', ha='center', va='bottom', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig('report/images/indel_classification.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: report/images/indel_classification.png")

print("\nAll figures generated successfully!")
