import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score
import xgboost as xgb

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

# The baseline is 0.78. This is a very strong signal.
# Let's look at the data again. Is there a leak in the object_id or field_id?

print("Train field_id counts:")
print(train['field_id'].value_counts())

print("\nVal field_id counts:")
print(val['field_id'].value_counts())

# Let's check if field_id is predictive.
for field in train['field_id'].unique():
    subset = train[train['field_id'] == field]
    print(f"Field {field} label mean: {subset['label'].mean():.4f} (count: {len(subset)})")

# Let's check if object_id is predictive (e.g. odd/even).
train['obj_num'] = train['object_id'].apply(lambda x: int(x[3:]))
print(f"\nObj num odd label mean: {train[train['obj_num'] % 2 != 0]['label'].mean():.4f}")
print(f"Obj num even label mean: {train[train['obj_num'] % 2 == 0]['label'].mean():.4f}")
