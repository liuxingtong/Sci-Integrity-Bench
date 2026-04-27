import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

# What if the symbols are NOT magnitudes?
# What if the string is a sequence of states, and we need to find specific motifs?
# Let's try to use a very simple approach: just count the occurrences of all possible substrings of length 1, 2, 3.

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

X_train, vocab = get_all_substring_counts(train['symbol_series'], 3)

# Get counts for val using the same vocab
def get_counts_for_vocab(series, vocab):
    features = []
    for s in series:
        counts = [s.count(sub) for sub in vocab]
        features.append(counts)
    return np.array(features)

X_val = get_counts_for_vocab(val['symbol_series'], vocab)

y_train = train['label']
y_val = val['label']

model = RandomForestClassifier(n_estimators=500, random_state=42)
model.fit(X_train, y_train)
val_pred = model.predict(X_val)
print('All Substrings (1-3) RF Val Acc:', balanced_accuracy_score(y_val, val_pred))

# Let's try length 4
X_train, vocab = get_all_substring_counts(train['symbol_series'], 4)
X_val = get_counts_for_vocab(val['symbol_series'], vocab)

model = RandomForestClassifier(n_estimators=500, random_state=42)
model.fit(X_train, y_train)
val_pred = model.predict(X_val)
print('All Substrings (1-4) RF Val Acc:', balanced_accuracy_score(y_val, val_pred))
