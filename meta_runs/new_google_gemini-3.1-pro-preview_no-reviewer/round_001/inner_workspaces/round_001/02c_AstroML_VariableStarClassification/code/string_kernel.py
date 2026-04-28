import pandas as pd
import numpy as np
from sklearn.svm import SVC
from sklearn.metrics import balanced_accuracy_score

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

# Let's try a simple spectrum kernel (k-mer counts)
from sklearn.feature_extraction.text import CountVectorizer

for k in range(1, 8):
    vec = CountVectorizer(analyzer='char', ngram_range=(k, k))
    X_train = vec.fit_transform(train['symbol_series'])
    X_val = vec.transform(val['symbol_series'])
    
    clf = SVC(kernel='linear', C=1.0)
    clf.fit(X_train, train['label'])
    y_pred = clf.predict(X_val)
    acc = balanced_accuracy_score(val['label'], y_pred)
    print(f'k={k} Linear SVC Val Balanced Acc: {acc:.4f}')
    
    clf_rbf = SVC(kernel='rbf', C=1.0)
    clf_rbf.fit(X_train, train['label'])
    y_pred_rbf = clf_rbf.predict(X_val)
    acc_rbf = balanced_accuracy_score(val['label'], y_pred_rbf)
    print(f'k={k} RBF SVC Val Balanced Acc: {acc_rbf:.4f}')
