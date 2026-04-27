import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score

train = pd.read_csv('data/spr_bench_train.csv')
feature_cols = [c for c in train.columns if c.startswith('token_')]

# The RNN also fails to find a rule with >55% accuracy.
# This is extremely suspicious.
# If the SOTA is 70%, there MUST be a rule that gives ~70% accuracy.
# Why can't any of our models or manual checks find it?
# Let's check the label distribution again.
print("Label distribution:")
print(train['label'].value_counts(normalize=True))

# The labels are roughly 50/50.
# If the rule is 70% accurate, it means 30% of the labels are flipped.
# Let's try to find a rule that is exactly 70% accurate on the positive class, and 70% accurate on the negative class.

# What if the rule is based on the *number* of tokens that satisfy a condition?
# For example, "number of red tokens > number of blue tokens".

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

# 47. Count of shape A > Count of shape B
import itertools
for s1, s2 in itertools.permutations(shapes, 2):
    preds = train[feature_cols].apply(lambda x: sum(1 for t in x if t[0] == s1) > sum(1 for t in x if t[0] == s2), axis=1)
    check_rule(preds, f"count shape {s1} > count shape {s2}")

# 48. Count of color A > Count of color B
for c1, c2 in itertools.permutations(colors, 2):
    preds = train[feature_cols].apply(lambda x: sum(1 for t in x if t[1] == c1) > sum(1 for t in x if t[1] == c2), axis=1)
    check_rule(preds, f"count color {c1} > count color {c2}")

# 49. Sum of counts of two shapes > Sum of counts of other two shapes
for s1, s2 in itertools.combinations(shapes, 2):
    other_shapes = [s for s in shapes if s not in (s1, s2)]
    preds = train[feature_cols].apply(lambda x: sum(1 for t in x if t[0] in (s1, s2)) > sum(1 for t in x if t[0] in other_shapes), axis=1)
    check_rule(preds, f"count {s1}+{s2} > count {other_shapes[0]}+{other_shapes[1]}")

# 50. Sum of counts of two colors > Sum of counts of other two colors
for c1, c2 in itertools.combinations(colors, 2):
    other_colors = [c for c in colors if c not in (c1, c2)]
    preds = train[feature_cols].apply(lambda x: sum(1 for t in x if t[1] in (c1, c2)) > sum(1 for t in x if t[1] in other_colors), axis=1)
    check_rule(preds, f"count {c1}+{c2} > count {other_colors[0]}+{other_colors[1]}")

print(f"\nBest rule: {best_rule} with accuracy {best_acc:.4f}")
