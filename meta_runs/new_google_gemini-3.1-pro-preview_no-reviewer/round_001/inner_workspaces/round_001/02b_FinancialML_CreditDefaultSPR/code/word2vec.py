import pandas as pd
import numpy as np
from gensim.models import Word2Vec
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
import xgboost as xgb

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

def get_ngrams(seq, n):
    return [seq[i:i+n] for i in range(len(seq)-n+1)]

for n in [1, 2, 3, 4]:
    print(f'\n--- N-gram size: {n} ---')
    sentences = [get_ngrams(seq, n) for seq in train['sym_seq']]
    
    w2v = Word2Vec(sentences, vector_size=32, window=5, min_count=1, workers=4, seed=42)
    
    def get_seq_vector(seq):
        ngrams = get_ngrams(seq, n)
        vectors = [w2v.wv[ngram] for ngram in ngrams if ngram in w2v.wv]
        if not vectors:
            return np.zeros(32)
        return np.mean(vectors, axis=0)
        
    X_train = np.array([get_seq_vector(seq) for seq in train['sym_seq']])
    y_train = train['default_flag']
    
    X_val = np.array([get_seq_vector(seq) for seq in val['sym_seq']])
    y_val = val['default_flag']
    
    models = {
        'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42),
        'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
        'XGBoost': xgb.XGBClassifier(eval_metric='logloss', random_state=42)
    }
    
    for name, model in models.items():
        model.fit(X_train, y_train)
        y_val_pred = model.predict_proba(X_val)[:, 1]
        auc = roc_auc_score(y_val, y_val_pred)
        print(f'{name} Val AUC: {auc:.4f}')
