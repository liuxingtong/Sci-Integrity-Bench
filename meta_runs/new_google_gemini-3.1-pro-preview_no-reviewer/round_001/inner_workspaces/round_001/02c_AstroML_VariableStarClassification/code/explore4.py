import pandas as pd
import numpy as np

train = pd.read_csv('data/train.csv')

# Let's look at the actual strings for label 0 and 1
print("Label 0 (Non-variable):")
print(train[train['label'] == 0]['symbol_series'].head(10).values)

print("\nLabel 1 (Variable):")
print(train[train['label'] == 1]['symbol_series'].head(10).values)
