import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os

# 1. Load Data
df = pd.read_csv('data/incident_narratives.csv')

# 2. Preprocessing & Quantitative Summaries
# Calculate lengths
df['char_length'] = df['narrative_text'].apply(len)
df['word_length'] = df['narrative_text'].apply(lambda x: len(x.split()))

# Keyword frequencies
keywords = ['blocked', 'reset', 'disabled', 'sinkhole', 'closed', 'enabled', 'powershell', 'smb', 'logins', 'dns', 'ransomware', 'tls']
for kw in keywords:
    df[f'kw_{kw}'] = df['narrative_text'].str.lower().str.contains(kw).astype(int)

# Summaries
source_counts = df['source_system'].value_counts().to_dict()
length_summary = df.groupby('source_system')[['char_length', 'word_length']].mean().to_dict()
keyword_summary = df.groupby('source_system')[[f'kw_{kw}' for kw in keywords]].sum().to_dict()

summary_stats = {
    'source_counts': source_counts,
    'length_summary': length_summary,
    'keyword_summary': keyword_summary
}

with open('outputs/summary_stats.json', 'w') as f:
    json.dump(summary_stats, f, indent=4)

# 3. Visualization
plt.figure(figsize=(8, 5))
sns.countplot(data=df, x='source_system', palette='Set2')
plt.title('Incident Counts by Source System')
plt.xlabel('Source System')
plt.ylabel('Count')
plt.savefig('report/images/source_counts.png')
plt.close()

plt.figure(figsize=(8, 5))
sns.boxplot(data=df, x='source_system', y='word_length', palette='Set2')
plt.title('Narrative Word Length by Source System')
plt.xlabel('Source System')
plt.ylabel('Word Count')
plt.savefig('report/images/word_length.png')
plt.close()

# Save processed data
df.to_csv('outputs/processed_narratives.csv', index=False)
print("Data analysis and visualization complete.")
