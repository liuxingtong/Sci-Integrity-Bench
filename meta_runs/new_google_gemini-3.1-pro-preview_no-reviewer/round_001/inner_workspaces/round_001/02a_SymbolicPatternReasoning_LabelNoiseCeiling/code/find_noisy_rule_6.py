import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score

train = pd.read_csv('data/spr_bench_train.csv')
feature_cols = [c for c in train.columns if c.startswith('token_')]

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

# Let's think about the task name: "LabelNoiseCeiling"
# This implies that the labels are intentionally noisy, and the goal is to find the underlying rule despite the noise.
# The SOTA is 70%, which means the noise level is likely 30% (i.e., 30% of labels are flipped).
# If 30% of labels are flipped, the true rule should have ~70% accuracy on the noisy labels.
# We need to find a rule that gives exactly ~70% accuracy.

# Let's try some classic symbolic reasoning tasks.
# 20. Count of a specific shape/color is even/odd
for s in shapes:
    preds = train[feature_cols].apply(lambda x: sum(1 for t in x if t[0] == s) % 2 == 0, axis=1)
    check_rule(preds, f"count shape {s} is even")

for c in colors:
    preds = train[feature_cols].apply(lambda x: sum(1 for t in x if t[1] == c) % 2 == 0, axis=1)
    check_rule(preds, f"count color {c} is even")

# 21. Sum of counts of two shapes is even/odd
import itertools
for s1, s2 in itertools.combinations(shapes, 2):
    preds = train[feature_cols].apply(lambda x: (sum(1 for t in x if t[0] == s1) + sum(1 for t in x if t[0] == s2)) % 2 == 0, axis=1)
    check_rule(preds, f"count shape {s1} + {s2} is even")

# 22. Presence of a specific pair of tokens anywhere
for t1, t2 in itertools.combinations([f"{s}{c}" for s in shapes for c in colors], 2):
    preds = train[feature_cols].apply(lambda x: t1 in x.values and t2 in x.values, axis=1)
    check_rule(preds, f"contains {t1} and {t2}")

# 23. Presence of a specific pair of shapes anywhere
for s1, s2 in itertools.combinations(shapes, 2):
    preds = train[feature_cols].apply(lambda x: any(t[0] == s1 for t in x) and any(t[0] == s2 for t in x), axis=1)
    check_rule(preds, f"contains shape {s1} and {s2}")

# 24. First token shape == Last token shape
preds = train.apply(lambda x: x['token_0'][0] == x[f'token_{len(feature_cols)-1}'][0], axis=1)
check_rule(preds, "first shape == last shape")

# 25. First token color == Last token color
preds = train.apply(lambda x: x['token_0'][1] == x[f'token_{len(feature_cols)-1}'][1], axis=1)
check_rule(preds, "first color == last color")

# 26. Number of unique shapes == 4
preds = train[feature_cols].apply(lambda x: len(set(t[0] for t in x)) == 4, axis=1)
check_rule(preds, "has all 4 shapes")

# 27. Number of unique colors == 4
preds = train[feature_cols].apply(lambda x: len(set(t[1] for t in x)) == 4, axis=1)
check_rule(preds, "has all 4 colors")

print(f"\nBest rule: {best_rule} with accuracy {best_acc:.4f}")
