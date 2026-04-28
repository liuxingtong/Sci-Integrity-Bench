import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score
import xgboost as xgb

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

# Let's look at the baseline again. 0.78 is very high.
# Is there a leak? Or a very simple rule?
# Let's check if the first or last character is predictive.

for i in range(40):
    train[f'char_{i}'] = train['symbol_series'].apply(lambda x: x[i])
    val[f'char_{i}'] = val['symbol_series'].apply(lambda x: x[i])

for i in range(40):
    acc = balanced_accuracy_score(train['label'], train[f'char_{i}'] == '*')
    if acc > 0.55 or acc < 0.45:
        print(f'Pos {i} == * -> Acc: {acc:.4f}')

# Let's check if the number of unique characters is predictive.
acc = balanced_accuracy_score(train['label'], train['symbol_series'].apply(lambda x: len(set(x))) > 7)
print(f'Unique chars > 7 -> Acc: {acc:.4f}')

# Let's check if the presence of a specific character is predictive.
for c in ['*', '.', 'u', 'v', 'w', 'x', 'y', 'z']:
    acc = balanced_accuracy_score(train['label'], train['symbol_series'].apply(lambda x: c in x))
    print(f'Presence of {c} -> Acc: {acc:.4f}')
