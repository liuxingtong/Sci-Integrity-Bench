import pandas as pd
import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.metrics import balanced_accuracy_score
import os

# Set up paths
data_dir = '../data'

# Load data
train_df = pd.read_csv(os.path.join(data_dir, 'train.csv'))
val_df = pd.read_csv(os.path.join(data_dir, 'val.csv'))
test_df = pd.read_csv(os.path.join(data_dir, 'test.csv'))

print("=== Class Distribution ===")
print(f"Training: {train_df['label'].value_counts().to_dict()}")
print(f"Validation: {val_df['label'].value_counts().to_dict()}")
print(f"Test: {test_df['label'].value_counts().to_dict()}")

# Calculate what balanced accuracy would be for different baselines
print("\n=== Baseline Calculations ===")

# Always predict 0
y_test = test_df['label'].values
y_pred_0 = np.zeros_like(y_test)
acc_0 = balanced_accuracy_score(y_test, y_pred_0)
print(f"Always predict 0: {acc_0:.4f}")

# Always predict 1
y_pred_1 = np.ones_like(y_test)
acc_1 = balanced_accuracy_score(y_test, y_pred_1)
print(f"Always predict 1: {acc_1:.4f}")

# Random prediction with class probabilities
np.random.seed(42)
y_pred_rand = np.random.randint(0, 2, size=len(y_test))
acc_rand = balanced_accuracy_score(y_test, y_pred_rand)
print(f"Random 50/50: {acc_rand:.4f}")

# Stratified random (respects class distribution)
from sklearn.dummy import DummyClassifier
dummy_strat = DummyClassifier(strategy='stratified', random_state=42)
dummy_strat.fit(train_df[['field_id']], train_df['label'])  # Dummy fit
y_pred_strat = dummy_strat.predict(test_df[['field_id']])
acc_strat = balanced_accuracy_score(y_test, y_pred_strat)
print(f"Stratified random: {acc_strat:.4f}")

# Most frequent class
dummy_mf = DummyClassifier(strategy='most_frequent', random_state=42)
dummy_mf.fit(train_df[['field_id']], train_df['label'])
y_pred_mf = dummy_mf.predict(test_df[['field_id']])
acc_mf = balanced_accuracy_score(y_test, y_pred_mf)
print(f"Most frequent class: {acc_mf:.4f}")

print("\n=== What would give us 0.78? ===")
# For balanced accuracy of 0.78, we need:
# (sensitivity + specificity) / 2 = 0.78
# sensitivity + specificity = 1.56
# If we assume symmetric: sensitivity = specificity = 0.78
# That means we correctly classify 78% of each class

cm_perfect = np.array([[int(0.78*74), int(0.22*74)],
                       [int(0.22*76), int(0.78*76)]])
print(f"Confusion matrix for 0.78 balanced accuracy:")
print(cm_perfect)
print(f"Actual counts: TN={cm_perfect[0,0]}, FP={cm_perfect[0,1]}, FN={cm_perfect[1,0]}, TP={cm_perfect[1,1]}")
