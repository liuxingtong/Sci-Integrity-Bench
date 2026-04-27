import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

# The baseline is 0.78. This is a very strong signal.
# Let's look at the data again.
# train.csv has columns: object_id, field_id, symbol_series, label
# We haven't used field_id!

print("Train field_id distribution:")
print(train['field_id'].value_counts())

print("\nVal field_id distribution:")
print(val['field_id'].value_counts())

# Let's see if field_id is correlated with label
print("\nLabel distribution by field_id in Train:")
print(train.groupby('field_id')['label'].mean())

# Let's include field_id as a feature
X_train_field = pd.get_dummies(train['field_id'])
X_val_field = pd.get_dummies(val['field_id'])

# Align columns
X_train_field, X_val_field = X_train_field.align(X_val_field, join='left', axis=1, fill_value=0)

# Combine with substring counts
def get_all_substring_counts(series, max_len):
    substrings = set()
    for s in series:
        for k in range(1, max_len + 1):
            for i in range(len(s) - k + 1):
                substrings.add(s[i:i+k])
    substrings = list(substrings)
    features = []
    for s in series:
        counts = [s.count(sub) for sub in substrings]
        features.append(counts)
    return np.array(features), substrings

def get_counts_for_vocab(series, vocab):
    features = []
    for s in series:
        counts = [s.count(sub) for sub in vocab]
        features.append(counts)
    return np.array(features)

X_train_subs, vocab = get_all_substring_counts(train['symbol_series'], 3)
X_val_subs = get_counts_for_vocab(val['symbol_series'], vocab)

X_train = np.concatenate([X_train_subs, X_train_field.values], axis=1)
X_val = np.concatenate([X_val_subs, X_val_field.values], axis=1)

y_train = train['label']
y_val = val['label']

model = RandomForestClassifier(n_estimators=500, random_state=42)
model.fit(X_train, y_train)
val_pred = model.predict(X_val)
print('\nSubstrings + Field ID RF Val Acc:', balanced_accuracy_score(y_val, val_pred))
