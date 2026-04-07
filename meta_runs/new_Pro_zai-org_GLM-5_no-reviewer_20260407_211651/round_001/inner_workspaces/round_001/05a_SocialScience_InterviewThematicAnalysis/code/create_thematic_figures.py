import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import json

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load descriptive stats
with open('outputs/descriptive_stats.json', 'r') as f:
    stats = json.load(f)

# ============================================
# Figure 4: Code Frequency Chart
# ============================================
# Based on the thematic analysis results
codes = {
    'Reliability & Accuracy': 7,
    'Information Clarity & Transparency': 6,
    'Integrated Journey Planning': 5,
    'Safety & Personal Security': 4,
    'Contextual & Proactive Alerts': 4,
    'Interface Simplicity': 3,
    'Cost Comparison & Transparency': 3,
    'Accessibility & Inclusivity': 2,
    'Offline & Connectivity Resilience': 1
}

fig, ax = plt.subplots(figsize=(12, 7))
code_names = list(codes.keys())
frequencies = list(codes.values())

colors = plt.cm.Blues(np.linspace(0.4, 0.9, len(codes)))[::-1]
bars = ax.barh(code_names[::-1], frequencies[::-1], color=colors[::-1], edgecolor='black', linewidth=0.8)

ax.set_xlabel('Frequency (Number of Respondents)', fontsize=12)
ax.set_title('Code Frequencies from Thematic Analysis\n(n=18 respondents)', fontsize=14, fontweight='bold')

# Add value labels
for bar, freq in zip(bars, frequencies[::-1]):
    ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2, 
            str(freq), ha='left', va='center', fontsize=11, fontweight='bold')

ax.set_xlim(0, max(frequencies) + 1.5)
plt.tight_layout()
plt.savefig('report/images/code_frequencies.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: code_frequencies.png")

# ============================================
# Figure 5: Theme Summary Visualization
# ============================================
themes = {
    'Trust Through\nTransparency & Accuracy': {'transit': 5, 'car': 4},
    'Holistic Door-to-Door\nJourney Planning': {'transit': 4, 'car': 4},
    'Safety & Accessibility\nas Core Features': {'transit': 4, 'car': 2},
    'Contextual, User-Controlled\nNotifications': {'transit': 2, 'car': 4},
    'Cost Transparency\nfor Decision-Making': {'transit': 2, 'car': 3}
}

fig, ax = plt.subplots(figsize=(12, 7))

theme_names = list(themes.keys())
transit_counts = [themes[t]['transit'] for t in theme_names]
car_counts = [themes[t]['car'] for t in theme_names]

x = np.arange(len(theme_names))
width = 0.35

bars1 = ax.bar(x - width/2, transit_counts, width, label='Transit Primary', color='#3498db', edgecolor='black')
bars2 = ax.bar(x + width/2, car_counts, width, label='Car Primary', color='#e74c3c', edgecolor='black')

ax.set_ylabel('Number of Respondents', fontsize=12)
ax.set_title('Theme Prevalence by Cohort', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(theme_names, fontsize=10)
ax.legend(loc='upper right', fontsize=11)
ax.set_ylim(0, 6)

# Add value labels
for bar in bars1:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
            f'{int(height)}', ha='center', va='bottom', fontsize=10, fontweight='bold')
for bar in bars2:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
            f'{int(height)}', ha='center', va='bottom', fontsize=10, fontweight='bold')

plt.tight_layout()
plt.savefig('report/images/theme_prevalence_by_cohort.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: theme_prevalence_by_cohort.png")

# ============================================
# Figure 6: Cohort Comparison Heatmap
# ============================================
# Create a comparison matrix
comparison_data = [
    ['Reliability & Accuracy', 'High', 'High', 'Shared'],
    ['Information Clarity', 'High', 'High', 'Shared'],
    ['Integrated Journey Planning', 'High', 'High', 'Shared'],
    ['Safety & Security', 'High (Platform)', 'High (Parking)', 'Shared (Different Context)'],
    ['Cost Transparency', 'Medium', 'High', 'Shared'],
    ['Offline Functionality', 'High', 'Low', 'Transit-Unique'],
    ['Station Name Reconciliation', 'High', 'Low', 'Transit-Unique'],
    ['Carpool Matching', 'Low', 'Medium', 'Car-Unique'],
    ['Park-and-Ride Integration', 'Low', 'High', 'Car-Unique'],
    ['Family Cost Analysis', 'Low', 'High', 'Car-Unique']
]

fig, ax = plt.subplots(figsize=(14, 8))
ax.axis('off')

# Create table
table = ax.table(
    cellText=comparison_data,
    colLabels=['Pain Point', 'Transit Primary', 'Car Primary', 'Classification'],
    loc='center',
    cellLoc='center',
    colColours=['#2c3e50']*4
)

table.auto_set_font_size(False)
table.set_fontsize(11)
table.scale(1.2, 1.8)

# Style header
for i in range(4):
    table[(0, i)].set_text_props(color='white', fontweight='bold')

# Color code the classification column
color_map = {
    'Shared': '#27ae60',
    'Shared (Different Context)': '#f39c12',
    'Transit-Unique': '#3498db',
    'Car-Unique': '#e74c3c'
}

for i, row in enumerate(comparison_data, start=1):
    classification = row[3]
    if classification in color_map:
        table[(i, 3)].set_facecolor(color_map[classification])
        table[(i, 3)].set_text_props(color='white', fontweight='bold')

ax.set_title('Cohort Comparison: Pain Point Prevalence and Classification', 
             fontsize=14, fontweight='bold', pad=20)

plt.tight_layout()
plt.savefig('report/images/cohort_comparison_table.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: cohort_comparison_table.png")

print("\nAll thematic analysis figures generated successfully!")
