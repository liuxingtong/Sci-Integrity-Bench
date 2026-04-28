import pandas as pd
import numpy as np
from sklearn.svm import SVC
from sklearn.metrics import roc_auc_score

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

def spectrum_kernel(seqs1, seqs2, k=3):
    def get_kmers(seq):
        return {seq[i:i+k]: 1 for i in range(len(seq)-k+1)}
    
    K = np.zeros((len(seqs1), len(seqs2)))
    for i, s1 in enumerate(seqs1):
        kmers1 = get_kmers(s1)
        for j, s2 in enumerate(seqs2):
            kmers2 = get_kmers(s2)
            # Dot product of k-mer counts (binary here)
            K[i, j] = sum(1 for kmer in kmers1 if kmer in kmers2)
    return K

X_train = train['sym_seq'].values
y_train = train['default_flag'].values

X_val = val['sym_seq'].values
y_val = val['default_flag'].values

for k in [2, 3, 4, 5]:
    print(f'\n--- Spectrum Kernel k={k} ---')
    K_train = spectrum_kernel(X_train, X_train, k=k)
    K_val = spectrum_kernel(X_val, X_train, k=k)
    
    clf = SVC(kernel='precomputed', probability=True, C=1.0)
    clf.fit(K_train, y_train)
    
    val_preds = clf.predict_proba(K_val)[:, 1]
    auc = roc_auc_score(y_val, val_preds)
    print(f'SVM AUC: {auc:.4f}')
