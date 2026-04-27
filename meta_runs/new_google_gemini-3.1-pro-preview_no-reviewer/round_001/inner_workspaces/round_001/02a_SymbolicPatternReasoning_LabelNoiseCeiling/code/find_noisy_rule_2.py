import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score
import itertools

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

# 5. Count of shape > threshold
for s in shapes:
    counts = train[feature_cols].apply(lambda x: sum(1 for t in x if t[0] == s), axis=1)
    for thresh in range(1, 5):
        check_rule(counts >= thresh, f"count shape {s} >= {thresh}")

# 6. Count of color > threshold
for c in colors:
    counts = train[feature_cols].apply(lambda x: sum(1 for t in x if t[1] == c), axis=1)
    for thresh in range(1, 5):
        check_rule(counts >= thresh, f"count color {c} >= {thresh}")

# 7. Adjacent identical shapes/colors
preds_adj_shape = train[feature_cols].apply(lambda x: any(x[i][0] == x[i+1][0] for i in range(len(x)-1)), axis=1)
check_rule(preds_adj_shape, "has adjacent same shape")

preds_adj_color = train[feature_cols].apply(lambda x: any(x[i][1] == x[i+1][1] for i in range(len(x)-1)), axis=1)
check_rule(preds_adj_color, "has adjacent same color")

# 8. Alternating shapes/colors
preds_alt_shape = train[feature_cols].apply(lambda x: all(x[i][0] != x[i+1][0] for i in range(len(x)-1)), axis=1)
check_rule(preds_alt_shape, "has alternating shapes")

preds_alt_color = train[feature_cols].apply(lambda x: all(x[i][1] != x[i+1][1] for i in range(len(x)-1)), axis=1)
check_rule(preds_alt_color, "has alternating colors")

# 9. Number of unique shapes/colors
unique_shapes = train[feature_cols].apply(lambda x: len(set(t[0] for t in x)), axis=1)
for i in range(1, 5):
    check_rule(unique_shapes == i, f"unique shapes == {i}")

unique_colors = train[feature_cols].apply(lambda x: len(set(t[1] for t in x)), axis=1)
for i in range(1, 5):
    check_rule(unique_colors == i, f"unique colors == {i}")

# 10. First token shape == Last token shape
preds_first_last_shape = train.apply(lambda x: x['token_0'][0] == x[f'token_{len(feature_cols)-1}'][0], axis=1)
check_rule(preds_first_last_shape, "first shape == last shape")

preds_first_last_color = train.apply(lambda x: x['token_0'][1] == x[f'token_{len(feature_cols)-1}'][1], axis=1)
check_rule(preds_first_last_color, "first color == last color")

print(f"\nBest rule: {best_rule} with accuracy {best_acc:.4f}")
