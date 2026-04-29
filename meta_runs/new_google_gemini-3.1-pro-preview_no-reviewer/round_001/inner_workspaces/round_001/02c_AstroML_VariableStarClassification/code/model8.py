import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer

train_df = pd.read_csv('data/train.csv')
val_df = pd.read_csv('data/val.csv')

for n in [1, 2, 3, 4, 5, 6]:
    vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(1, n))
    X_train = vectorizer.fit_transform(train_df['symbol_series'])
    X_val = vectorizer.transform(val_df['symbol_series'])
    
    y_train = train_df['label']
    y_val = val_df['label']
    
    model = LogisticRegression(max_iter=1000, C=1.0, random_state=42)
    model.fit(X_train, y_train)
    y_val_pred = model.predict(X_val)
    acc = balanced_accuracy_score(y_val, y_val_pred)
    print(f'TF-IDF N-gram (1, {n}) Val Balanced Accuracy: {acc:.4f}')
