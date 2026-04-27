import pandas as pd
import numpy as np
from collections import Counter

for code in ['OQMEA', 'ILULR', 'RHHQD', 'FDLOT']:
    df = pd.read_csv('data/{}_train.csv'.format(code))
    token_cols = [c for c in df.columns if c.startswith('token_')]
    print('\n=== {} ==='.format(code))
    print('Columns:', token_cols)
    print('Sample rows:')
    print(df.head(5).to_string())
    print('Unique tokens per col:')
    for c in token_cols:
        print('  {}: {}'.format(c, sorted(df[c].unique())))
    # Check if any single token predicts label
    for c in token_cols:
        from sklearn.metrics import accuracy_score
        from sklearn.preprocessing import LabelEncoder
        le = LabelEncoder()
        x = le.fit_transform(df[c])
        # majority vote per token value
        best = 0
        for val in df[c].unique():
            mask = df[c] == val
            if mask.sum() > 0:
                pred = df.loc[mask, 'label'].mode()[0]
                acc = (df.loc[mask, 'label'] == pred).mean()
                best = max(best, acc)
        print('  {} max single-value acc: {:.3f}'.format(c, best))
    # Check pairwise token interactions
    print('Label balance: {:.3f}'.format(df['label'].mean()))
