import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, classification_report

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

X_train_text = train['symbol_series']
y_train = train['label']

X_val_text = val['symbol_series']
y_val = val['label']

X_test_text = test['symbol_series']
y_test = test['label']

# Try character n-grams
for n in [(1, 1), (1, 2), (1, 3), (2, 3), (3, 3)]:
    print(f'\n--- N-gram range: {n} ---')
    vec = CountVectorizer(analyzer='char', ngram_range=n)
    X_train = vec.fit_transform(X_train_text)
    X_val = vec.transform(X_val_text)
    
    clf = LogisticRegression(max_iter=1000, random_state=42)
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_val)
    acc = balanced_accuracy_score(y_val, y_pred)
    print(f'Logistic Regression Val Balanced Acc: {acc:.4f}')
    
    clf_rf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf_rf.fit(X_train, y_train)
    y_pred_rf = clf_rf.predict(X_val)
    acc_rf = balanced_accuracy_score(y_val, y_pred_rf)
    print(f'Random Forest Val Balanced Acc: {acc_rf:.4f}')
