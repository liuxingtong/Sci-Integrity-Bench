"""
Generate additional publication-quality figures for the thematic analysis report.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import json

# Set publication style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_context("paper", font_scale=1.2)

# Load data
df = pd.read_csv('outputs/preprocessed_interviews.csv')
with open('outputs/quantitative_summary.json', 'r') as f:
    quant_summary = json.load(f)

# Figure 3: Word cloud-style bar chart of top words by cohort
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Transit cohort words
transit_words = list(quant_summary['top_words_transit'].keys())[:10]
transit_counts = list(quant_summary['top_words_transit'].values())[:10]
axes[0].barh(transit_words[::-1], transit_counts[::-1], color='#2E86AB')
axes[0].set_title('Transit-Primary: Top Words', fontweight='bold')
axes[0].set_xlabel('Frequency')

# Car cohort words
car_words = list(quant_summary['top_words_car'].keys())[:10]
car_counts = list(quant_summary['top_words_car'].values())[:10]
axes[1].barh(car_words[::-1], car_counts[::-1], color='#A23B72')
axes[1].set_title('Car-Primary: Top Words', fontweight='bold')
axes[1].set_xlabel('Frequency')

plt.tight_layout()
plt.savefig('report/images/figure3_word_frequency.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: report/images/figure3_word_frequency.png")

# Figure 4: Response characteristics comparison
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# Word count distribution
df.boxplot(column='response_length_words', by='cohort', ax=axes[0,0])
axes[0,0].set_title('Word Count Distribution')
axes[0,0].set_xlabel('Cohort')
axes[0,0].set_ylabel('Words')
axes[0,0].get_figure().suptitle('')

# Character count
df.boxplot(column='response_length_chars', by='cohort', ax=axes[0,1])
axes[0,1].set_title('Character Count Distribution')
axes[0,1].set_xlabel('Cohort')
axes[0,1].set_ylabel('Characters')
axes[0,1].get_figure().suptitle('')

# Theme mentions stacked bar
theme_cols = ['ux_mentions', 'trust_mentions', 'safety_mentions', 
              'convenience_mentions', 'pain_mentions', 'information_mentions']
theme_labels = ['UX', 'Trust', 'Safety', 'Convenience', 'Pain Points', 'Information']
theme_data = df.groupby('cohort')[theme_cols].sum()

theme_data.plot(kind='bar', stacked=True, ax=axes[1,0], 
                color=sns.color_palette("Set2", len(theme_cols)))
axes[1,0].set_title('Thematic Mentions by Cohort')
axes[1,0].set_xlabel('Cohort')
axes[1,0].set_ylabel('Total Mentions')
axes[1,0].legend(theme_labels, bbox_to_anchor=(1.05, 1), loc='upper left')
axes[1,0].tick_params(axis='x', rotation=0)

# Normalized theme distribution
theme_data_norm = theme_data.div(theme_data.sum(axis=1), axis=0) * 100
theme_data_norm.plot(kind='bar', ax=axes[1,1], 
                     color=sns.color_palette("Set2", len(theme_cols)))
axes[1,1].set_title('Theme Distribution (% by Cohort)')
axes[1,1].set_xlabel('Cohort')
axes[1,1].set_ylabel('Percentage')
axes[1,1].legend(theme_labels, bbox_to_anchor=(1.05, 1), loc='upper left')
axes[1,1].tick_params(axis='x', rotation=0)

plt.tight_layout()
plt.savefig('report/images/figure4_response_characteristics.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: report/images/figure4_response_characteristics.png")

# Figure 5: Cohort comparison radar-style visualization
fig, ax = plt.subplots(figsize=(10, 8))

categories = ['UX Focus', 'Trust Concerns', 'Safety', 'Pain Points', 'Info Needs']
transit_values = [10, 4, 2, 5, 2]
car_values = [7, 2, 2, 3, 2]

x = np.arange(len(categories))
width = 0.35

bars1 = ax.bar(x - width/2, transit_values, width, label='Transit-Primary', color='#2E86AB')
bars2 = ax.bar(x + width/2, car_values, width, label='Car-Primary', color='#A23B72')

ax.set_ylabel('Mention Count')
ax.set_title('Thematic Focus Comparison by Cohort', fontweight='bold', fontsize=14)
ax.set_xticks(x)
ax.set_xticklabels(categories)
ax.legend()

# Add value labels on bars
for bar in bars1:
    height = bar.get_height()
    ax.annotate(f'{int(height)}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha='center', va='bottom', fontsize=10)

for bar in bars2:
    height = bar.get_height()
    ax.annotate(f'{int(height)}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha='center', va='bottom', fontsize=10)

plt.tight_layout()
plt.savefig('report/images/figure5_cohort_comparison.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: report/images/figure5_cohort_comparison.png")

print("\nAll figures generated successfully.")
