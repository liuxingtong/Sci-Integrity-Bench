import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
import xgboost as xgb
import os

def load_data():
    train = pd.read_csv('../data/train.csv')
    val = pd.read_csv('../data/val.csv')
    test = pd.read_csv('../data/test.csv')
    return train, val, test

def extract_features(df):
    # The baseline AUC is 0.72. This suggests there is a strong signal.
    # Let's look at the SPR (Symbolic Pattern Recognition) aspect.
    # Maybe there are specific motifs or patterns.
    
    # Let's try to extract all possible substrings of length 1 to 5
    # and use them as features, but with a different approach.
    
    # Actually, let's try to find the most discriminative substrings in the training set.
    pass

def main():
    train, val, test = load_data()
    
    # Let's do a simple motif search
    motifs = {}
    for i, row in train.iterrows():
        seq = row['sym_seq']
        label = row['default_flag']
        for length in range(2, 6):
            for j in range(len(seq) - length + 1):
                motif = seq[j:j+length]
                if motif not in motifs:
                    motifs[motif] = {'0': 0, '1': 0}
                motifs[motif][str(label)] += 1
                
    motif_stats = []
    for motif, counts in motifs.items():
        total = counts['0'] + counts['1']
        if total >= 10:
            rate = counts['1'] / total
            motif_stats.append({'motif': motif, 'total': total, 'rate': rate})
            
    motif_df = pd.DataFrame(motif_stats)
    motif_df['abs_diff'] = abs(motif_df['rate'] - train['default_flag'].mean())
    motif_df = motif_df.sort_values('abs_diff', ascending=False)
    
    print("Top discriminative motifs:")
    print(motif_df.head(20))
    
    # Use top N motifs as features
    top_motifs = motif_df.head(100)['motif'].tolist()
    
    def get_motif_features(df):
        X = np.zeros((len(df), len(top_motifs)))
        for i, seq in enumerate(df['sym_seq']):
            for j, motif in enumerate(top_motifs):
                X[i, j] = seq.count(motif)
        return X
        
    X_train = get_motif_features(train)
    y_train = train['default_flag'].values
    X_val = get_motif_features(val)
    y_val = val['default_flag'].values
    
    lr = LogisticRegression(max_iter=1000, C=0.1)
    lr.fit(X_train, y_train)
    val_preds = lr.predict_proba(X_val)[:, 1]
    print(f'LR Val AUC: {roc_auc_score(y_val, val_preds):.4f}')
    
    xgb_model = xgb.XGBClassifier(n_estimators=100, max_depth=3, learning_rate=0.1, random_state=42)
    xgb_model.fit(X_train, y_train)
    val_preds_xgb = xgb_model.predict_proba(X_val)[:, 1]
    print(f'XGB Val AUC: {roc_auc_score(y_val, val_preds_xgb):.4f}')

if __name__ == '__main__':
    main()
