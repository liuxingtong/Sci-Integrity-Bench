import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score
import Levenshtein

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

train_full = pd.concat([train, val])
train_0 = train_full[train_full['default_flag'] == 0]['sym_seq'].tolist()
train_1 = train_full[train_full['default_flag'] == 1]['sym_seq'].tolist()

def get_avg_distance(seq, ref_seqs):
    dists = [Levenshtein.distance(seq, ref) for ref in ref_seqs]
    return np.mean(dists)

y_test_pred_avg = []
for seq in test['sym_seq']:
    dist_0_avg = get_avg_distance(seq, train_0)
    dist_1_avg = get_avg_distance(seq, train_1)
    y_test_pred_avg.append(dist_0_avg - dist_1_avg)

test_auc = roc_auc_score(test['default_flag'], y_test_pred_avg)
print(f'Avg Distance Test AUC (Train+Val): {test_auc:.4f}')
