import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, roc_auc_score, classification_report
from sklearn.feature_extraction.text import CountVectorizer
import matplotlib.pyplot as plt
import seaborn as sns

def extract_features(df):
    # We can treat the sequence as a string of characters and use CountVectorizer with char analyzer
    return df['symbol_series']

train_df = pd.read_csv('data/train.csv')
val_df = pd.read_csv('data/val.csv')
test_df = pd.read_csv('data/test.csv')

vectorizer = CountVectorizer(analyzer='char', ngram_range=(1, 2))
X_train = vectorizer.fit_transform(train_df['symbol_series'])
X_val = vectorizer.transform(val_df['symbol_series'])
X_test = vectorizer.transform(test_df['symbol_series'])

y_train = train_df['label']
y_val = val_df['label']
y_test = test_df['label']

print(f'Number of features: {X_train.shape[1]}')

models = {
    'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42),
    'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
    'Gradient Boosting': GradientBoostingClassifier(n_estimators=100, random_state=42)
}

for name, model in models.items():
    model.fit(X_train, y_train)
    y_val_pred = model.predict(X_val)
    acc = balanced_accuracy_score(y_val, y_val_pred)
    print(f'{name} Val Balanced Accuracy: {acc:.4f}')
