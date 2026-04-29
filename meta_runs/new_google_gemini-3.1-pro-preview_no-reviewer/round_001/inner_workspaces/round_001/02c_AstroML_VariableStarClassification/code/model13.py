import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.svm import SVC
import xgboost as xgb

train_df = pd.read_csv('data/train.csv')
val_df = pd.read_csv('data/val.csv')

for n in range(1, 11):
    vectorizer = CountVectorizer(analyzer='char', ngram_range=(1, n))
    X_train = vectorizer.fit_transform(train_df['symbol_series'])
    X_val = vectorizer.transform(val_df['symbol_series'])
    
    y_train = train_df['label']
    y_val = val_df['label']
    
    model = LogisticRegression(max_iter=1000, random_state=42)
    model.fit(X_train, y_train)
    y_val_pred = model.predict(X_val)
    acc = balanced_accuracy_score(y_val, y_val_pred)
    print(f'LR Count N-gram (1, {n}) Val Balanced Accuracy: {acc:.4f}')
    
    model = SVC(kernel='rbf', random_state=42)
    model.fit(X_train, y_train)
    y_val_pred = model.predict(X_val)
    acc = balanced_accuracy_score(y_val, y_val_pred)
    print(f'SVC Count N-gram (1, {n}) Val Balanced Accuracy: {acc:.4f}')
    
    model = xgb.XGBClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    y_val_pred = model.predict(X_val)
    acc = balanced_accuracy_score(y_val, y_val_pred)
    print(f'XGB Count N-gram (1, {n}) Val Balanced Accuracy: {acc:.4f}')
    print('-'*30)
