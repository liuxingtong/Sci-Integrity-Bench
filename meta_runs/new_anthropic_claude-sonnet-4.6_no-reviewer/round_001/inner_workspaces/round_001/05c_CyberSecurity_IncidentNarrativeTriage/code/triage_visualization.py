"""Additional triage visualization using LLM output."""

import json
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

# Load data
df = pd.read_csv('data/incident_narratives.csv')
df['source_system'] = df['source_system'].str.strip().str.lower()

# Load LLM output
with open('outputs/gemini_raw.json', 'r', encoding='utf-8') as f:
    gemini_data = json.load(f)

parsed = gemini_data['parsed']

# Build triage dataframe
label_assignments = parsed['label_assignments']
priority_ranking = parsed['priority_ranking']

triage_df = pd.DataFrame(label_assignments)
priority_df = pd.DataFrame(priority_ranking)

# Merge
triage_df = triage_df.merge(priority_df[['incident_id','rank']], on='incident_id')
triage_df = triage_df.merge(df[['incident_id','source_system']], on='incident_id')
triage_df = triage_df.sort_values('rank')

print("=== Triage Summary Table ===")
print(triage_df[['rank','incident_id','source_system','label']].to_string(index=False))

# Save triage table
triage_df.to_csv('outputs/triage_assignments.csv', index=False)

# ─────────────────────────────────────────────
# Figure 3: Comprehensive triage dashboard
# ─────────────────────────────────────────────
os.makedirs('report/images', exist_ok=True)

# Color maps
label_colors = {
    'T1_ACTIVE_THREAT':    '#D32F2F',  # red
    'T2_LATERAL_MOVEMENT': '#F57C00',  # orange
    'T3_EXFILTRATION_RISK':'#FBC02D',  # yellow
    'T4_CREDENTIAL_ABUSE': '#7B1FA2',  # purple
    'T5_FALSE_POSITIVE':   '#388E3C',  # green
}
source_colors = {'edr': '#2196F3', 'network_ids': '#FF9800'}

fig = plt.figure(figsize=(16, 10))
fig.suptitle('Incident Narrative Triage Dashboard', fontsize=16, fontweight='bold', y=0.98)

# ── Panel A: Priority ranking with triage labels (left, tall)
ax1 = fig.add_subplot(2, 3, (1, 4))  # spans rows 1-2, col 1

y_positions = list(range(len(triage_df)))
labels_list = triage_df['label'].tolist()
incidents = triage_df['incident_id'].tolist()
sources = triage_df['source_system'].tolist()
ranks = triage_df['rank'].tolist()

for i, (inc, lbl, src, rank) in enumerate(zip(incidents, labels_list, sources, ranks)):
    color = label_colors.get(lbl, 'gray')
    # Priority bar
    bar_width = (7 - rank) / 6  # rank 1 = widest
    ax1.barh(i, bar_width, color=color, alpha=0.85, edgecolor='black', linewidth=0.8, height=0.6)
    # Source system marker
    ax1.scatter(bar_width + 0.02, i, color=source_colors[src], s=120, zorder=5,
                marker='D' if src == 'edr' else 'o', edgecolors='black', linewidth=0.8)
    ax1.text(0.02, i, f"Rank {rank}: {inc}", va='center', fontsize=10, fontweight='bold', color='white')
    ax1.text(bar_width - 0.02, i, lbl.replace('_', ' '), va='center', ha='right',
             fontsize=8, color='white', alpha=0.9)

ax1.set_yticks(y_positions)
ax1.set_yticklabels([f"{inc}" for inc in incidents], fontsize=10)
ax1.set_xlim(0, 1.15)
ax1.set_xlabel('Relative Priority (wider = higher priority)', fontsize=9)
ax1.set_title('A. Priority Ranking with Triage Labels', fontweight='bold', fontsize=11)
ax1.invert_yaxis()

# Legend for labels
label_patches = [mpatches.Patch(color=c, label=l.replace('_',' ')) for l, c in label_colors.items()]
src_patches = [
    mpatches.Patch(color=source_colors['edr'], label='EDR (diamond)'),
    mpatches.Patch(color=source_colors['network_ids'], label='Network IDS (circle)')
]
ax1.legend(handles=label_patches + src_patches, loc='lower right', fontsize=7.5,
           framealpha=0.9, title='Labels & Sources', title_fontsize=8)

# ── Panel B: Label distribution (top center)
ax2 = fig.add_subplot(2, 3, 2)
label_counts = triage_df['label'].value_counts()
colors_pie = [label_colors.get(l, 'gray') for l in label_counts.index]
wedges, texts, autotexts = ax2.pie(
    label_counts.values,
    labels=[l.replace('_','\n') for l in label_counts.index],
    colors=colors_pie,
    autopct='%1.0f%%',
    startangle=90,
    textprops={'fontsize': 8}
)
for at in autotexts:
    at.set_fontsize(9)
    at.set_fontweight('bold')
ax2.set_title('B. Triage Label Distribution', fontweight='bold', fontsize=11)

# ── Panel C: Source system vs label heatmap (top right)
ax3 = fig.add_subplot(2, 3, 3)
cross = pd.crosstab(triage_df['source_system'], triage_df['label'])
# Ensure all labels present
for lbl in label_colors:
    if lbl not in cross.columns:
        cross[lbl] = 0
cross = cross[sorted(cross.columns)]

im = ax3.imshow(cross.values, cmap='YlOrRd', aspect='auto', vmin=0, vmax=2)
ax3.set_xticks(range(len(cross.columns)))
ax3.set_xticklabels([c.replace('_','\n') for c in cross.columns], fontsize=7)
ax3.set_yticks(range(len(cross.index)))
ax3.set_yticklabels(cross.index, fontsize=9)
ax3.set_title('C. Source System × Triage Label', fontweight='bold', fontsize=11)
plt.colorbar(im, ax=ax3, shrink=0.8, label='Count')
for i in range(len(cross.index)):
    for j in range(len(cross.columns)):
        val = cross.values[i, j]
        ax3.text(j, i, str(val), ha='center', va='center', fontsize=12, fontweight='bold',
                 color='black' if val < 1.5 else 'white')

# ── Panel D: Keyword category radar / bar (bottom center)
ax4 = fig.add_subplot(2, 3, 5)
kw_df = pd.read_csv('outputs/keyword_counts_by_source.csv', index_col=0)
categories = [c.replace('kw_','').replace('_',' ').title() for c in kw_df.columns]
x = np.arange(len(categories))
width = 0.35
bars1 = ax4.bar(x - width/2, kw_df.loc['edr'].values if 'edr' in kw_df.index else [0]*len(categories),
                width, label='EDR', color='#2196F3', edgecolor='black', linewidth=0.6)
bars2 = ax4.bar(x + width/2, kw_df.loc['network_ids'].values if 'network_ids' in kw_df.index else [0]*len(categories),
                width, label='Network IDS', color='#FF9800', edgecolor='black', linewidth=0.6)
ax4.set_xticks(x)
ax4.set_xticklabels(categories, rotation=35, ha='right', fontsize=7.5)
ax4.set_ylabel('Keyword Hit Count')
ax4.set_title('D. Keyword Categories by Source System', fontweight='bold', fontsize=11)
ax4.legend(fontsize=9)
ax4.set_ylim(0, max(kw_df.values.max() + 1, 6))

# ── Panel E: Word count distribution (bottom right)
ax5 = fig.add_subplot(2, 3, 6)
df['word_count'] = df['narrative_text'].apply(lambda x: len(x.split()))
for src, grp in df.groupby('source_system'):
    ax5.scatter(grp.index, grp['word_count'], color=source_colors[src], s=100,
                label=src.upper().replace('_',' '), zorder=3, edgecolors='black', linewidth=0.7)
    ax5.hlines(grp['word_count'].mean(), grp.index.min()-0.3, grp.index.max()+0.3,
               colors=source_colors[src], linewidth=2, linestyle='--', alpha=0.7)
ax5.set_xticks(df.index)
ax5.set_xticklabels(df['incident_id'], rotation=30, fontsize=8)
ax5.set_ylabel('Word Count')
ax5.set_title('E. Narrative Length by Incident', fontweight='bold', fontsize=11)
ax5.legend(fontsize=9)
ax5.set_ylim(0, max(df['word_count']) + 5)

plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.savefig('report/images/triage_dashboard.png', dpi=150, bbox_inches='tight')
plt.close()
print("Dashboard saved: report/images/triage_dashboard.png")

print("\nVisualization complete.")
