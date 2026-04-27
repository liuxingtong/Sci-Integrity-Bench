import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score

train = pd.read_csv('data/spr_bench_train.csv')
feature_cols = [c for c in train.columns if c.startswith('token_')]

# Let's rethink. The task is "LabelNoiseCeiling".
# This means the labels are noisy. The SOTA is 70%.
# If the labels are noisy, maybe the rule is very simple, but 30% of the labels are flipped.
# Let's try to find a rule that gives exactly 70% accuracy.

shapes = ['T', 'S', 'C', 'D']
colors = ['r', 'g', 'b', 'y']

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

# Let's check all possible 1-token rules
for i in range(8):
    for s in shapes:
        preds = train[f'token_{i}'].str[0] == s
        check_rule(preds, f"token_{i} shape is {s}")
    for c in colors:
        preds = train[f'token_{i}'].str[1] == c
        check_rule(preds, f"token_{i} color is {c}")
    for s in shapes:
        for c in colors:
            preds = train[f'token_{i}'] == f"{s}{c}"
            check_rule(preds, f"token_{i} is {s}{c}")

# Let's check all possible 2-token rules (AND)
for i in range(8):
    for j in range(i+1, 8):
        for s1 in shapes:
            for s2 in shapes:
                preds = (train[f'token_{i}'].str[0] == s1) & (train[f'token_{j}'].str[0] == s2)
                check_rule(preds, f"token_{i} shape is {s1} AND token_{j} shape is {s2}")

print(f"\nBest rule: {best_rule} with accuracy {best_acc:.4f}")
