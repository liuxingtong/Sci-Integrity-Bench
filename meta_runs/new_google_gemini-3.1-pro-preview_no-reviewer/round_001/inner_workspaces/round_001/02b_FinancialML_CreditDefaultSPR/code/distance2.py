import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score
import Levenshtein
from sklearn.neighbors import KNeighborsClassifier

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

def compute_distance_matrix(seqs1, seqs2):
    n1 = len(seqs1)
    n2 = len(seqs2)
    dist_matrix = np.zeros((n1, n2))
    for i in range(n1):
        for j in range(n2):
            dist_matrix[i, j] = Levenshtein.distance(seqs1[i], seqs2[j])
    return dist_matrix

X_train = train['sym_seq'].tolist()
y_train = train['default_flag'].values

X_val = val['sym_seq'].tolist()
y_val = val['default_flag'].values

print('Computing train distance matrix...')
train_dist_matrix = compute_distance_matrix(X_train, X_train)

print('Computing val distance matrix...')
val_dist_matrix = compute_distance_matrix(X_val, X_train)

for k in [1, 3, 5, 7, 9, 11, 15, 21, 31, 51]:
    knn = KNeighborsClassifier(n_neighbors=k, metric='precomputed')
    knn.fit(train_dist_matrix, y_train)
    y_val_pred = knn.predict_proba(val_dist_matrix)[:, 1]
    auc = roc_auc_score(y_val, y_val_pred)
    print(f'KNN (k={k}) Val AUC: {auc:.4f}')
