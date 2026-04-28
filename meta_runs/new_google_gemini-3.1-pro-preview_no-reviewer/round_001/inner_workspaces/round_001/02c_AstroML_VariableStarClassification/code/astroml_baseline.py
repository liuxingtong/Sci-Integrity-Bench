import pandas as pd
import numpy as np
from sklearn.metrics import balanced_accuracy_score

# The protocol says: Baseline balanced accuracy ≈ 0.78.
# This is very high compared to what we are getting (~0.57).
# There must be a specific feature or pattern we are missing.
# Let's look at the data again.

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

# Let's print some examples of label 0 and label 1
print("Label 0:")
for s in train[train['label'] == 0]['symbol_series'].head(5):
    print(s)

print("\nLabel 1:")
for s in train[train['label'] == 1]['symbol_series'].head(5):
    print(s)

# Is it possible that the symbols represent a light curve and we need to fold it?
# Or maybe the symbols are just a string representation of a time series and we need to use a specific distance metric?
# Let's try to find the period.
