import pandas as pd
import numpy as np
from hmmlearn import hmm
from sklearn.metrics import roc_auc_score

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

chars = ['1', '2', 'A', 'B', 'C', 'D']
char_to_idx = {c: i for i, c in enumerate(chars)}

def seq_to_idx(seq):
    return np.array([[char_to_idx[c]] for c in seq])

train_0 = train[train['default_flag'] == 0]
train_1 = train[train['default_flag'] == 1]

X_train_0 = np.concatenate([seq_to_idx(seq) for seq in train_0['sym_seq']])
lengths_0 = [len(seq) for seq in train_0['sym_seq']]

X_train_1 = np.concatenate([seq_to_idx(seq) for seq in train_1['sym_seq']])
lengths_1 = [len(seq) for seq in train_1['sym_seq']]

for n_components in [2, 3, 4, 5, 6]:
    model_0 = hmm.CategoricalHMM(n_components=n_components, random_state=42, n_iter=100)
    model_0.fit(X_train_0, lengths_0)
    
    model_1 = hmm.CategoricalHMM(n_components=n_components, random_state=42, n_iter=100)
    model_1.fit(X_train_1, lengths_1)
    
    val_preds = []
    for seq in val['sym_seq']:
        x = seq_to_idx(seq)
        score_0 = model_0.score(x)
        score_1 = model_1.score(x)
        # Log likelihood ratio
        val_preds.append(score_1 - score_0)
        
    auc = roc_auc_score(val['default_flag'], val_preds)
    print(f'HMM n_components={n_components}, Val AUC: {auc:.4f}')
