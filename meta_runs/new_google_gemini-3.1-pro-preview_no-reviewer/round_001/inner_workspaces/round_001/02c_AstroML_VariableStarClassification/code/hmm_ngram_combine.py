import pandas as pd
import numpy as np
from hmmlearn import hmm
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.metrics import balanced_accuracy_score
from sklearn.pipeline import FeatureUnion
from sklearn.base import BaseEstimator, TransformerMixin

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

train_0 = train[train['label'] == 0]
X_train_0, lengths_0 = get_sequences(train_0)

train_1 = train[train['label'] == 1]
X_train_1, lengths_1 = get_sequences(train_1)

model_0 = hmm.CategoricalHMM(n_components=2, random_state=42, n_iter=50)
model_0.fit(X_train_0, lengths_0)

model_1 = hmm.CategoricalHMM(n_components=2, random_state=42, n_iter=50)
model_1.fit(X_train_1, lengths_1)

class HMMFeatures(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self
    def transform(self, X):
        features = []
        for s in X:
            seq = np.array([[char_to_idx[c]] for c in s])
            score_0 = model_0.score(seq)
            score_1 = model_1.score(seq)
            features.append([score_0, score_1, score_1 - score_0])
        return np.array(features)

class TextSelector(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self
    def transform(self, X):
        return X

union = FeatureUnion([
    ('hmm', HMMFeatures()),
    ('tfidf', TfidfVectorizer(analyzer='char', ngram_range=(1, 7)))
])

X_train_combined = union.fit_transform(train['symbol_series'])
X_val_combined = union.transform(val['symbol_series'])

clf_lr = LogisticRegression(max_iter=1000, random_state=42)
clf_lr.fit(X_train_combined, train['label'])
acc_lr = balanced_accuracy_score(val['label'], clf_lr.predict(X_val_combined))
print(f'Combined LR Val Balanced Acc: {acc_lr:.4f}')

clf_svc = SVC(kernel='linear', random_state=42)
clf_svc.fit(X_train_combined, train['label'])
acc_svc = balanced_accuracy_score(val['label'], clf_svc.predict(X_val_combined))
print(f'Combined SVC Val Balanced Acc: {acc_svc:.4f}')
