"""Step 4: Generate theme summary figure from LLM thematic analysis."""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os

IMG_DIR = "report/images"
os.makedirs(IMG_DIR, exist_ok=True)

# Themes identified by LLM with respondent counts per cohort
themes = [
    "Reliability of\nInformation",
    "Safety &\nSecurity",
    "Integrated\nMultimodal",
    "Cost\nTransparency",
    "Interface\nPersonalization",
    "Accessibility &\nInclusion",
]

# Respondents per theme per cohort (from LLM output)
# transit_primary respondents: INT-01..INT-09
# car_primary respondents: INT-10..INT-18
transit_counts = [3, 2, 2, 1, 1, 2]  # INT-01,08,05 | INT-02,04 | INT-07,09 | INT-03 | INT-06 | INT-05,06
car_counts     = [3, 1, 2, 2, 2, 0]  # INT-10,17,18 | INT-13 | INT-12,15 | INT-10,15 | INT-16,14 | none

x = np.arange(len(themes))
width = 0.35

fig, ax = plt.subplots(figsize=(11, 5))
bars1 = ax.bar(x - width/2, transit_counts, width, label="Transit-Primary",
               color="#2196F3", edgecolor="white", linewidth=0.8)
bars2 = ax.bar(x + width/2, car_counts, width, label="Car-Primary",
               color="#FF5722", edgecolor="white", linewidth=0.8)

for bar in bars1:
    h = bar.get_height()
    if h > 0:
        ax.text(bar.get_x() + bar.get_width()/2, h + 0.05, str(int(h)),
                ha="center", va="bottom", fontsize=10, fontweight="bold", color="#2196F3")
for bar in bars2:
    h = bar.get_height()
    if h > 0:
        ax.text(bar.get_x() + bar.get_width()/2, h + 0.05, str(int(h)),
                ha="center", va="bottom", fontsize=10, fontweight="bold", color="#FF5722")

ax.set_xticks(x)
ax.set_xticklabels(themes, fontsize=10)
ax.set_ylabel("Number of Respondents", fontsize=11)
ax.set_title("LLM-Identified Themes: Respondent Coverage by Cohort",
             fontsize=13, fontweight="bold")
ax.legend(fontsize=10)
ax.set_ylim(0, max(max(transit_counts), max(car_counts)) + 1.2)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
plt.tight_layout()
plt.savefig(f"{IMG_DIR}/fig5_themes_by_cohort.png", dpi=150)
plt.close()
print("Saved fig5_themes_by_cohort.png")

# ── Figure 6: Radar / spider chart of UX concern dimensions ───────────────
categories = [
    "Real-time\nInfo",
    "Safety",
    "Multimodal\nIntegration",
    "Cost\nTransparency",
    "UI Clarity",
    "Accessibility",
]
# Normalized scores 0-5 based on keyword heatmap + LLM themes
transit_scores = [4.5, 3.5, 3.0, 2.0, 2.5, 4.0]
car_scores     = [3.0, 2.5, 4.5, 3.5, 3.5, 1.0]

N = len(categories)
angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
# close the polygon
transit_scores_c = transit_scores + [transit_scores[0]]
car_scores_c     = car_scores     + [car_scores[0]]
angles_c         = angles         + [angles[0]]
categories_c     = categories     + [categories[0]]

fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
ax.plot(angles_c, transit_scores_c, "o-", linewidth=2, color="#2196F3", label="Transit-Primary")
ax.fill(angles_c, transit_scores_c, alpha=0.20, color="#2196F3")
ax.plot(angles_c, car_scores_c, "s-", linewidth=2, color="#FF5722", label="Car-Primary")
ax.fill(angles_c, car_scores_c, alpha=0.20, color="#FF5722")
ax.set_thetagrids(np.degrees(angles), categories, fontsize=10)
ax.set_ylim(0, 5)
ax.set_yticks([1, 2, 3, 4, 5])
ax.set_yticklabels(["1", "2", "3", "4", "5"], fontsize=8)
ax.set_title("UX Priority Profile by Cohort\n(composite score 0–5)",
             fontsize=12, fontweight="bold", pad=20)
ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=10)
plt.tight_layout()
plt.savefig(f"{IMG_DIR}/fig6_radar_ux_priorities.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved fig6_radar_ux_priorities.png")

print("\nAll theme figures saved.")
