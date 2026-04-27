"""CyberSecurity Incident Narrative Triage - Analysis Script"""

import os
import json
import re
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from collections import Counter

# ─────────────────────────────────────────────
# 1. LOAD & PREPROCESS
# ─────────────────────────────────────────────
df = pd.read_csv('data/incident_narratives.csv')
print("=== Raw Data ===")
print(df.to_string())
print()

# Minimal cleaning: strip whitespace, lowercase source_system
df['source_system'] = df['source_system'].str.strip().str.lower()
df['narrative_text'] = df['narrative_text'].str.strip()

# Derived features
df['word_count'] = df['narrative_text'].apply(lambda x: len(x.split()))
df['char_count'] = df['narrative_text'].apply(len)
df['narrative_lower'] = df['narrative_text'].str.lower()

print("=== Preprocessed DataFrame ===")
print(df[['incident_id','source_system','word_count','char_count']].to_string())
print()

# ─────────────────────────────────────────────
# 2. QUANTITATIVE SUMMARIES
# ─────────────────────────────────────────────

# 2a. Counts by source_system
counts_by_source = df['source_system'].value_counts().reset_index()
counts_by_source.columns = ['source_system', 'count']
print("=== Counts by source_system ===")
print(counts_by_source.to_string(index=False))
print()

# 2b. Response length stats by source_system
length_stats = df.groupby('source_system')[['word_count','char_count']].agg(['mean','min','max'])
print("=== Response Length Stats by source_system ===")
print(length_stats.to_string())
print()

# 2c. Keyword frequency analysis
# Define keyword categories relevant to cybersecurity triage
KEYWORD_CATEGORIES = {
    'execution': ['powershell', 'script', 'encoded', 'payload', 'process', 'explorer'],
    'lateral_movement': ['smb', 'subnet', 'lateral', 'session', 'internal'],
    'credential_access': ['login', 'admin', 'account', 'password', 'credential', 'failed'],
    'exfiltration': ['dns', 'tunneling', 'exfil', 'data', 'outbound', 'tls', 'domain'],
    'impact': ['ransomware', 'file', 'extension', 'mass', 'change', 'encrypt'],
    'response_action': ['blocked', 'disabled', 'reset', 'closed', 'applied', 'enabled', 'notified', 'queued', 'reimage', 'sinkhole', 'challenge'],
    'false_positive': ['false positive', 'fp', 'closed', 'backup', 'indexer'],
}

def count_keywords(text, keywords):
    """Count occurrences of any keyword in text (case-insensitive)."""
    count = 0
    for kw in keywords:
        count += len(re.findall(r'\b' + re.escape(kw) + r'\b', text, re.IGNORECASE))
    return count

for cat, kws in KEYWORD_CATEGORIES.items():
    df[f'kw_{cat}'] = df['narrative_lower'].apply(lambda t: count_keywords(t, kws))

kw_cols = [c for c in df.columns if c.startswith('kw_')]
print("=== Keyword Category Counts per Incident ===")
print(df[['incident_id','source_system'] + kw_cols].to_string(index=False))
print()

# 2d. Keyword totals by source_system
kw_by_source = df.groupby('source_system')[kw_cols].sum()
print("=== Keyword Category Totals by source_system ===")
print(kw_by_source.to_string())
print()

# 2e. Simple unigram frequency across all narratives
all_words = []
for text in df['narrative_lower']:
    tokens = re.findall(r'[a-z][a-z0-9\-]+', text)
    all_words.extend(tokens)

STOPWORDS = {'the','a','an','and','or','to','in','on','from','for','of','with',
             'at','by','is','was','are','were','be','been','as','it','its',
             'this','that','not','no','per','after','after','after'}
filtered_words = [w for w in all_words if w not in STOPWORDS and len(w) > 2]
word_freq = Counter(filtered_words).most_common(20)
print("=== Top 20 Unigrams (filtered) ===")
for word, freq in word_freq:
    print(f"  {word}: {freq}")
print()

# Save summaries to CSV
os.makedirs('outputs', exist_ok=True)
counts_by_source.to_csv('outputs/counts_by_source.csv', index=False)
length_stats.to_csv('outputs/length_stats_by_source.csv')
kw_by_source.to_csv('outputs/keyword_counts_by_source.csv')

word_freq_df = pd.DataFrame(word_freq, columns=['word','frequency'])
word_freq_df.to_csv('outputs/top_unigrams.csv', index=False)

print("Summaries saved to outputs/")

# ─────────────────────────────────────────────
# 3. FIGURES
# ─────────────────────────────────────────────
os.makedirs('report/images', exist_ok=True)

# Figure 1: Counts by source_system
fig, axes = plt.subplots(1, 3, figsize=(14, 5))
fig.suptitle('Incident Narrative Triage: Quantitative Summaries', fontsize=14, fontweight='bold')

# Panel A: Count by source_system
colors = {'edr': '#2196F3', 'network_ids': '#FF9800'}
ax = axes[0]
bars = ax.bar(counts_by_source['source_system'], counts_by_source['count'],
              color=[colors[s] for s in counts_by_source['source_system']], edgecolor='black', linewidth=0.8)
ax.set_title('A. Incident Count by Source System', fontweight='bold')
ax.set_xlabel('Source System')
ax.set_ylabel('Number of Incidents')
ax.set_ylim(0, max(counts_by_source['count']) + 1)
for bar, val in zip(bars, counts_by_source['count']):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05, str(val),
            ha='center', va='bottom', fontweight='bold')

# Panel B: Word count by source_system (individual points + mean)
ax2 = axes[1]
for src, grp in df.groupby('source_system'):
    ax2.scatter([src]*len(grp), grp['word_count'], color=colors[src], s=80, zorder=3, edgecolors='black', linewidth=0.5)
    ax2.hlines(grp['word_count'].mean(), -0.3 + list(colors.keys()).index(src),
               0.3 + list(colors.keys()).index(src), colors='black', linewidth=2, linestyle='--')
ax2.set_xticks(list(colors.keys()))
ax2.set_title('B. Narrative Word Count by Source System', fontweight='bold')
ax2.set_xlabel('Source System')
ax2.set_ylabel('Word Count')
ax2.set_ylim(0, max(df['word_count']) + 5)

# Panel C: Keyword category totals stacked bar
ax3 = axes[2]
category_labels = [c.replace('kw_','').replace('_',' ').title() for c in kw_cols]
bottom_edr = [0] * len(kw_cols)
bottom_net = [0] * len(kw_cols)

cmap = plt.cm.get_cmap('tab10', len(kw_cols))
for i, (col, label) in enumerate(zip(kw_cols, category_labels)):
    edr_val = kw_by_source.loc['edr', col] if 'edr' in kw_by_source.index else 0
    net_val = kw_by_source.loc['network_ids', col] if 'network_ids' in kw_by_source.index else 0
    ax3.bar(['EDR', 'Network IDS'], [edr_val, net_val], bottom=[bottom_edr[i], bottom_net[i]],
            color=cmap(i), label=label, edgecolor='white', linewidth=0.5)
    bottom_edr[i] = bottom_edr[i] + edr_val
    bottom_net[i] = bottom_net[i] + net_val

# Fix stacking
bottom_edr_vals = [0]
bottom_net_vals = [0]
ax3.cla()
for i, (col, label) in enumerate(zip(kw_cols, category_labels)):
    edr_val = int(kw_by_source.loc['edr', col]) if 'edr' in kw_by_source.index else 0
    net_val = int(kw_by_source.loc['network_ids', col]) if 'network_ids' in kw_by_source.index else 0
    ax3.bar(['EDR', 'Network IDS'], [edr_val, net_val],
            bottom=[bottom_edr_vals[-1], bottom_net_vals[-1]],
            color=cmap(i), label=label, edgecolor='white', linewidth=0.5)
    bottom_edr_vals.append(bottom_edr_vals[-1] + edr_val)
    bottom_net_vals.append(bottom_net_vals[-1] + net_val)

ax3.set_title('C. Keyword Categories by Source System', fontweight='bold')
ax3.set_xlabel('Source System')
ax3.set_ylabel('Keyword Hit Count')
ax3.legend(loc='upper right', fontsize=7, framealpha=0.8)

plt.tight_layout()
plt.savefig('report/images/triage_summary.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure saved: report/images/triage_summary.png")

# Figure 2: Top unigrams bar chart
fig2, ax = plt.subplots(figsize=(10, 6))
words_plot = [w for w, _ in word_freq[:15]]
freqs_plot = [f for _, f in word_freq[:15]]
bars = ax.barh(words_plot[::-1], freqs_plot[::-1], color='steelblue', edgecolor='black', linewidth=0.6)
ax.set_title('Top 15 Unigrams Across All Incident Narratives', fontsize=13, fontweight='bold')
ax.set_xlabel('Frequency')
ax.set_ylabel('Token')
for bar, val in zip(bars, freqs_plot[::-1]):
    ax.text(bar.get_width() + 0.02, bar.get_y() + bar.get_height()/2, str(val),
            va='center', fontsize=9)
plt.tight_layout()
plt.savefig('report/images/top_unigrams.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure saved: report/images/top_unigrams.png")

print("\nAnalysis complete.")
