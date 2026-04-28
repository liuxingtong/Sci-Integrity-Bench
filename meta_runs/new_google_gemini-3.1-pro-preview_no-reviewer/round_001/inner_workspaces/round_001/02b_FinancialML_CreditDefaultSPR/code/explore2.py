import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

for i in range(20):
    print(f'\n--- Position {i} ---')
    counts = train.groupby(train['sym_seq'].str[i])['default_flag'].mean()
    print(counts)
