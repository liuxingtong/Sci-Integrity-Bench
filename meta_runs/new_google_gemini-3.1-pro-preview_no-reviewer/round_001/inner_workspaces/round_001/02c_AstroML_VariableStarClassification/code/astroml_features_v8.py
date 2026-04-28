import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score
import xgboost as xgb

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

# Let's look at the data again. Is there a specific pattern in the strings?
# Maybe it's a palindrome? Or has a repeating pattern?

def is_palindrome(s):
    return s == s[::-1]

print(f"Palindromes in train: {sum(train['symbol_series'].apply(is_palindrome))}")

# Let's try to find the longest repeating non-overlapping substring.
import re
def longest_repeating_substring(s):
    n = len(s)
    LCSRe = [[0 for x in range(n + 1)] for y in range(n + 1)]
    res = ""
    res_length = 0
    index = 0
    for i in range(1, n + 1):
        for j in range(i + 1, n + 1):
            if (s[i - 1] == s[j - 1] and LCSRe[i - 1][j - 1] < (j - i)):
                LCSRe[i][j] = LCSRe[i - 1][j - 1] + 1
                if (LCSRe[i][j] > res_length):
                    res_length = LCSRe[i][j]
                    index = max(i, index)
            else:
                LCSRe[i][j] = 0
    if (res_length > 0):
        for i in range(index - res_length + 1, index + 1):
            res = res + s[i - 1]
    return res_length

train['lrs'] = train['symbol_series'].apply(longest_repeating_substring)
val['lrs'] = val['symbol_series'].apply(longest_repeating_substring)

print(f"LRS mean for label 0: {train[train['label'] == 0]['lrs'].mean()}")
print(f"LRS mean for label 1: {train[train['label'] == 1]['lrs'].mean()}")

clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(train[['lrs']], train['label'])
y_pred = clf.predict(val[['lrs']])
print(f'LRS RF Val Balanced Acc: {balanced_accuracy_score(val["label"], y_pred):.4f}')
