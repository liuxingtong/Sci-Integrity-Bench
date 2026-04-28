"""Step 3: Generate figures for the report."""

import pandas as pd
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import numpy as np
import os

OUT_DIR = "outputs"
IMG_DIR = "report/images"
os.makedirs(IMG_DIR, exist_ok=True)

# ── Load data ──────────────────────────────────────────────────────────────
df = pd.read_csv(f"{OUT_DIR}/processed_interviews.csv")
with open(f"{OUT_DIR}/descriptive_summary.json") as f:
    summary = json.load(f)

TOPICS = ["reliability","information","safety","pricing","accessibility",
          "crowding","multimodal","trust","ux_design"]

COHORT_COLORS = {"transit_primary": "#2196F3", "car_primary": "#FF5722"}
COHORT_LABELS = {"transit_primary": "Transit-Primary", "car_primary": "Car-Primary"}

# ─────────────────────────────────────────────────────────────────────────
# Figure 1: Topic mention rates by cohort (grouped bar chart)
# ─────────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 6))

cohorts = ["transit_primary", "car_primary"]
topic_labels = [t.replace("_", "\n") for t in TOPICS]
x = np.arange(len(TOPICS))
width = 0.35

for i, cohort in enumerate(cohorts):
    rates = [summary["topic_mention_rates"][cohort][t] for t in TOPICS]
    bars = ax.bar(x + i*width - width/2, rates, width,
                  label=COHORT_LABELS[cohort],
                  color=COHORT_COLORS[cohort], alpha=0.85, edgecolor='white')
    for bar, rate in zip(bars, rates):
        if rate > 0:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f"{rate:.0%}", ha='center', va='bottom', fontsize=8, fontweight='bold')

ax.set_xlabel("Topic", fontsize=12)
ax.set_ylabel("Proportion of Respondents Mentioning Topic", fontsize=12)
ax.set_title("Topic Mention Rates by Cohort", fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(topic_labels, fontsize=9)
ax.set_ylim(0, 1.1)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0%}"))
ax.legend(fontsize=11)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig(f"{IMG_DIR}/fig1_topic_mention_rates.png", dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig1_topic_mention_rates.png")

# ─────────────────────────────────────────────────────────────────────────
# Figure 2: Response length distribution (word count) by cohort
# ─────────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Left: strip + box plot
for cohort in cohorts:
    sub = df[df["cohort"] == cohort]["word_count"]
    x_pos = cohorts.index(cohort)
    axes[0].boxplot(sub, positions=[x_pos], widths=0.4,
                    patch_artist=True,
                    boxprops=dict(facecolor=COHORT_COLORS[cohort], alpha=0.6),
                    medianprops=dict(color='black', linewidth=2),
                    whiskerprops=dict(linewidth=1.5),
                    capprops=dict(linewidth=1.5),
                    flierprops=dict(marker='o', markersize=5))
    jitter = np.random.default_rng(42).uniform(-0.1, 0.1, len(sub))
    axes[0].scatter(np.full(len(sub), x_pos) + jitter, sub,
                    color=COHORT_COLORS[cohort], alpha=0.8, zorder=5, s=60)

axes[0].set_xticks([0, 1])
axes[0].set_xticklabels([COHORT_LABELS[c] for c in cohorts], fontsize=11)
axes[0].set_ylabel("Word Count per Response", fontsize=11)
axes[0].set_title("Response Length Distribution", fontsize=13, fontweight='bold')
axes[0].spines['top'].set_visible(False)
axes[0].spines['right'].set_visible(False)
axes[0].grid(axis='y', alpha=0.3)

# Right: cumulative topic mentions per respondent
df["total_topics"] = df[[f"flag_{t}" for t in TOPICS]].sum(axis=1)
for cohort in cohorts:
    sub = df[df["cohort"] == cohort]["total_topics"]
    axes[1].hist(sub, bins=range(0, 8), alpha=0.65,
                 color=COHORT_COLORS[cohort],
                 label=COHORT_LABELS[cohort],
                 edgecolor='white', align='left')

axes[1].set_xlabel("Number of Distinct Topics Mentioned", fontsize=11)
axes[1].set_ylabel("Number of Respondents", fontsize=11)
axes[1].set_title("Topic Breadth per Respondent", fontsize=13, fontweight='bold')
axes[1].legend(fontsize=10)
axes[1].spines['top'].set_visible(False)
axes[1].spines['right'].set_visible(False)
axes[1].grid(axis='y', alpha=0.3)
axes[1].xaxis.set_major_locator(plt.MaxNLocator(integer=True))

plt.tight_layout()
plt.savefig(f"{IMG_DIR}/fig2_response_characteristics.png", dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig2_response_characteristics.png")

# ─────────────────────────────────────────────────────────────────────────
# Figure 3: Heatmap of topic presence per respondent
# ─────────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(11, 7))

# Build matrix: rows = respondents, cols = topics
df_sorted = df.sort_values(["cohort","respondent_id"]).reset_index(drop=True)
matrix = df_sorted[[f"flag_{t}" for t in TOPICS]].values
row_labels = [f"{row['respondent_id']} ({COHORT_LABELS[row['cohort']].split('-')[0]})"
              for _, row in df_sorted.iterrows()]
col_labels = [t.replace("_", "\n") for t in TOPICS]

cmap = plt.cm.Blues
im = ax.imshow(matrix, cmap=cmap, aspect='auto', vmin=0, vmax=1)

ax.set_xticks(range(len(TOPICS)))
ax.set_xticklabels(col_labels, fontsize=9)
ax.set_yticks(range(len(df_sorted)))
ax.set_yticklabels(row_labels, fontsize=8)
ax.set_title("Topic Presence per Respondent", fontsize=14, fontweight='bold')

# Add cohort separator line
car_count = (df_sorted["cohort"] == "car_primary").sum()
transit_count = (df_sorted["cohort"] == "transit_primary").sum()
ax.axhline(car_count - 0.5, color='red', linewidth=2, linestyle='--', alpha=0.7)
ax.text(len(TOPICS) - 0.3, car_count/2 - 0.5, 'Car-Primary',
        va='center', ha='right', fontsize=9, color='#FF5722', fontweight='bold')
ax.text(len(TOPICS) - 0.3, car_count + transit_count/2 - 0.5, 'Transit-Primary',
        va='center', ha='right', fontsize=9, color='#2196F3', fontweight='bold')

# Cell annotations
for i in range(matrix.shape[0]):
    for j in range(matrix.shape[1]):
        ax.text(j, i, '✓' if matrix[i,j] else '', ha='center', va='center',
                fontsize=10, color='white' if matrix[i,j] else 'lightgray')

plt.colorbar(im, ax=ax, shrink=0.6, label='Topic Mentioned (1=Yes)')
plt.tight_layout()
plt.savefig(f"{IMG_DIR}/fig3_topic_heatmap.png", dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig3_topic_heatmap.png")

# ─────────────────────────────────────────────────────────────────────────
# Figure 4: Top words comparison (horizontal bar)
# ─────────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

for ax, cohort in zip(axes, cohorts):
    words_counts = summary["top_words"][cohort][:12]
    words = [wc[0] for wc in words_counts]
    counts = [wc[1] for wc in words_counts]
    y_pos = range(len(words))
    bars = ax.barh(y_pos, counts, color=COHORT_COLORS[cohort], alpha=0.8, edgecolor='white')
    ax.set_yticks(y_pos)
    ax.set_yticklabels(words, fontsize=10)
    ax.invert_yaxis()
    ax.set_xlabel("Frequency", fontsize=11)
    ax.set_title(f"Top Words — {COHORT_LABELS[cohort]}", fontsize=12, fontweight='bold')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='x', alpha=0.3)
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    for bar, count in zip(bars, counts):
        ax.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height()/2,
                str(count), va='center', fontsize=9)

plt.suptitle("Most Frequent Content Words by Cohort", fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(f"{IMG_DIR}/fig4_top_words.png", dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig4_top_words.png")

print("\n✓ All figures saved to report/images/")
