import pandas as pd
import numpy as np

train_df = pd.read_csv('data/train.csv')

# Let's look at the actual sequences for label 0 and 1
print("Label 0 examples:")
print(train_df[train_df['label'] == 0]['symbol_series'].head(10).tolist())

print("\nLabel 1 examples:")
print(train_df[train_df['label'] == 1]['symbol_series'].head(10).tolist())
