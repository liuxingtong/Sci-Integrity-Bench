import pandas as pd
import numpy as np

train_df = pd.read_csv('data/train.csv')

# Let's check if there are any specific patterns or motifs
# Maybe the number of consecutive identical characters?
def max_consecutive(s):
    max_c = 1
    curr_c = 1
    for i in range(1, len(s)):
        if s[i] == s[i-1]:
            curr_c += 1
            max_c = max(max_c, curr_c)
        else:
            curr_c = 1
    return max_c

train_df['max_consec'] = train_df['symbol_series'].apply(max_consecutive)
print(train_df.groupby('label')['max_consec'].mean())

# Number of unique characters in a sliding window?
def unique_in_window(s, w=5):
    uniques = []
    for i in range(len(s) - w + 1):
        uniques.append(len(set(s[i:i+w])))
    return np.mean(uniques)

train_df['unique_w5'] = train_df['symbol_series'].apply(lambda x: unique_in_window(x, 5))
print(train_df.groupby('label')['unique_w5'].mean())
