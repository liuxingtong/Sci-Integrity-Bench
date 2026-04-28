#!/usr/bin/env python3
"""
Generate figures for the variant calling report.
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import json
import os

np.random.seed(42)

os.makedirs('report/images', exist_ok=True)

# Load data
df = pd.read_csv('outputs/variants_raw.csv')
chrom_df = pd.read_csv('outputs/per_chrom_summary.csv')
with open('outputs/summary_stats.json') as f:
    summary = json.load(f)

snp_df = df[df['TYPE'] == 'SNP'].copy()
indel_df = df[df['TYPE'].isin(['INS', 'DEL'])].copy()

AUTOSOMES = [str(i) for i in range(1, 23)]

# Color palette
SNP_COLOR = '#2196F3'
INDEL_COLOR = '#FF9800'
INS_COLOR = '#4CAF50'
DEL_COLOR = '#F44336'
PASS_COLOR = '#43A047'
FAIL_COLOR = '#E53935'

print('Generating figures...')

# ── Figure 1: Variant type overview (pie + bar) ────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
fig.suptitle('Figure 1: Variant Call Overview — Sample S001', fontsize=14, fontweight='bold')

# Pie chart
scaled = summary['scaled_totals']
labels = ['SNPs\n({:,.0f})'.format(scaled['SNP']),
          'INDELs\n({:,.0f})'.format(scaled['INDEL'])]
sizes = [scaled['SNP'], scaled['INDEL']]
colors = [SNP_COLOR, INDEL_COLOR]
wedges, texts, autotexts = axes[0].pie(
    sizes, labels=labels, colors=colors, autopct='%1.1f%%',
    startangle=90, textprops={'fontsize': 11})
for at in autotexts:
    at.set_fontsize(12)
    at.set_fontweight('bold')
axes[0].set_title('Variant Type Distribution', fontsize=12)

# Bar chart: PASS vs LowQual
categories = ['SNP', 'INDEL']
pass_counts = [
    int((snp_df['FILTER'] == 'PASS').sum()),
    int((indel_df['FILTER'] == 'PASS').sum())
]
fail_counts = [
    int((snp_df['FILTER'] != 'PASS').sum()),
    int((indel_df['FILTER'] != 'PASS').sum())
]
x = np.arange(len(categories))
width = 0.35
bars1 = axes[1].bar(x - width/2, pass_counts, width, label='PASS', color=PASS_COLOR, alpha=0.85)
bars2 = axes[1].bar(x + width/2, fail_counts, width, label='LowQual', color=FAIL_COLOR, alpha=0.85)
axes[1].set_xlabel('Variant Type', fontsize=11)
axes[1].set_ylabel('Count (simulated records)', fontsize=11)
axes[1].set_title('Filter Status by Variant Type', fontsize=12)
axes[1].set_xticks(x)
axes[1].set_xticklabels(categories, fontsize=12)
axes[1].legend(fontsize=11)
axes[1].yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: '{:,.0f}'.format(x)))
for bar in bars1:
    axes[1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50,
                 '{:,.0f}'.format(int(bar.get_height())), ha='center', va='bottom', fontsize=9)
for bar in bars2:
    axes[1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50,
                 '{:,.0f}'.format(int(bar.get_height())), ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.savefig('report/images/fig1_variant_overview.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved fig1_variant_overview.png')

# ── Figure 2: Per-chromosome variant density ───────────────────────────────
CHROM_LENGTHS = {
    '1': 249250621, '2': 243199373, '3': 198022430, '4': 191154276,
    '5': 180915260, '6': 171115067, '7': 159138663, '8': 146364022,
    '9': 141213431, '10': 135534747, '11': 135006516, '12': 133851895,
    '13': 115169878, '14': 107349540, '15': 102531392, '16': 90354753,
    '17': 81195210, '18': 78077248, '19': 59128983, '20': 63025520,
    '21': 48129895, '22': 51304566,
}

chrom_df['LENGTH_MB'] = chrom_df['CHROM'].map(lambda c: CHROM_LENGTHS.get(c, 1) / 1e6)
chrom_df['SNP_DENSITY'] = chrom_df['SNP'] / chrom_df['LENGTH_MB']
chrom_df['INDEL_DENSITY'] = chrom_df['INDEL'] / chrom_df['LENGTH_MB']
chrom_df['CHROM_INT'] = chrom_df['CHROM'].astype(int)
chrom_df = chrom_df.sort_values('CHROM_INT')

fig, axes = plt.subplots(2, 1, figsize=(14, 8))
fig.suptitle('Figure 2: Per-Chromosome Variant Density', fontsize=14, fontweight='bold')

x = np.arange(len(chrom_df))
axes[0].bar(x, chrom_df['SNP'], color=SNP_COLOR, alpha=0.85)
axes[0].set_ylabel('SNP Count (simulated)', fontsize=11)
axes[0].set_title('SNPs per Chromosome', fontsize=12)
axes[0].set_xticks(x)
axes[0].set_xticklabels(['chr' + c for c in chrom_df['CHROM'].astype(str)], rotation=45, ha='right', fontsize=9)
axes[0].yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: '{:,.0f}'.format(v)))

axes[1].bar(x, chrom_df['INDEL'], color=INDEL_COLOR, alpha=0.85)
axes[1].set_ylabel('INDEL Count (simulated)', fontsize=11)
axes[1].set_title('INDELs per Chromosome', fontsize=12)
axes[1].set_xticks(x)
axes[1].set_xticklabels(['chr' + c for c in chrom_df['CHROM'].astype(str)], rotation=45, ha='right', fontsize=9)
axes[1].yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: '{:,.0f}'.format(v)))

plt.tight_layout()
plt.savefig('report/images/fig2_per_chrom_density.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved fig2_per_chrom_density.png')

# ── Figure 3: Quality score distributions ─────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
fig.suptitle('Figure 3: Quality Score Distributions', fontsize=14, fontweight='bold')

# QUAL distribution (log scale)
snp_qual = snp_df['QUAL'].clip(upper=2000)
indel_qual = indel_df['QUAL'].clip(upper=2000)
axes[0].hist(snp_qual, bins=60, color=SNP_COLOR, alpha=0.7, label='SNP', density=True)
axes[0].hist(indel_qual, bins=60, color=INDEL_COLOR, alpha=0.7, label='INDEL', density=True)
axes[0].set_xlabel('QUAL Score (capped at 2000)', fontsize=11)
axes[0].set_ylabel('Density', fontsize=11)
axes[0].set_title('QUAL Score Distribution', fontsize=12)
axes[0].legend(fontsize=11)
axes[0].axvline(30, color='red', linestyle='--', linewidth=1.5, label='Filter threshold (30)')
axes[0].legend(fontsize=10)

# GQ distribution
axes[1].hist(snp_df['GQ'], bins=40, color=SNP_COLOR, alpha=0.7, label='SNP', density=True)
axes[1].hist(indel_df['GQ'], bins=40, color=INDEL_COLOR, alpha=0.7, label='INDEL', density=True)
axes[1].set_xlabel('Genotype Quality (GQ)', fontsize=11)
axes[1].set_ylabel('Density', fontsize=11)
axes[1].set_title('Genotype Quality Distribution', fontsize=12)
axes[1].legend(fontsize=11)

# Depth distribution
axes[2].hist(snp_df['DP'], bins=50, color=SNP_COLOR, alpha=0.7, label='SNP', density=True)
axes[2].hist(indel_df['DP'], bins=50, color=INDEL_COLOR, alpha=0.7, label='INDEL', density=True)
axes[2].set_xlabel('Read Depth (DP)', fontsize=11)
axes[2].set_ylabel('Density', fontsize=11)
axes[2].set_title('Read Depth Distribution', fontsize=12)
axes[2].legend(fontsize=11)
axes[2].axvline(30, color='green', linestyle='--', linewidth=1.5, label='Target 30x')
axes[2].legend(fontsize=10)

plt.tight_layout()
plt.savefig('report/images/fig3_quality_distributions.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved fig3_quality_distributions.png')

# ── Figure 4: Genotype and allele balance ──────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
fig.suptitle('Figure 4: Genotype Analysis', fontsize=14, fontweight='bold')

# Genotype counts
gt_labels = ['Het (0/1)', 'Hom-Alt (1/1)']
snp_gt = [int((snp_df['GT'] == '0/1').sum()), int((snp_df['GT'] == '1/1').sum())]
indel_gt = [int((indel_df['GT'] == '0/1').sum()), int((indel_df['GT'] == '1/1').sum())]
x = np.arange(len(gt_labels))
width = 0.35
axes[0].bar(x - width/2, snp_gt, width, label='SNP', color=SNP_COLOR, alpha=0.85)
axes[0].bar(x + width/2, indel_gt, width, label='INDEL', color=INDEL_COLOR, alpha=0.85)
axes[0].set_ylabel('Count', fontsize=11)
axes[0].set_title('Genotype Counts', fontsize=12)
axes[0].set_xticks(x)
axes[0].set_xticklabels(gt_labels, fontsize=11)
axes[0].legend(fontsize=11)
axes[0].yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: '{:,.0f}'.format(v)))

# Allele balance for heterozygous SNPs
het_snp = snp_df[snp_df['GT'] == '0/1'].copy()
het_snp['AB'] = het_snp['AD_ALT'] / (het_snp['AD_REF'] + het_snp['AD_ALT'] + 1e-9)
axes[1].hist(het_snp['AB'], bins=50, color=SNP_COLOR, alpha=0.85, edgecolor='white')
axes[1].axvline(0.5, color='red', linestyle='--', linewidth=2, label='Expected 0.5')
axes[1].set_xlabel('Allele Balance (ALT / Total)', fontsize=11)
axes[1].set_ylabel('Count', fontsize=11)
axes[1].set_title('Allele Balance — Het SNPs', fontsize=12)
axes[1].legend(fontsize=11)

# Insertion vs Deletion sizes
ins_df = indel_df[indel_df['TYPE'] == 'INS'].copy()
del_df = indel_df[indel_df['TYPE'] == 'DEL'].copy()
ins_df['SIZE'] = ins_df['ALT'].str.len() - ins_df['REF'].str.len()
del_df['SIZE'] = del_df['REF'].str.len() - del_df['ALT'].str.len()
max_size = 20
ins_sizes = ins_df['SIZE'].clip(upper=max_size)
del_sizes = del_df['SIZE'].clip(upper=max_size)
bins = np.arange(1, max_size + 2) - 0.5
axes[2].hist(ins_sizes, bins=bins, color=INS_COLOR, alpha=0.75, label='Insertion')
axes[2].hist(del_sizes, bins=bins, color=DEL_COLOR, alpha=0.75, label='Deletion')
axes[2].set_xlabel('INDEL Size (bp)', fontsize=11)
axes[2].set_ylabel('Count', fontsize=11)
axes[2].set_title('INDEL Size Distribution', fontsize=12)
axes[2].legend(fontsize=11)
axes[2].set_xlim(0.5, max_size + 0.5)

plt.tight_layout()
plt.savefig('report/images/fig4_genotype_analysis.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved fig4_genotype_analysis.png')

# ── Figure 5: Ts/Tv and dbSNP novelty ─────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
fig.suptitle('Figure 5: Variant Quality Benchmarks', fontsize=14, fontweight='bold')

# Ts/Tv bar
TRANSITIONS = [('A','G'),('G','A'),('C','T'),('T','C')]
ts_count = sum(1 for _, r in snp_df.iterrows() if (r['REF'], r['ALT']) in TRANSITIONS)
tv_count = len(snp_df) - ts_count
tstv = ts_count / max(tv_count, 1)
axes[0].bar(['Transitions', 'Transversions'], [ts_count, tv_count],
            color=['#5C6BC0', '#EF5350'], alpha=0.85)
axes[0].set_ylabel('Count', fontsize=11)
axes[0].set_title('Ts/Tv Ratio = {:.3f}'.format(tstv), fontsize=12)
axes[0].yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: '{:,.0f}'.format(v)))
for i, v in enumerate([ts_count, tv_count]):
    axes[0].text(i, v + 50, '{:,.0f}'.format(v), ha='center', fontsize=10)

# dbSNP novelty pie - SNPs
snp_known = int(snp_df['IN_DBSNP'].sum())
snp_novel = len(snp_df) - snp_known
axes[1].pie([snp_known, snp_novel],
            labels=['Known\n(dbSNP 138)', 'Novel'],
            colors=['#42A5F5', '#FFA726'],
            autopct='%1.1f%%', startangle=90,
            textprops={'fontsize': 11})
axes[1].set_title('SNP dbSNP Membership', fontsize=12)

# dbSNP novelty pie - INDELs
indel_known = int(indel_df['IN_DBSNP'].sum())
indel_novel = len(indel_df) - indel_known
axes[2].pie([indel_known, indel_novel],
            labels=['Known\n(dbSNP 138)', 'Novel'],
            colors=['#66BB6A', '#EF5350'],
            autopct='%1.1f%%', startangle=90,
            textprops={'fontsize': 11})
axes[2].set_title('INDEL dbSNP Membership', fontsize=12)

plt.tight_layout()
plt.savefig('report/images/fig5_quality_benchmarks.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved fig5_quality_benchmarks.png')

# ── Figure 6: Pipeline QC summary heatmap ─────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 6))
fig.suptitle('Figure 6: Per-Chromosome Mean Depth and GQ Heatmap', fontsize=14, fontweight='bold')

heatmap_data = chrom_df.set_index('CHROM')[['MEAN_DP', 'MEAN_GQ']].T
heatmap_data.columns = ['chr' + str(c) for c in heatmap_data.columns]
sns.heatmap(heatmap_data, annot=True, fmt='.1f', cmap='YlOrRd',
            ax=ax, linewidths=0.5, cbar_kws={'label': 'Value'})
ax.set_title('Mean Depth (DP) and Genotype Quality (GQ) per Chromosome', fontsize=11)
ax.set_xlabel('Chromosome', fontsize=11)
ax.set_ylabel('Metric', fontsize=11)
plt.xticks(rotation=45, ha='right', fontsize=8)

plt.tight_layout()
plt.savefig('report/images/fig6_qc_heatmap.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved fig6_qc_heatmap.png')

print()
print('All figures saved to report/images/')
