import pandas as pd
import numpy as np
from hmmlearn import hmm
from sklearn.metrics import roc_auc_score
import os

def load_data():
    train = pd.read_csv('../data/train.csv')
    val = pd.read_csv('../data/val.csv')
    test = pd.read_csv('../data/test.csv')
    return train, val, test

def seq_to_X_lengths(df):
    chars = ['A', 'B', 'C', 'D', '1', '2']
    char_to_idx = {c: i for i, c in enumerate(chars)}
    
    X = []
    lengths = []
    for seq in df['sym_seq']:
        X.extend([[char_to_idx[c]] for c in seq])
        lengths.append(len(seq))
    return np.array(X), lengths

def main():
    train, val, test = load_data()
    
    train_0 = train[train['default_flag'] == 0]
    train_1 = train[train['default_flag'] == 1]
    
    X_0, lengths_0 = seq_to_X_lengths(train_0)
    X_1, lengths_1 = seq_to_X_lengths(train_1)
    
    best_auc = 0
    best_n = 0
    
    for n_components in [2, 3, 4, 5, 6]:
        model_0 = hmm.CategoricalHMM(n_components=n_components, random_state=42, n_iter=100)
        model_0.fit(X_0, lengths_0)
        
        model_1 = hmm.CategoricalHMM(n_components=n_components, random_state=42, n_iter=100)
        model_1.fit(X_1, lengths_1)
        
        val_preds = []
        for seq in val['sym_seq']:
            chars = ['A', 'B', 'C', 'D', '1', '2']
            char_to_idx = {c: i for i, c in enumerate(chars)}
            x = np.array([[char_to_idx[c]] for c in seq])
            
            score_0 = model_0.score(x)
            score_1 = model_1.score(x)
            
            # Log likelihood ratio
            val_preds.append(score_1 - score_0)
            
        auc = roc_auc_score(val['default_flag'], val_preds)
        print(f'n_components={n_components}, Val AUC: {auc:.4f}')
        if auc > best_auc:
            best_auc = auc
            best_n = n_components
            
    print(f'Best HMM Val AUC: {best_auc:.4f} with n={best_n}')

if __name__ == '__main__':
    main()
