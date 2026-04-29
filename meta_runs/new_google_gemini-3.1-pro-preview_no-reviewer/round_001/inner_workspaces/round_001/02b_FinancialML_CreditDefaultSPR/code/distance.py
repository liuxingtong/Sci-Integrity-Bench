import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score
import Levenshtein

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

train_0 = train[train['default_flag'] == 0]['sym_seq'].tolist()
train_1 = train[train['default_flag'] == 1]['sym_seq'].tolist()

def get_min_distance(seq, ref_seqs):
    min_dist = float('inf')
    for ref in ref_seqs:
        dist = Levenshtein.distance(seq, ref)
        if dist < min_dist:
            min_dist = dist
    return min_dist

def get_avg_distance(seq, ref_seqs):
    dists = [Levenshtein.distance(seq, ref) for ref in ref_seqs]
    return np.mean(dists)

y_val_pred_min = []
y_val_pred_avg = []

for seq in val['sym_seq']:
    dist_0_min = get_min_distance(seq, train_0)
    dist_1_min = get_min_distance(seq, train_1)
    y_val_pred_min.append(dist_0_min - dist_1_min) # If closer to 1, dist_1 is smaller, so dist_0 - dist_1 is positive
    
    dist_0_avg = get_avg_distance(seq, train_0)
    dist_1_avg = get_avg_distance(seq, train_1)
    y_val_pred_avg.append(dist_0_avg - dist_1_avg)

auc_min = roc_auc_score(val['default_flag'], y_val_pred_min)
print(f'Min Distance Val AUC: {auc_min:.4f}')

auc_avg = roc_auc_score(val['default_flag'], y_val_pred_avg)
print(f'Avg Distance Val AUC: {auc_avg:.4f}')
