import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import CountVectorizer

train = pd.read_csv('outputs/train.csv')
val = pd.read_csv('outputs/val.csv')
test = pd.read_csv('outputs/test.csv')

vectorizer = CountVectorizer(analyzer='char', ngram_range=(1, 10))
X_train = vectorizer.fit_transform(train['sym_seq'])
X_val = vectorizer.transform(val['sym_seq'])

y_train = train['default_flag']
y_val = val['default_flag']

for C in [0.01, 0.1, 1.0, 10.0]:
    lr = LogisticRegression(penalty='l1', solver='liblinear', C=C, random_state=42)
    lr.fit(X_train, y_train)
    val_preds = lr.predict_proba(X_val)[:, 1]
    auc = roc_auc_score(y_val, val_preds)
    print(f'C={C}, Val AUC: {auc:.4f}')
