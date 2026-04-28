import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score
import xgboost as xgb

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

# What if the characters represent a 2D shape or a matrix?
# 40 characters = 5x8 or 8x5 or 4x10 or 10x4.
# Let's try to reshape it and look for patterns.

def print_reshaped(s, rows, cols):
    for i in range(rows):
        print(s[i*cols:(i+1)*cols])
    print('-'*cols)

print("Label 0:")
for s in train[train['label'] == 0]['symbol_series'].head(3):
    print_reshaped(s, 5, 8)

print("Label 1:")
for s in train[train['label'] == 1]['symbol_series'].head(3):
    print_reshaped(s, 5, 8)

# Let's try 8x5
print("\nLabel 0 (8x5):")
for s in train[train['label'] == 0]['symbol_series'].head(3):
    print_reshaped(s, 8, 5)

print("Label 1 (8x5):")
for s in train[train['label'] == 1]['symbol_series'].head(3):
    print_reshaped(s, 8, 5)
