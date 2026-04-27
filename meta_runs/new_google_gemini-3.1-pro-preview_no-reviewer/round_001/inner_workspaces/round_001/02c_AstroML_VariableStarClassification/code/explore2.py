import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

train = pd.read_csv('data/train.csv')

chars = ['*', '.', 'u', 'v', 'w', 'x', 'y', 'z']

for c in chars:
    train[f'count_{c}'] = train['symbol_series'].apply(lambda x: x.count(c))

fig, axes = plt.subplots(2, 4, figsize=(15, 8))
axes = axes.flatten()

for i, c in enumerate(chars):
    sns.boxplot(data=train, x='label', y=f'count_{c}', ax=axes[i])
    axes[i].set_title(f'Count of {c}')

plt.tight_layout()
plt.savefig('outputs/char_counts.png')

# Let's also look at the position of characters
# Maybe variable stars have more variation?
train['unique_chars'] = train['symbol_series'].apply(lambda x: len(set(x)))
sns.boxplot(data=train, x='label', y='unique_chars')
plt.savefig('outputs/unique_chars.png')
