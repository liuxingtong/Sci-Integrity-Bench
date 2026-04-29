import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import balanced_accuracy_score
from sklearn.feature_extraction.text import CountVectorizer
import xgboost as xgb

train_df = pd.read_csv('data/train.csv')
val_df = pd.read_csv('data/val.csv')

vectorizer = CountVectorizer(analyzer='char', ngram_range=(1, 2))
X_train = vectorizer.fit_transform(train_df['symbol_series'])
X_val = vectorizer.transform(val_df['symbol_series'])

y_train = train_df['label']
y_val = val_df['label']

model = xgb.XGBClassifier(n_estimators=200, max_depth=5, learning_rate=0.1, random_state=42)
model.fit(X_train, y_train)
y_val_pred = model.predict(X_val)
acc = balanced_accuracy_score(y_val, y_val_pred)
print(f'XGBoost Val Balanced Accuracy: {acc:.4f}')
