import pandas as pd
import numpy as np
from hmmlearn import hmm
from sklearn.metrics import roc_auc_score

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

chars = ['1', '2', 'A', 'B', 'C', 'D']
char_to_idx = {c: i for i, c in enumerate(chars)}

def encode_seq(seq):
    return np.array([char_to_idx[c] for c in seq]).reshape(-1, 1)

train_0 = train[train['default_flag'] == 0]
train_1 = train[train['default_flag'] == 1]

X_train_0 = np.concatenate([encode_seq(s) for s in train_0['sym_seq']])
lengths_0 = [len(s) for s in train_0['sym_seq']]

X_train_1 = np.concatenate([encode_seq(s) for s in train_1['sym_seq']])
lengths_1 = [len(s) for s in train_1['sym_seq']]

for n_components in [2, 4, 6]:
    print(f'\n--- n_components: {n_components} ---')
    model_0 = hmm.CategoricalHMM(n_components=n_components, random_state=42, n_iter=50)
    model_0.fit(X_train_0, lengths_0)
    
    model_1 = hmm.CategoricalHMM(n_components=n_components, random_state=42, n_iter=50)
    model_1.fit(X_train_1, lengths_1)
    
    y_val_pred = []
    for seq in val['sym_seq']:
        x = encode_seq(seq)
        score_0 = model_0.score(x)
        score_1 = model_1.score(x)
        y_val_pred.append(score_1 - score_0)
        
    auc = roc_auc_score(val['default_flag'], y_val_pred)
    print(f'HMM Val AUC: {auc:.4f}')
