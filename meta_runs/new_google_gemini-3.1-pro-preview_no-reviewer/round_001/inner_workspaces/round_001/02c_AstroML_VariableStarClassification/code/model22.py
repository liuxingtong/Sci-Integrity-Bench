import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import balanced_accuracy_score
from sklearn.feature_extraction.text import CountVectorizer
import xgboost as xgb

train_df = pd.read_csv('data/train.csv')
val_df = pd.read_csv('data/val.csv')

vectorizer = CountVectorizer(analyzer='char', ngram_range=(2, 2))
X_train_ngram = vectorizer.fit_transform(train_df['symbol_series']).toarray()
X_val_ngram = vectorizer.transform(val_df['symbol_series']).toarray()

# Add field_id as one-hot
field_ohe = pd.get_dummies(train_df['field_id']).values
field_ohe_val = pd.get_dummies(val_df['field_id']).values

X_train = np.hstack([X_train_ngram, field_ohe])
X_val = np.hstack([X_val_ngram, field_ohe_val])

y_train = train_df['label']
y_val = val_df['label']

model = xgb.XGBClassifier(n_estimators=200, max_depth=5, learning_rate=0.1, random_state=42)
model.fit(X_train, y_train)
y_val_pred = model.predict(X_val)
acc = balanced_accuracy_score(y_val, y_val_pred)
print(f'XGBoost N-gram(2,2) + Field Val Balanced Accuracy: {acc:.4f}')
