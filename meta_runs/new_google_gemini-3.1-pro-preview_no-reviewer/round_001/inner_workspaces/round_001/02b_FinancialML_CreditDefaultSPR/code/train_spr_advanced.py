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

def main():
    train, val, test = load_data()
    
    # Let's do a simple motif search
    motifs = {}
    for i, row in train.iterrows():
        seq = row['sym_seq']
        label = row['default_flag']
        for length in range(1, 7):
            for j in range(len(seq) - length + 1):
                motif = seq[j:j+length]
                if motif not in motifs:
                    motifs[motif] = {'0': 0, '1': 0}
                motifs[motif][str(label)] += 1
                
    motif_stats = []
    for motif, counts in motifs.items():
        total = counts['0'] + counts['1']
        if total >= 5:
            rate = counts['1'] / total
            motif_stats.append({'motif': motif, 'total': total, 'rate': rate})
            
    motif_df = pd.DataFrame(motif_stats)
    motif_df['abs_diff'] = abs(motif_df['rate'] - train['default_flag'].mean())
    motif_df = motif_df.sort_values('abs_diff', ascending=False)
    
    # Use top N motifs as features
    for top_n in [50, 100, 200, 500, 1000]:
        top_motifs = motif_df.head(top_n)['motif'].tolist()
        
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
        
        xgb_model = xgb.XGBClassifier(n_estimators=100, max_depth=3, learning_rate=0.1, random_state=42)
        xgb_model.fit(X_train, y_train)
        val_preds_xgb = xgb_model.predict_proba(X_val)[:, 1]
        print(f'Top {top_n} Motifs - XGB Val AUC: {roc_auc_score(y_val, val_preds_xgb):.4f}')

if __name__ == '__main__':
    main()
