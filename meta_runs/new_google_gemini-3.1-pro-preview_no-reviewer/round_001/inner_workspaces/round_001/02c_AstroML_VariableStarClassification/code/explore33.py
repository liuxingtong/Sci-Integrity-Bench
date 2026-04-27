import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

# The baseline is 0.78. This is a very high score.
# Let's look at the data again. Is there any leakage?
# The strings are 40 characters long.
# What if the strings are just hashes or IDs?
# No, the problem says "symbol_series features".

# Let's try to use a very simple feature: the count of each character.
chars = ['u', 'v', 'w', 'x', 'y', 'z', '.', '*']

def get_counts(s):
    return [s.count(c) for c in chars]

X_train = np.array([get_counts(s) for s in train['symbol_series']])
X_val = np.array([get_counts(s) for s in val['symbol_series']])

y_train = train['label']
y_val = val['label']

model = RandomForestClassifier(n_estimators=500, random_state=42)
model.fit(X_train, y_train)
val_pred = model.predict(X_val)
print('Counts RF Val Acc:', balanced_accuracy_score(y_val, val_pred))

# Let's try to use the count of each character in the first half and second half
def get_half_counts(s):
    half = len(s) // 2
    s1 = s[:half]
    s2 = s[half:]
    return [s1.count(c) for c in chars] + [s2.count(c) for c in chars]

X_train = np.array([get_half_counts(s) for s in train['symbol_series']])
X_val = np.array([get_half_counts(s) for s in val['symbol_series']])

model = RandomForestClassifier(n_estimators=500, random_state=42)
model.fit(X_train, y_train)
val_pred = model.predict(X_val)
print('Half Counts RF Val Acc:', balanced_accuracy_score(y_val, val_pred))

# Let's try to use the count of each character in 4 quarters
def get_quarter_counts(s):
    q = len(s) // 4
    s1 = s[:q]
    s2 = s[q:2*q]
    s3 = s[2*q:3*q]
    s4 = s[3*q:]
    return [s1.count(c) for c in chars] + [s2.count(c) for c in chars] + [s3.count(c) for c in chars] + [s4.count(c) for c in chars]

X_train = np.array([get_quarter_counts(s) for s in train['symbol_series']])
X_val = np.array([get_quarter_counts(s) for s in val['symbol_series']])

model = RandomForestClassifier(n_estimators=500, random_state=42)
model.fit(X_train, y_train)
val_pred = model.predict(X_val)
print('Quarter Counts RF Val Acc:', balanced_accuracy_score(y_val, val_pred))
