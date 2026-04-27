import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

# The baseline is 0.78. We are still far.
# Let's look at the problem description again: "Classify variable vs non-variable sources using symbol_series features."
# It explicitly says "using symbol_series features". So field_id is probably not the main signal.

# What if the symbols are a sequence of observations, and the *order* matters a lot?
# Let's try to use a 1D CNN or an RNN. Since we can't easily use PyTorch/TensorFlow, let's try to extract features that capture the order.

# Let's try to find the position of the first occurrence of each character
chars = ['u', 'v', 'w', 'x', 'y', 'z', '.', '*']

def get_first_positions(s):
    positions = []
    for c in chars:
        idx = s.find(c)
        positions.append(idx if idx != -1 else 40)
    return positions

# Let's try to find the position of the last occurrence of each character
def get_last_positions(s):
    positions = []
    for c in chars:
        idx = s.rfind(c)
        positions.append(idx if idx != -1 else -1)
    return positions

# Let's try to find the mean position of each character
def get_mean_positions(s):
    positions = []
    for c in chars:
        indices = [i for i, char in enumerate(s) if char == c]
        positions.append(np.mean(indices) if len(indices) > 0 else 20)
    return positions

X_train = np.array([get_first_positions(s) + get_last_positions(s) + get_mean_positions(s) for s in train['symbol_series']])
X_val = np.array([get_first_positions(s) + get_last_positions(s) + get_mean_positions(s) for s in val['symbol_series']])

y_train = train['label']
y_val = val['label']

model = RandomForestClassifier(n_estimators=500, random_state=42)
model.fit(X_train, y_train)
val_pred = model.predict(X_val)
print('Positions RF Val Acc:', balanced_accuracy_score(y_val, val_pred))
