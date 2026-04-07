import pandas as pd
import json
import os
import re
from collections import Counter
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Set style for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Create output directories if they don't exist
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# ============================================
# STEP 1: Load and Preprocess Data
# ============================================
print("Loading interview data...")
df = pd.read_csv('data/interview_excerpts.csv')

print(f"Total respondents: {len(df)}")
print(f"Columns: {df.columns.tolist()}")

# ============================================
# STEP 2: Reproducible Preprocessing & Summaries
# ============================================
print("\n--- Cohort Counts ---")
cohort_counts = df['cohort'].value_counts().to_dict()
print(cohort_counts)

# Response length analysis (characters and words)
df['response_length_chars'] = df['response_text'].str.len()
df['response_length_words'] = df['response_text'].str.split().str.len()

print("\n--- Response Length Statistics ---")
length_stats = df.groupby('cohort').agg({
    'response_length_chars': ['mean', 'std', 'min', 'max'],
    'response_length_words': ['mean', 'std', 'min', 'max']
}).round(2)
print(length_stats)

# Word frequency analysis
def get_word_frequencies(texts, min_length=4):
    """Extract word frequencies from texts, excluding common stopwords."""
    stopwords = {'the', 'and', 'for', 'that', 'with', 'this', 'from', 'have', 
                 'are', 'was', 'were', 'been', 'being', 'has', 'had', 'does',
                 'will', 'would', 'could', 'should', 'may', 'might', 'must',
                 'when', 'where', 'what', 'which', 'who', 'whom', 'whose',
                 'about', 'into', 'than', 'then', 'them', 'they', 'their',
                 'some', 'such', 'only', 'more', 'also', 'just', 'even',
                 'like', 'very', 'much', 'well', 'back', 'after', 'before'}
    all_words = []
    for text in texts:
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        words = [w for w in words if len(w) >= min_length and w not in stopwords]
        all_words.extend(words)
    return Counter(all_words)

print("\n--- Word Frequencies by Cohort ---")
transit_texts = df[df['cohort'] == 'transit_primary']['response_text'].tolist()
car_texts = df[df['cohort'] == 'car_primary']['response_text'].tolist()

transit_freq = get_word_frequencies(transit_texts)
car_freq = get_word_frequencies(car_texts)

print("\nTop 15 words - Transit Primary:")
for word, count in transit_freq.most_common(15):
    print(f"  {word}: {count}")

print("\nTop 15 words - Car Primary:")
for word, count in car_freq.most_common(15):
    print(f"  {word}: {count}")

# ============================================
# STEP 3: Save Descriptive Statistics
# ============================================
descriptive_stats = {
    'total_respondents': len(df),
    'cohort_counts': cohort_counts,
    'length_stats_by_cohort': {
        'transit_primary': {
            'mean_chars': float(df[df['cohort'] == 'transit_primary']['response_length_chars'].mean()),
            'mean_words': float(df[df['cohort'] == 'transit_primary']['response_length_words'].mean()),
            'std_chars': float(df[df['cohort'] == 'transit_primary']['response_length_chars'].std()),
            'std_words': float(df[df['cohort'] == 'transit_primary']['response_length_words'].std())
        },
        'car_primary': {
            'mean_chars': float(df[df['cohort'] == 'car_primary']['response_length_chars'].mean()),
            'mean_words': float(df[df['cohort'] == 'car_primary']['response_length_words'].mean()),
            'std_chars': float(df[df['cohort'] == 'car_primary']['response_length_chars'].std()),
            'std_words': float(df[df['cohort'] == 'car_primary']['response_length_words'].std())
        }
    },
    'top_words_transit': dict(transit_freq.most_common(20)),
    'top_words_car': dict(car_freq.most_common(20))
}

with open('outputs/descriptive_stats.json', 'w') as f:
    json.dump(descriptive_stats, f, indent=2)

print("\nDescriptive statistics saved to outputs/descriptive_stats.json")

# ============================================
# STEP 4: Generate Visualizations
# ============================================
print("\nGenerating visualizations...")

# Figure 1: Cohort Distribution
fig, ax = plt.subplots(figsize=(8, 6))
cohorts = list(cohort_counts.keys())
counts = list(cohort_counts.values())
colors = ['#3498db', '#e74c3c']
bars = ax.bar(cohorts, counts, color=colors, edgecolor='black', linewidth=1.2)
ax.set_xlabel('Cohort', fontsize=12)
ax.set_ylabel('Number of Respondents', fontsize=12)
ax.set_title('Distribution of Respondents by Cohort', fontsize=14, fontweight='bold')
for bar, count in zip(bars, counts):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
            str(count), ha='center', va='bottom', fontsize=12, fontweight='bold')
ax.set_ylim(0, max(counts) + 1)
plt.tight_layout()
plt.savefig('report/images/cohort_distribution.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: cohort_distribution.png")

# Figure 2: Response Length Comparison
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Character length
transit_chars = df[df['cohort'] == 'transit_primary']['response_length_chars']
car_chars = df[df['cohort'] == 'car_primary']['response_length_chars']

bp1 = axes[0].boxplot([transit_chars, car_chars], labels=['Transit Primary', 'Car Primary'],
                       patch_artist=True)
bp1['boxes'][0].set_facecolor('#3498db')
bp1['boxes'][1].set_facecolor('#e74c3c')
axes[0].set_ylabel('Response Length (Characters)', fontsize=11)
axes[0].set_title('Character Count by Cohort', fontsize=12, fontweight='bold')

# Word count
transit_words = df[df['cohort'] == 'transit_primary']['response_length_words']
car_words = df[df['cohort'] == 'car_primary']['response_length_words']

bp2 = axes[1].boxplot([transit_words, car_words], labels=['Transit Primary', 'Car Primary'],
                       patch_artist=True)
bp2['boxes'][0].set_facecolor('#3498db')
bp2['boxes'][1].set_facecolor('#e74c3c')
axes[1].set_ylabel('Response Length (Words)', fontsize=11)
axes[1].set_title('Word Count by Cohort', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig('report/images/response_length_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: response_length_comparison.png")

# Figure 3: Top Word Frequencies Comparison
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Transit words
transit_top = dict(transit_freq.most_common(10))
axes[0].barh(list(transit_top.keys())[::-1], list(transit_top.values())[::-1], 
             color='#3498db', edgecolor='black')
axes[0].set_xlabel('Frequency', fontsize=11)
axes[0].set_title('Top 10 Words - Transit Primary', fontsize=12, fontweight='bold')

# Car words
car_top = dict(car_freq.most_common(10))
axes[1].barh(list(car_top.keys())[::-1], list(car_top.values())[::-1], 
             color='#e74c3c', edgecolor='black')
axes[1].set_xlabel('Frequency', fontsize=11)
axes[1].set_title('Top 10 Words - Car Primary', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig('report/images/word_frequency_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: word_frequency_comparison.png")

# ============================================
# STEP 5: Prepare Data for Anthropic API
# ============================================
print("\nPreparing interview data for thematic analysis...")

# Format interviews for API
interview_data = []
for _, row in df.iterrows():
    interview_data.append({
        'respondent_id': row['respondent_id'],
        'cohort': row['cohort'],
        'response_text': row['response_text']
    })

# Save formatted data
with open('outputs/interview_data_formatted.json', 'w') as f:
    json.dump(interview_data, f, indent=2)

print("Interview data formatted and saved.")

# Print summary for verification
print("\n" + "="*60)
print("SUMMARY OF PREPROCESSING")
print("="*60)
print(f"Total respondents: {len(df)}")
print(f"Transit Primary: {cohort_counts.get('transit_primary', 0)}")
print(f"Car Primary: {cohort_counts.get('car_primary', 0)}")
print(f"Average response length (chars): {df['response_length_chars'].mean():.1f}")
print(f"Average response length (words): {df['response_length_words'].mean():.1f}")
print("="*60)
