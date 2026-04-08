"""
Preprocessing and quantitative descriptives for interview thematic analysis.
Mixed-methods approach: transparent quantitative counts ground LLM-assisted qualitative synthesis.
"""

import pandas as pd
import numpy as np
import json
import re
from collections import Counter
import matplotlib.pyplot as plt
import seaborn as sns

# Set style for publication-quality figures
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load data (run from workspace root)
df = pd.read_csv('data/interview_excerpts.csv')

print("=" * 60)
print("INTERVIEW DATA OVERVIEW")
print("=" * 60)

# Basic cohort counts
print("\n1. COHORT DISTRIBUTION")
cohort_counts = df['cohort'].value_counts()
print(cohort_counts)
print(f"\nTotal respondents: {len(df)}")

# Response length analysis
df['response_length_chars'] = df['response_text'].str.len()
df['response_length_words'] = df['response_text'].str.split().str.len()
df['sentence_count'] = df['response_text'].str.count(r'[.!?]+')

print("\n2. RESPONSE LENGTH STATISTICS")
length_stats = df.groupby('cohort')[['response_length_chars', 'response_length_words', 'sentence_count']].describe()
print(length_stats)

# Word frequency analysis (excluding common stop words)
stop_words = {'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours', 
              'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers',
              'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves',
              'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are',
              'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does',
              'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until',
              'while', 'of', 'at', 'by', 'for', 'with', 'through', 'during', 'before', 'after',
              'above', 'below', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again',
              'further', 'then', 'once', 'to', 'from'}

def extract_meaningful_words(text):
    """Extract meaningful words from text, excluding stop words."""
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    return [w for w in words if w not in stop_words and len(w) > 2]

# Extract all meaningful words by cohort
transit_text = ' '.join(df[df['cohort'] == 'transit_primary']['response_text'])
car_text = ' '.join(df[df['cohort'] == 'car_primary']['response_text'])

transit_words = extract_meaningful_words(transit_text)
car_words = extract_meaningful_words(car_text)

print("\n3. TOP WORDS BY COHORT")
print("\nTransit-primary cohort top words:")
transit_freq = Counter(transit_words).most_common(15)
for word, count in transit_freq:
    print(f"  {word}: {count}")

print("\nCar-primary cohort top words:")
car_freq = Counter(car_words).most_common(15)
for word, count in car_freq:
    print(f"  {word}: {count}")

# Domain-specific keyword analysis
ux_keywords = ['app', 'interface', 'ux', 'button', 'screen', 'map', 'display', 'mode', 'offline', 'feature']
trust_keywords = ['trust', 'reliable', 'reliability', 'honest', 'wrong', 'accurate', 'assume']
safety_keywords = ['safe', 'safety', 'scary', 'unsafe', 'lighting', 'cctv', 'security']
convenience_keywords = ['easy', 'convenient', 'quick', 'fast', 'simple', 'seamless', 'smooth']
pain_keywords = ['pain', 'problem', 'issue', 'fail', 'wrong', 'miss', 'delay', 'crowded', 'gap']
information_keywords = ['info', 'information', 'know', 'explain', 'alert', 'notification', 'update']

def count_keywords(text, keywords):
    text_lower = text.lower()
    return sum(text_lower.count(kw) for kw in keywords)

# Calculate keyword frequencies
df['ux_mentions'] = df['response_text'].apply(lambda x: count_keywords(x, ux_keywords))
df['trust_mentions'] = df['response_text'].apply(lambda x: count_keywords(x, trust_keywords))
df['safety_mentions'] = df['response_text'].apply(lambda x: count_keywords(x, safety_keywords))
df['convenience_mentions'] = df['response_text'].apply(lambda x: count_keywords(x, convenience_keywords))
df['pain_mentions'] = df['response_text'].apply(lambda x: count_keywords(x, pain_keywords))
df['information_mentions'] = df['response_text'].apply(lambda x: count_keywords(x, information_keywords))

print("\n4. THEMATIC KEYWORD FREQUENCIES BY COHORT")
theme_cols = ['ux_mentions', 'trust_mentions', 'safety_mentions', 
              'convenience_mentions', 'pain_mentions', 'information_mentions']
theme_summary = df.groupby('cohort')[theme_cols].sum()
print(theme_summary)

# Save processed data
df.to_csv('outputs/preprocessed_interviews.csv', index=False)

# Save quantitative summary
summary_stats = {
    'cohort_counts': cohort_counts.to_dict(),
    'length_stats': df.groupby('cohort')[['response_length_chars', 'response_length_words', 'sentence_count']].mean().to_dict(),
    'top_words_transit': dict(transit_freq),
    'top_words_car': dict(car_freq),
    'theme_frequencies': theme_summary.to_dict()
}

with open('outputs/quantitative_summary.json', 'w') as f:
    json.dump(summary_stats, f, indent=2)

print("\n5. SAVED OUTPUTS")
print("  - outputs/preprocessed_interviews.csv")
print("  - outputs/quantitative_summary.json")

# Create visualization 1: Response length distribution
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Word count distribution
df.boxplot(column='response_length_words', by='cohort', ax=axes[0])
axes[0].set_title('Response Length by Cohort')
axes[0].set_xlabel('Cohort')
axes[0].set_ylabel('Word Count')
axes[0].get_figure().suptitle('')

# Theme mentions by cohort
theme_summary.T.plot(kind='bar', ax=axes[1])
axes[1].set_title('Thematic Keyword Mentions by Cohort')
axes[1].set_xlabel('Theme Category')
axes[1].set_ylabel('Total Mentions')
axes[1].legend(title='Cohort')
axes[1].tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.savefig('report/images/figure1_descriptives.png', dpi=300, bbox_inches='tight')
plt.close()

print("  - report/images/figure1_descriptives.png")

# Create visualization 2: Theme heatmap
fig, ax = plt.subplots(figsize=(10, 6))
theme_summary_norm = theme_summary.div(theme_summary.sum(axis=1), axis=0) * 100
sns.heatmap(theme_summary_norm, annot=True, fmt='.1f', cmap='YlOrRd', 
            cbar_kws={'label': 'Percentage of Mentions'}, ax=ax)
ax.set_title('Thematic Focus by Cohort (% Distribution)')
ax.set_xlabel('Theme Category')
ax.set_ylabel('Cohort')
plt.tight_layout()
plt.savefig('report/images/figure2_theme_heatmap.png', dpi=300, bbox_inches='tight')
plt.close()

print("  - report/images/figure2_theme_heatmap.png")

print("\n" + "=" * 60)
print("PREPROCESSING COMPLETE")
print("=" * 60)
