import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score
import xgboost as xgb

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

# Let's try to use the ternary representation as a sequence and train a model on it.

def get_ternary_seq(df):
    features = []
    for s in df['symbol_series']:
        ter_s = [0 if c in ['*', '.'] else 1 if c in ['u', 'v', 'w'] else 2 for c in s]
        features.append(ter_s)
    return np.array(features)

X_train = get_ternary_seq(train)
X_val = get_ternary_seq(val)

clf = RandomForestClassifier(n_estimators=200, random_state=42)
clf.fit(X_train, train['label'])
y_pred = clf.predict(X_val)
print(f'Ternary Seq RF Val Balanced Acc: {balanced_accuracy_score(val["label"], y_pred):.4f}')

clf_xgb = xgb.XGBClassifier(random_state=42, max_depth=3, n_estimators=100)
clf_xgb.fit(X_train, train['label'])
y_pred_xgb = clf_xgb.predict(X_val)
print(f'Ternary Seq XGB Val Balanced Acc: {balanced_accuracy_score(val["label"], y_pred_xgb):.4f}')

# What if we use the ternary sequence with TF-IDF?
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC

def get_ternary_str(df):
    features = []
    for s in df['symbol_series']:
        ter_s = "".join(['0' if c in ['*', '.'] else '1' if c in ['u', 'v', 'w'] else '2' for c in s])
        features.append(ter_s)
    return features

X_train_str = get_ternary_str(train)
X_val_str = get_ternary_str(val)

vec = TfidfVectorizer(analyzer='char', ngram_range=(1, 10))
X_train_tfidf = vec.fit_transform(X_train_str)
X_val_tfidf = vec.transform(X_val_str)

clf_svc = SVC(kernel='linear', random_state=42)
clf_svc.fit(X_train_tfidf, train['label'])
y_pred_svc = clf_svc.predict(X_val_tfidf)
print(f'Ternary TF-IDF SVC Val Balanced Acc: {balanced_accuracy_score(val["label"], y_pred_svc):.4f}')
