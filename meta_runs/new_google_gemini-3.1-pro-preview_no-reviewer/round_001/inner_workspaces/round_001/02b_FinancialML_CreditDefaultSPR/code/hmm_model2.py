import pandas as pd
import numpy as np
from hmmlearn import hmm
from sklearn.metrics import roc_auc_score

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

chars = ['A', 'B', 'C', 'D', '1', '2']
char_to_idx = {c: i for i, c in enumerate(chars)}

def seq_to_idx(seq):
    return np.array([[char_to_idx[c]] for c in seq])

train_0 = train[train['default_flag'] == 0]['sym_seq'].values
train_1 = train[train['default_flag'] == 1]['sym_seq'].values

X_0 = np.concatenate([seq_to_idx(seq) for seq in train_0])
lengths_0 = [len(seq) for seq in train_0]

X_1 = np.concatenate([seq_to_idx(seq) for seq in train_1])
lengths_1 = [len(seq) for seq in train_1]

for n_comp in [2, 3, 4, 5, 6, 8, 10]:
    # Train HMM for class 0
    model_0 = hmm.CategoricalHMM(n_components=n_comp, random_state=42, n_iter=100)
    model_0.fit(X_0, lengths_0)
    
    # Train HMM for class 1
    model_1 = hmm.CategoricalHMM(n_components=n_comp, random_state=42, n_iter=100)
    model_1.fit(X_1, lengths_1)
    
    def predict_proba(seqs):
        probs = []
        for seq in seqs:
            x = seq_to_idx(seq)
            score_0 = model_0.score(x)
            score_1 = model_1.score(x)
            # Softmax with temperature to avoid overflow/underflow
            # prob_1 = np.exp(score_1) / (np.exp(score_0) + np.exp(score_1))
            # Use log-sum-exp trick implicitly by just taking difference
            probs.append(score_1 - score_0)
        return np.array(probs)
    
    val_preds = predict_proba(val['sym_seq'].values)
    auc = roc_auc_score(val['default_flag'], val_preds)
    print(f'HMM (n={n_comp}) AUC: {auc:.4f}')
