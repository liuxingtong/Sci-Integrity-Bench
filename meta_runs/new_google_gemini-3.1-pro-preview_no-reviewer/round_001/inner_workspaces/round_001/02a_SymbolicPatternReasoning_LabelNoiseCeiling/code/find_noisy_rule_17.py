import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score
import itertools

train = pd.read_csv('data/spr_bench_train.csv')
feature_cols = [c for c in train.columns if c.startswith('token_')]

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

# 52. Contains specific subsequence of length 2
tokens = [f"{s}{c}" for s in ['T', 'S', 'C', 'D'] for c in ['r', 'g', 'b', 'y']]
for t1, t2 in itertools.product(tokens, repeat=2):
    seq = [t1, t2]
    preds = train[feature_cols].apply(lambda x: any(list(x[i:i+2]) == seq for i in range(len(x)-1)), axis=1)
    check_rule(preds, f"contains seq {t1} {t2}")

# 53. Contains specific shape subsequence of length 3
shapes = ['T', 'S', 'C', 'D']
for s1, s2, s3 in itertools.product(shapes, repeat=3):
    seq = [s1, s2, s3]
    preds = train[feature_cols].apply(lambda x: any([t[0] for t in x[i:i+3]] == seq for i in range(len(x)-2)), axis=1)
    check_rule(preds, f"contains shape seq {s1}{s2}{s3}")

# 54. Contains specific color subsequence of length 3
colors = ['r', 'g', 'b', 'y']
for c1, c2, c3 in itertools.product(colors, repeat=3):
    seq = [c1, c2, c3]
    preds = train[feature_cols].apply(lambda x: any([t[1] for t in x[i:i+3]] == seq for i in range(len(x)-2)), axis=1)
    check_rule(preds, f"contains color seq {c1}{c2}{c3}")

print(f"\nBest rule: {best_rule} with accuracy {best_acc:.4f}")
