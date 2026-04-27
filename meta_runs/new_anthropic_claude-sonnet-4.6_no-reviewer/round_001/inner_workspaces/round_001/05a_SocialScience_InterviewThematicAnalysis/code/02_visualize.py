"""Step 2: Generate figures for the report."""

import json
import os
import re
from collections import Counter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

OUT_DIR = "outputs"
IMG_DIR = "report/images"
os.makedirs(IMG_DIR, exist_ok=True)

with open(f"{OUT_DIR}/preprocessing_summary.json", encoding="utf-8") as f:
    summary = json.load(f)

respondents = summary["respondents"]
cohorts = ["transit_primary", "car_primary"]
colors = {"transit_primary": "#2196F3", "car_primary": "#FF5722"}
labels = {"transit_primary": "Transit-Primary", "car_primary": "Car-Primary"}

# ── Figure 1: Cohort distribution bar chart ────────────────────────────────
fig, ax = plt.subplots(figsize=(6, 4))
cohort_names = [labels[c] for c in cohorts]
cohort_vals  = [summary["cohort_counts"][c] for c in cohorts]
bars = ax.bar(cohort_names, cohort_vals,
              color=[colors[c] for c in cohorts],
              edgecolor="white", linewidth=1.2, width=0.5)
for bar, val in zip(bars, cohort_vals):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
            str(val), ha="center", va="bottom", fontsize=13, fontweight="bold")
ax.set_ylabel("Number of Respondents", fontsize=11)
ax.set_title("Respondents by Cohort", fontsize=13, fontweight="bold")
ax.set_ylim(0, max(cohort_vals) + 2)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
plt.tight_layout()
plt.savefig(f"{IMG_DIR}/fig1_cohort_distribution.png", dpi=150)
plt.close()
print("Saved fig1_cohort_distribution.png")

# ── Figure 2: Response word-count distribution by cohort ──────────────────
fig, ax = plt.subplots(figsize=(7, 4))
for cohort in cohorts:
    wcs = [r["word_count"] for r in respondents if r["cohort"] == cohort]
    ax.hist(wcs, bins=range(14, 30), alpha=0.65,
            color=colors[cohort], label=labels[cohort],
            edgecolor="white", linewidth=0.8)
ax.set_xlabel("Word Count per Response", fontsize=11)
ax.set_ylabel("Frequency", fontsize=11)
ax.set_title("Distribution of Response Lengths by Cohort", fontsize=13, fontweight="bold")
ax.legend(fontsize=10)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
plt.tight_layout()
plt.savefig(f"{IMG_DIR}/fig2_response_lengths.png", dpi=150)
plt.close()
print("Saved fig2_response_lengths.png")

# ── Figure 3: Top-10 words per cohort (side-by-side horizontal bars) ───────
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
for ax, cohort in zip(axes, cohorts):
    top = summary["cohort_top15"][cohort][:10]
    words = [w for w, _ in top]
    counts = [c for _, c in top]
    y_pos = range(len(words))
    ax.barh(y_pos, counts, color=colors[cohort], edgecolor="white", linewidth=0.8)
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(words, fontsize=11)
    ax.invert_yaxis()
    ax.set_xlabel("Frequency", fontsize=10)
    ax.set_title(f"Top Words — {labels[cohort]}", fontsize=12, fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
plt.suptitle("Most Frequent Content Words by Cohort", fontsize=13, fontweight="bold", y=1.01)
plt.tight_layout()
plt.savefig(f"{IMG_DIR}/fig3_top_words_by_cohort.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved fig3_top_words_by_cohort.png")

# ── Figure 4: UX concern category heatmap (manual keyword tagging) ─────────
# Define concern categories and keywords
categories = {
    "Real-time Info": ["arrival", "board", "delay", "delays", "alert", "alerts", "live", "wrong", "honest", "explanation", "generic", "erode", "trust"],
    "Crowding & Safety": ["crowding", "unsafe", "platform", "safety", "lighting", "cctv", "scary", "lot", "skip"],
    "Pricing & Cost": ["pricing", "opaque", "caps", "discounts", "costs", "fare", "fuel", "weekly", "comparison", "cheapest", "price"],
    "Navigation & Maps": ["map", "routing", "transfers", "station", "names", "reconcile", "exit", "corner", "line", "trip", "plan", "legs", "stitch"],
    "Accessibility": ["accessibility", "elevator", "outages", "buried", "offline", "signal", "tunnels", "mode"],
    "Multimodal Integration": ["bike", "docks", "park", "ride", "carpool", "matching", "driving", "train", "transit", "alternatives", "strike"],
    "UI / Interface": ["interface", "crowded", "buttons", "home", "screen", "clutter", "menus", "banners", "feed", "prompts", "app"],
}

def score_text(text, keywords):
    text_lower = text.lower()
    return sum(1 for kw in keywords if kw in text_lower)

heatmap_data = np.zeros((len(categories), len(cohorts)))
cat_names = list(categories.keys())
for ci, cohort in enumerate(cohorts):
    texts = [r["response_text"] for r in respondents if r["cohort"] == cohort]
    for ri, (cat, kws) in enumerate(categories.items()):
        total = sum(score_text(t, kws) for t in texts)
        heatmap_data[ri, ci] = total

fig, ax = plt.subplots(figsize=(7, 6))
im = ax.imshow(heatmap_data, cmap="YlOrRd", aspect="auto")
ax.set_xticks([0, 1])
ax.set_xticklabels([labels[c] for c in cohorts], fontsize=11)
ax.set_yticks(range(len(cat_names)))
ax.set_yticklabels(cat_names, fontsize=10)
for i in range(len(cat_names)):
    for j in range(len(cohorts)):
        val = int(heatmap_data[i, j])
        ax.text(j, i, str(val), ha="center", va="center",
                fontsize=12, fontweight="bold",
                color="white" if heatmap_data[i, j] > heatmap_data.max()*0.6 else "black")
plt.colorbar(im, ax=ax, label="Keyword Hit Count")
ax.set_title("UX Concern Categories by Cohort\n(keyword-based scoring)",
             fontsize=12, fontweight="bold")
plt.tight_layout()
plt.savefig(f"{IMG_DIR}/fig4_concern_heatmap.png", dpi=150)
plt.close()
print("Saved fig4_concern_heatmap.png")

print("\nAll figures saved.")
