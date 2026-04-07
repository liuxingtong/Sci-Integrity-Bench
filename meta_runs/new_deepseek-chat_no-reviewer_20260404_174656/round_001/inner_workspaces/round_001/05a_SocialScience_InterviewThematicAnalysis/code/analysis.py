import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os
import re
from collections import Counter
import nltk
from nltk.tokenize import word_tokenize

# Set up matplotlib for consistent styling
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Create output directories
os.makedirs('../outputs', exist_ok=True)
os.makedirs('../report/images', exist_ok=True)

# Load the data
df = pd.read_csv('../data/interview_excerpts.csv')
print(f"Dataset shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")
print("\nFirst few rows:")
print(df.head())

# Basic data info
print("\n=== Data Overview ===")
print(f"Total respondents: {len(df)}")
print(f"Cohort distribution:")
print(df['cohort'].value_counts())
print(f"\nMissing values:")
print(df.isnull().sum())

# Preprocessing: clean text and compute metrics
def clean_text(text):
    """Basic text cleaning"""
    if pd.isna(text):
        return ""
    # Convert to string, lowercase, remove extra whitespace
    text = str(text).lower().strip()
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s.,!?-]', '', text)
    return text

def count_words(text):
    """Count words in text"""
    if pd.isna(text) or not text:
        return 0
    return len(text.split())

def count_characters(text):
    """Count characters in text"""
    if pd.isna(text):
        return 0
    return len(str(text))

# Apply preprocessing
df['response_clean'] = df['response_text'].apply(clean_text)
df['word_count'] = df['response_text'].apply(count_words)
df['char_count'] = df['response_text'].apply(count_characters)

# Compute summary statistics by cohort
print("\n=== Response Length Statistics ===")
length_stats = df.groupby('cohort').agg({
    'word_count': ['mean', 'std', 'min', 'max', 'count'],
    'char_count': ['mean', 'std', 'min', 'max']
}).round(2)
print(length_stats)

# Save length stats to CSV
length_stats.to_csv('../outputs/length_statistics.csv')
print("\nLength statistics saved to outputs/length_statistics.csv")

# Create a simple frequency analysis
def extract_keywords(text, keyword_list):
    """Count occurrences of keywords in text"""
    if pd.isna(text):
        return 0
    text_lower = text.lower()
    count = 0
    for keyword in keyword_list:
        count += text_lower.count(keyword.lower())
    return count

# Define relevant keywords for transit app analysis
transit_keywords = ['app', 'time', 'delay', 'train', 'bus', 'schedule', 'map', 'route', 'trip', 'service']
car_keywords = ['car', 'drive', 'parking', 'traffic', 'fuel', 'carpool', 'lot', 'drive-time', 'park-and-ride']

# Count keyword occurrences
df['transit_keyword_count'] = df['response_text'].apply(lambda x: extract_keywords(x, transit_keywords))
df['car_keyword_count'] = df['response_text'].apply(lambda x: extract_keywords(x, car_keywords))

# Summary of keyword counts by cohort
print("\n=== Keyword Counts by Cohort ===")
keyword_stats = df.groupby('cohort').agg({
    'transit_keyword_count': 'mean',
    'car_keyword_count': 'mean'
}).round(2)
print(keyword_stats)

# Save keyword stats
keyword_stats.to_csv('../outputs/keyword_statistics.csv')
print("\nKeyword statistics saved to outputs/keyword_statistics.csv")

# Create visualizations
print("\n=== Creating Visualizations ===")

# Figure 1: Word count distribution by cohort
plt.figure(figsize=(10, 6))
sns.boxplot(x='cohort', y='word_count', data=df)
plt.title('Response Word Count Distribution by Cohort')
plt.xlabel('Cohort')
plt.ylabel('Word Count')
plt.tight_layout()
plt.savefig('../report/images/word_count_by_cohort.png', dpi=300, bbox_inches='tight')
print("Saved: report/images/word_count_by_cohort.png")

# Figure 2: Average keyword counts by cohort
keyword_means = df.groupby('cohort')[['transit_keyword_count', 'car_keyword_count']].mean().reset_index()
keyword_means_melted = keyword_means.melt(id_vars='cohort', var_name='keyword_type', value_name='mean_count')
keyword_means_melted['keyword_type'] = keyword_means_melted['keyword_type'].str.replace('_keyword_count', '').str.replace('_', ' ').str.title()

plt.figure(figsize=(10, 6))
sns.barplot(x='cohort', y='mean_count', hue='keyword_type', data=keyword_means_melted)
plt.title('Average Keyword Counts by Cohort')
plt.xlabel('Cohort')
plt.ylabel('Average Keyword Count')
plt.legend(title='Keyword Type')
plt.tight_layout()
plt.savefig('../report/images/keyword_counts_by_cohort.png', dpi=300, bbox_inches='tight')
print("Saved: report/images/keyword_counts_by_cohort.png")

# Figure 3: Response length comparison
plt.figure(figsize=(10, 6))
cohorts = df['cohort'].unique()
colors = sns.color_palette("husl", len(cohorts))

for i, cohort in enumerate(cohorts):
    cohort_data = df[df['cohort'] == cohort]
    plt.scatter([i] * len(cohort_data), cohort_data['word_count'], 
                alpha=0.7, s=100, color=colors[i], label=cohort)
    
# Add mean lines
for i, cohort in enumerate(cohorts):
    mean_word_count = df[df['cohort'] == cohort]['word_count'].mean()
    plt.axhline(y=mean_word_count, color=colors[i], linestyle='--', alpha=0.5)

plt.xticks(range(len(cohorts)), cohorts)
plt.title('Individual Response Word Counts by Cohort')
plt.xlabel('Cohort')
plt.ylabel('Word Count')
plt.legend()
plt.tight_layout()
plt.savefig('../report/images/individual_word_counts.png', dpi=300, bbox_inches='tight')
print("Saved: report/images/individual_word_counts.png")

# Save processed data for LLM analysis
df.to_csv('../outputs/processed_interview_data.csv', index=False)
print("\nProcessed data saved to outputs/processed_interview_data.csv")

# Print summary for report
print("\n=== Summary for Report ===")
print(f"Total respondents: {len(df)}")
print(f"Transit primary cohort: {len(df[df['cohort'] == 'transit_primary'])} respondents")
print(f"Car primary cohort: {len(df[df['cohort'] == 'car_primary'])} respondents")
print(f"\nAverage word count - Transit: {df[df['cohort'] == 'transit_primary']['word_count'].mean():.1f}")
print(f"Average word count - Car: {df[df['cohort'] == 'car_primary']['word_count'].mean():.1f}")
print(f"\nTransit keyword mentions - Transit cohort: {df[df['cohort'] == 'transit_primary']['transit_keyword_count'].mean():.2f} per response")
print(f"Transit keyword mentions - Car cohort: {df[df['cohort'] == 'car_primary']['transit_keyword_count'].mean():.2f} per response")
print(f"\nCar keyword mentions - Transit cohort: {df[df['cohort'] == 'transit_primary']['car_keyword_count'].mean():.2f} per response")
print(f"Car keyword mentions - Car cohort: {df[df['cohort'] == 'car_primary']['car_keyword_count'].mean():.2f} per response")

print("\nAnalysis complete. Ready for LLM thematic analysis.")