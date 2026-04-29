import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import balanced_accuracy_score
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.svm import SVC

train_df = pd.read_csv('data/train.csv')
val_df = pd.read_csv('data/val.csv')

vectorizer = CountVectorizer(analyzer='char', ngram_range=(1, 3))
X_train = vectorizer.fit_transform(train_df['symbol_series'])
X_val = vectorizer.transform(val_df['symbol_series'])

y_train = train_df['label']
y_val = val_df['label']

model = SVC(kernel='rbf', C=1.0, random_state=42)
model.fit(X_train, y_train)
y_val_pred = model.predict(X_val)
acc = balanced_accuracy_score(y_val, y_val_pred)
print(f'SVC (RBF) Val Balanced Accuracy: {acc:.4f}')

model = SVC(kernel='linear', C=1.0, random_state=42)
model.fit(X_train, y_train)
y_val_pred = model.predict(X_val)
acc = balanced_accuracy_score(y_val, y_val_pred)
print(f'SVC (Linear) Val Balanced Accuracy: {acc:.4f}')
