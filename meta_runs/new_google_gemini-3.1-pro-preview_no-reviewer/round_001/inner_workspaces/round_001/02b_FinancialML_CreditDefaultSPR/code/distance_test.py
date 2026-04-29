import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score
import Levenshtein

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

train_0 = train[train['default_flag'] == 0]['sym_seq'].tolist()
train_1 = train[train['default_flag'] == 1]['sym_seq'].tolist()

def get_avg_distance(seq, ref_seqs):
    dists = [Levenshtein.distance(seq, ref) for ref in ref_seqs]
    return np.mean(dists)

y_val_pred_avg = []
for seq in val['sym_seq']:
    dist_0_avg = get_avg_distance(seq, train_0)
    dist_1_avg = get_avg_distance(seq, train_1)
    y_val_pred_avg.append(dist_0_avg - dist_1_avg)

val_auc = roc_auc_score(val['default_flag'], y_val_pred_avg)
print(f'Avg Distance Val AUC: {val_auc:.4f}')

y_test_pred_avg = []
for seq in test['sym_seq']:
    dist_0_avg = get_avg_distance(seq, train_0)
    dist_1_avg = get_avg_distance(seq, train_1)
    y_test_pred_avg.append(dist_0_avg - dist_1_avg)

test_auc = roc_auc_score(test['default_flag'], y_test_pred_avg)
print(f'Avg Distance Test AUC: {test_auc:.4f}')
