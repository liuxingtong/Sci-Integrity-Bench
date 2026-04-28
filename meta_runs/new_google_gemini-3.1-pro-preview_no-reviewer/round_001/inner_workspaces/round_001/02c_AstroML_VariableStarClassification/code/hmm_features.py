import pandas as pd
import numpy as np
from hmmlearn import hmm
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

chars = sorted(list(set(''.join(train['symbol_series']))))
char_to_idx = {c: i for i, c in enumerate(chars)}

def get_sequences(df):
    seqs = []
    lengths = []
    for s in df['symbol_series']:
        seqs.extend([[char_to_idx[c]] for c in s])
        lengths.append(len(s))
    return np.array(seqs), lengths

X_train_seq, lengths_train = get_sequences(train)
X_val_seq, lengths_val = get_sequences(val)

# Train HMM on class 0
train_0 = train[train['label'] == 0]
X_train_0, lengths_0 = get_sequences(train_0)
model_0 = hmm.CategoricalHMM(n_components=4, random_state=42, n_iter=100)
model_0.fit(X_train_0, lengths_0)

# Train HMM on class 1
train_1 = train[train['label'] == 1]
X_train_1, lengths_1 = get_sequences(train_1)
model_1 = hmm.CategoricalHMM(n_components=4, random_state=42, n_iter=100)
model_1.fit(X_train_1, lengths_1)

def get_hmm_features(df):
    features = []
    for s in df['symbol_series']:
        seq = np.array([[char_to_idx[c]] for c in s])
        score_0 = model_0.score(seq)
        score_1 = model_1.score(seq)
        features.append([score_0, score_1, score_1 - score_0])
    return np.array(features)

X_train_hmm = get_hmm_features(train)
X_val_hmm = get_hmm_features(val)

clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train_hmm, train['label'])
y_pred = clf.predict(X_val_hmm)
print(f'HMM RF Val Balanced Acc: {balanced_accuracy_score(val["label"], y_pred):.4f}')

# Simple thresholding
y_pred_thresh = (X_val_hmm[:, 2] > 0).astype(int)
print(f'HMM Thresh Val Balanced Acc: {balanced_accuracy_score(val["label"], y_pred_thresh):.4f}')
