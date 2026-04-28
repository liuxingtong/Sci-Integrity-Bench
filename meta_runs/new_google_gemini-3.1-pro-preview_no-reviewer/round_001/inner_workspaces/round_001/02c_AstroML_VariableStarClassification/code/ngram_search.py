import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.metrics import balanced_accuracy_score
import xgboost as xgb

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

X_train_text = train['symbol_series']
y_train = train['label']

X_val_text = val['symbol_series']
y_val = val['label']

best_acc = 0
best_params = {}

for n_max in [3, 5, 7, 10, 15, 20]:
    for vec_type in ['count', 'tfidf']:
        if vec_type == 'count':
            vec = CountVectorizer(analyzer='char', ngram_range=(1, n_max))
        else:
            vec = TfidfVectorizer(analyzer='char', ngram_range=(1, n_max))
            
        X_train = vec.fit_transform(X_train_text)
        X_val = vec.transform(X_val_text)
        
        # Logistic Regression
        clf_lr = LogisticRegression(max_iter=1000, random_state=42, C=1.0)
        clf_lr.fit(X_train, y_train)
        acc_lr = balanced_accuracy_score(y_val, clf_lr.predict(X_val))
        if acc_lr > best_acc:
            best_acc = acc_lr
            best_params = {'n_max': n_max, 'vec': vec_type, 'clf': 'LR'}
            
        # SVC
        clf_svc = SVC(kernel='linear', random_state=42)
        clf_svc.fit(X_train, y_train)
        acc_svc = balanced_accuracy_score(y_val, clf_svc.predict(X_val))
        if acc_svc > best_acc:
            best_acc = acc_svc
            best_params = {'n_max': n_max, 'vec': vec_type, 'clf': 'SVC_Linear'}
            
        clf_svc_rbf = SVC(kernel='rbf', random_state=42)
        clf_svc_rbf.fit(X_train, y_train)
        acc_svc_rbf = balanced_accuracy_score(y_val, clf_svc_rbf.predict(X_val))
        if acc_svc_rbf > best_acc:
            best_acc = acc_svc_rbf
            best_params = {'n_max': n_max, 'vec': vec_type, 'clf': 'SVC_RBF'}
            
        # XGBoost
        clf_xgb = xgb.XGBClassifier(random_state=42, max_depth=3, n_estimators=100)
        clf_xgb.fit(X_train, y_train)
        acc_xgb = balanced_accuracy_score(y_val, clf_xgb.predict(X_val))
        if acc_xgb > best_acc:
            best_acc = acc_xgb
            best_params = {'n_max': n_max, 'vec': vec_type, 'clf': 'XGB'}
            
        print(f"n_max={n_max}, vec={vec_type} -> LR: {acc_lr:.4f}, SVC_L: {acc_svc:.4f}, SVC_R: {acc_svc_rbf:.4f}, XGB: {acc_xgb:.4f}")

print(f"\nBest Acc: {best_acc:.4f} with {best_params}")
