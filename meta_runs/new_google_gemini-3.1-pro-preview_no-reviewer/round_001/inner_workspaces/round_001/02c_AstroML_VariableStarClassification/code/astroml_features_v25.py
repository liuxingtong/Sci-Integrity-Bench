import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score
import xgboost as xgb
import zlib
import bz2
import lzma

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

def get_compression_features(df):
    features = []
    for s in df['symbol_series']:
        b = s.encode('utf-8')
        features.append([
            len(zlib.compress(b)),
            len(bz2.compress(b)),
            len(lzma.compress(b))
        ])
    return np.array(features)

X_train = get_compression_features(train)
X_val = get_compression_features(val)

clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, train['label'])
y_pred = clf.predict(X_val)
print(f'Compression RF Val Balanced Acc: {balanced_accuracy_score(val["label"], y_pred):.4f}')
