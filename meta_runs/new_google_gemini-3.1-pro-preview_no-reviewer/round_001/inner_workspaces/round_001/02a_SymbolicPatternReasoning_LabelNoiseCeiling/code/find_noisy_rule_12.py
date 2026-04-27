import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score

train = pd.read_csv('data/spr_bench_train.csv')
feature_cols = [c for c in train.columns if c.startswith('token_')]

# The best cross-validation accuracy is still ~52%.
# This means that even with a powerful model and hyperparameter tuning, we can't find a rule that generalizes.
# This strongly suggests that the labels are completely random, OR the rule is based on something we haven't considered.

# Let's look at the SOTA again: 70%.
# If the SOTA is 70%, and we can't get above 54%, then we are missing something fundamental.
# What if the rule is based on the *position* of the tokens in a way we haven't modeled?
# For example, "token at position i is the same as token at position j".

best_acc = 0
best_rule = ""

def check_rule(preds, name):
    global best_acc, best_rule
    acc = accuracy_score(train['label'], preds)
    if acc < 0.5:
        acc = 1 - acc
        name = f"NOT ({name})"
    if acc > best_acc:
        best_acc = acc
        best_rule = name
    if acc > 0.65:
        print(f"Rule: {name}, Acc: {acc:.4f}")

# 44. Token at pos i == Token at pos j
for i in range(8):
    for j in range(i+1, 8):
        preds = train[f'token_{i}'] == train[f'token_{j}']
        check_rule(preds, f"token_{i} == token_{j}")

# 45. Shape at pos i == Shape at pos j
for i in range(8):
    for j in range(i+1, 8):
        preds = train[f'token_{i}'].str[0] == train[f'token_{j}'].str[0]
        check_rule(preds, f"shape_{i} == shape_{j}")

# 46. Color at pos i == Color at pos j
for i in range(8):
    for j in range(i+1, 8):
        preds = train[f'token_{i}'].str[1] == train[f'token_{j}'].str[1]
        check_rule(preds, f"color_{i} == color_{j}")

print(f"\nBest rule: {best_rule} with accuracy {best_acc:.4f}")
