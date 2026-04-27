import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

os.makedirs('report/images', exist_ok=True)

df = pd.read_csv('outputs/merged_catalog.csv')

def categorize_period(note):
    note = str(note).lower()
    if any(x in note for x in ['bce', 'bc', 'warring states', 'han', 'zhou']):
        return 'BCE & Early CE (up to 500 CE)'
    elif any(x in note for x in ['tang', 'song', 'five dynasties', '12th c', '15th c', '1400s', 'medieval', '550 ce', '618-907', '10th c']):
        return 'Medieval (500 - 1500 CE)'
    elif any(x in note for x in ['ming', 'qing early', 'kangxi', 'edo', '17th c', '1600s', '18th c', '1752', 'qianlong', 'wanli']):
        return 'Early Modern (1500 - 1800 CE)'
    elif any(x in note for x in ['19th c', '1800s', '1880', '1890']):
        return '19th Century'
    elif any(x in note for x in ['20th c', '1920s', '1998', 'modern']):
        return '20th Century'
    else:
        return 'Unknown'

df['period'] = df['note'].apply(categorize_period)

print(df[['norm_acc', 'period', 'note']])

period_counts = df['period'].value_counts().reindex([
    'BCE & Early CE (up to 500 CE)',
    'Medieval (500 - 1500 CE)',
    'Early Modern (1500 - 1800 CE)',
    '19th Century',
    '20th Century',
    'Unknown'
])

plt.figure(figsize=(10, 6))
sns.barplot(x=period_counts.index, y=period_counts.values, hue=period_counts.index, palette='viridis', legend=False)
plt.title('Distribution of Museum Collection over Time')
plt.xlabel('Time Period')
plt.ylabel('Number of Objects')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig('report/images/time_distribution.png')
plt.close()

# Save the final catalog with periods
df.to_csv('outputs/final_catalog.csv', index=False)
