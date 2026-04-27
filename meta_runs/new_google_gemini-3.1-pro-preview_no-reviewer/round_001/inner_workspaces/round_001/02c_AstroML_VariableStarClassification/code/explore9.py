import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

# The baseline is 0.78. This means there is a strong signal.
# Let's try a simple TF-IDF with character n-grams, but with different parameters.

for n in range(1, 6):
    vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(n, n))
    X_train = vectorizer.fit_transform(train['symbol_series'])
    X_val = vectorizer.transform(val['symbol_series'])
    
    model = LogisticRegression(random_state=42, max_iter=1000)
    model.fit(X_train, train['label'])
    
    val_pred = model.predict(X_val)
    acc = balanced_accuracy_score(val['label'], val_pred)
    print(f'n-gram {n} Val Acc: {acc:.4f}')

print("\nTrying combinations:")
for n_max in range(2, 6):
    vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(1, n_max))
    X_train = vectorizer.fit_transform(train['symbol_series'])
    X_val = vectorizer.transform(val['symbol_series'])
    
    model = LogisticRegression(random_state=42, max_iter=1000)
    model.fit(X_train, train['label'])
    
    val_pred = model.predict(X_val)
    acc = balanced_accuracy_score(val['label'], val_pred)
    print(f'n-gram 1 to {n_max} Val Acc: {acc:.4f}')
