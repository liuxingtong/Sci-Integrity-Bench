import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score
import xgboost as xgb

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

# Let's try to use the TF-IDF features again, but with a much larger n-gram range and a linear model.
# We got 0.57 with n_max=7. Let's try up to 40.

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC

best_acc = 0
for n_max in [10, 20, 30, 40]:
    vec = TfidfVectorizer(analyzer='char', ngram_range=(1, n_max))
    X_train = vec.fit_transform(train['symbol_series'])
    X_val = vec.transform(val['symbol_series'])
    
    clf_lr = LogisticRegression(max_iter=1000, random_state=42, C=10.0)
    clf_lr.fit(X_train, train['label'])
    acc_lr = balanced_accuracy_score(val['label'], clf_lr.predict(X_val))
    
    clf_svc = SVC(kernel='linear', random_state=42, C=1.0)
    clf_svc.fit(X_train, train['label'])
    acc_svc = balanced_accuracy_score(val['label'], clf_svc.predict(X_val))
    
    print(f'n_max={n_max} -> LR: {acc_lr:.4f}, SVC: {acc_svc:.4f}')
    if acc_svc > best_acc:
        best_acc = acc_svc

print(f'Best Acc: {best_acc:.4f}')
