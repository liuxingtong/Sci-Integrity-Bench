import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
import xgboost as xgb

train = pd.read_csv('outputs/train.csv')
val = pd.read_csv('outputs/val.csv')

X_train_seq = train['sym_seq']
y_train = train['default_flag']

X_val_seq = val['sym_seq']
y_val = val['default_flag']

best_auc = 0

for n in range(1, 8):
    for vec_type in ['count', 'tfidf']:
        if vec_type == 'count':
            vectorizer = CountVectorizer(analyzer='char', ngram_range=(1, n))
        else:
            vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(1, n))
            
        X_train = vectorizer.fit_transform(X_train_seq)
        X_val = vectorizer.transform(X_val_seq)
        
        for C in [0.01, 0.1, 1.0, 10.0]:
            lr = LogisticRegression(max_iter=1000, C=C)
            lr.fit(X_train, y_train)
            auc = roc_auc_score(y_val, lr.predict_proba(X_val)[:, 1])
            if auc > best_auc:
                best_auc = auc
                print(f'New best! {vec_type} (1, {n}), LR C={C}, AUC: {auc:.4f}')
                
        xgb_model = xgb.XGBClassifier(n_estimators=100, random_state=42, eval_metric='logloss', max_depth=3, learning_rate=0.1)
        xgb_model.fit(X_train, y_train)
        auc = roc_auc_score(y_val, xgb_model.predict_proba(X_val)[:, 1])
        if auc > best_auc:
            best_auc = auc
            print(f'New best! {vec_type} (1, {n}), XGB, AUC: {auc:.4f}')
