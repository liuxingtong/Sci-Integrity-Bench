import pandas as pd
import numpy as np

train = pd.read_csv('data/train.csv')

# Let's look at the length of the series again
print(train['symbol_series'].apply(len).value_counts())

# Let's look at the characters again
all_chars = set()
for s in train['symbol_series']:
    all_chars.update(list(s))
print(all_chars)

# Is there a pattern in the position of characters?
# Let's create a matrix of shape (n_samples, 40) where each element is the character
char_map = {'u': 1, 'v': 2, 'w': 3, 'x': 4, 'y': 5, 'z': 6, '.': 7, '*': 8}

def to_numeric(s):
    return [char_map[c] for c in s]

X_train = np.array([to_numeric(s) for s in train['symbol_series']])
y_train = train['label'].values

# Let's train a simple model on this matrix
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score

val = pd.read_csv('data/val.csv')
X_val = np.array([to_numeric(s) for s in val['symbol_series']])
y_val = val['label'].values

model = RandomForestClassifier(random_state=42)
model.fit(X_train, y_train)
val_pred = model.predict(X_val)
print('RF on raw positions Val Acc:', balanced_accuracy_score(y_val, val_pred))

# Let's try one-hot encoding the positions
from sklearn.preprocessing import OneHotEncoder
encoder = OneHotEncoder(handle_unknown='ignore')
X_train_ohe = encoder.fit_transform(X_train)
X_val_ohe = encoder.transform(X_val)

model = RandomForestClassifier(random_state=42)
model.fit(X_train_ohe, y_train)
val_pred = model.predict(X_val_ohe)
print('RF on OHE positions Val Acc:', balanced_accuracy_score(y_val, val_pred))

from sklearn.linear_model import LogisticRegression
model = LogisticRegression(random_state=42, max_iter=1000)
model.fit(X_train_ohe, y_train)
val_pred = model.predict(X_val_ohe)
print('LR on OHE positions Val Acc:', balanced_accuracy_score(y_val, val_pred))
