import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
import joblib

# Load data
train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

# Prepare text data (character level)
def prepare_text(series):
    return series.apply(lambda x: ' '.join(list(x)))

X_train_text = prepare_text(train['symbol_series'])
X_val_text = prepare_text(val['symbol_series'])
X_test_text = prepare_text(test['symbol_series'])

y_train = train['label']
y_val = val['label']
y_test = test['label']

# Feature extraction
vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(1, 5), max_features=2000)
X_train = vectorizer.fit_transform(train['symbol_series'])
X_val = vectorizer.transform(val['symbol_series'])
X_test = vectorizer.transform(test['symbol_series'])

# Train model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate
y_val_pred = model.predict(X_val)
val_acc = balanced_accuracy_score(y_val, y_val_pred)
print(f'Validation Balanced Accuracy: {val_acc:.4f}')

y_test_pred = model.predict(X_test)
test_acc = balanced_accuracy_score(y_test, y_test_pred)
print(f'Test Balanced Accuracy: {test_acc:.4f}')

print('\nTest Classification Report:')
print(classification_report(y_test, y_test_pred))
