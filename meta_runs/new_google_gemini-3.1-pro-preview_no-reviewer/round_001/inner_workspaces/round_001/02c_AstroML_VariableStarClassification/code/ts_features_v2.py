import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score
import xgboost as xgb
from scipy.signal import periodogram

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

# The characters seem to represent magnitudes or fluxes.
# Let's try to find the best mapping by looking at the baseline.
# The baseline is 0.78. We are far from it.
# Maybe the characters are just categorical and we should use string kernels or more advanced n-grams.
# Let's try TF-IDF with character n-grams again, but with more features.

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC

X_train_text = train['symbol_series']
y_train = train['label']

X_val_text = val['symbol_series']
y_val = val['label']

for n in [(1, 4), (2, 4), (3, 5), (4, 6)]:
    print(f'\n--- TF-IDF N-gram range: {n} ---')
    vec = TfidfVectorizer(analyzer='char', ngram_range=n)
    X_train = vec.fit_transform(X_train_text)
    X_val = vec.transform(X_val_text)
    
    clf = SVC(kernel='linear', random_state=42)
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_val)
    acc = balanced_accuracy_score(y_val, y_pred)
    print(f'SVC Linear Val Balanced Acc: {acc:.4f}')
    
    clf_rbf = SVC(kernel='rbf', random_state=42)
    clf_rbf.fit(X_train, y_train)
    y_pred_rbf = clf_rbf.predict(X_val)
    acc_rbf = balanced_accuracy_score(y_val, y_pred_rbf)
    print(f'SVC RBF Val Balanced Acc: {acc_rbf:.4f}')
    
    clf_rf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf_rf.fit(X_train, y_train)
    y_pred_rf = clf_rf.predict(X_val)
    acc_rf = balanced_accuracy_score(y_val, y_pred_rf)
    print(f'Random Forest Val Balanced Acc: {acc_rf:.4f}')
