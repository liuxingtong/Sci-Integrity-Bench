import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score
from sklearn.svm import SVC

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

# Let's try CountVectorizer instead of TF-IDF
for n_max in range(2, 6):
    vectorizer = CountVectorizer(analyzer='char', ngram_range=(1, n_max))
    X_train = vectorizer.fit_transform(train['symbol_series'])
    X_val = vectorizer.transform(val['symbol_series'])
    
    model = SVC(random_state=42)
    model.fit(X_train, train['label'])
    
    val_pred = model.predict(X_val)
    acc = balanced_accuracy_score(val['label'], val_pred)
    print(f'CountVec n-gram 1 to {n_max} SVC Val Acc: {acc:.4f}')
    
    model = RandomForestClassifier(random_state=42)
    model.fit(X_train, train['label'])
    
    val_pred = model.predict(X_val)
    acc = balanced_accuracy_score(val['label'], val_pred)
    print(f'CountVec n-gram 1 to {n_max} RF Val Acc: {acc:.4f}')
