import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score
import xgboost as xgb

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

# What if the characters represent a sequence of states, and we need to count the number of times a specific state is visited?
# We already tried character counts and transitions.
# Let's try to find motifs (frequent substrings).

from sklearn.feature_extraction.text import CountVectorizer

vec = CountVectorizer(analyzer='char', ngram_range=(1, 5), min_df=0.05)
X_train = vec.fit_transform(train['symbol_series'])
X_val = vec.transform(val['symbol_series'])

clf = RandomForestClassifier(n_estimators=200, random_state=42)
clf.fit(X_train, train['label'])
y_pred = clf.predict(X_val)
print(f'Motif RF Val Balanced Acc: {balanced_accuracy_score(val["label"], y_pred):.4f}')

clf_xgb = xgb.XGBClassifier(random_state=42, max_depth=3, n_estimators=100)
clf_xgb.fit(X_train, train['label'])
y_pred_xgb = clf_xgb.predict(X_val)
print(f'Motif XGB Val Balanced Acc: {balanced_accuracy_score(val["label"], y_pred_xgb):.4f}')
