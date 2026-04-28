import pandas as pd
import numpy as np

train = pd.read_csv('data/train.csv')

# Let's look at the actual strings for label 0 and label 1
print("Label 0:")
print(train[train['label'] == 0]['symbol_series'].head(10).values)

print("\nLabel 1:")
print(train[train['label'] == 1]['symbol_series'].head(10).values)

# Are there any specific patterns? 
# Maybe the number of unique characters?
print("\nUnique characters per string:")
train['unique_chars'] = train['symbol_series'].apply(lambda x: len(set(x)))
print(train.groupby('label')['unique_chars'].mean())

# Maybe the length of the longest run of identical characters?
def longest_run(s):
    max_run = 1
    current_run = 1
    for i in range(1, len(s)):
        if s[i] == s[i-1]:
            current_run += 1
            max_run = max(max_run, current_run)
        else:
            current_run = 1
    return max_run

train['longest_run'] = train['symbol_series'].apply(longest_run)
print("\nLongest run:")
print(train.groupby('label')['longest_run'].mean())

# Maybe the number of transitions between * and . ?
def star_dot_transitions(s):
    count = 0
    for i in range(1, len(s)):
        if (s[i] == '*' and s[i-1] == '.') or (s[i] == '.' and s[i-1] == '*'):
            count += 1
    return count

train['star_dot_trans'] = train['symbol_series'].apply(star_dot_transitions)
print("\nStar-dot transitions:")
print(train.groupby('label')['star_dot_trans'].mean())
