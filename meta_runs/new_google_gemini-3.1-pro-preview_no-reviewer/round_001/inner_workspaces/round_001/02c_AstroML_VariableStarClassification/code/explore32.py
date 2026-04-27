import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

# Let's try to find the longest sequence of identical characters (ignoring . and *)
char_map = {'u': 1, 'v': 2, 'w': 3, 'x': 4, 'y': 5, 'z': 6}

def get_longest_identical(s):
    s_clean = [c for c in s if c in char_map]
    if len(s_clean) == 0:
        return 0
    
    max_len = 1
    current_len = 1
    for i in range(1, len(s_clean)):
        if s_clean[i] == s_clean[i-1]:
            current_len += 1
            max_len = max(max_len, current_len)
        else:
            current_len = 1
    return max_len

# Let's try to find the longest sequence of monotonically increasing/decreasing characters
def get_longest_monotonic(s):
    s_clean = [char_map[c] for c in s if c in char_map]
    if len(s_clean) == 0:
        return 0, 0
    
    max_inc = 1
    current_inc = 1
    max_dec = 1
    current_dec = 1
    
    for i in range(1, len(s_clean)):
        if s_clean[i] >= s_clean[i-1]:
            current_inc += 1
            max_inc = max(max_inc, current_inc)
        else:
            current_inc = 1
            
        if s_clean[i] <= s_clean[i-1]:
            current_dec += 1
            max_dec = max(max_dec, current_dec)
        else:
            current_dec = 1
            
    return max_inc, max_dec

X_train = np.array([[get_longest_identical(s)] + list(get_longest_monotonic(s)) for s in train['symbol_series']])
X_val = np.array([[get_longest_identical(s)] + list(get_longest_monotonic(s)) for s in val['symbol_series']])

y_train = train['label']
y_val = val['label']

model = RandomForestClassifier(n_estimators=500, random_state=42)
model.fit(X_train, y_train)
val_pred = model.predict(X_val)
print('Longest Sequences RF Val Acc:', balanced_accuracy_score(y_val, val_pred))
