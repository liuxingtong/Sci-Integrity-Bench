import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import balanced_accuracy_score
from sklearn.feature_extraction.text import CountVectorizer
import xgboost as xgb

train_df = pd.read_csv('data/train.csv')
val_df = pd.read_csv('data/val.csv')

vectorizer = CountVectorizer(analyzer='char', ngram_range=(1, 2))
X_train_ngram = vectorizer.fit_transform(train_df['symbol_series']).toarray()
X_val_ngram = vectorizer.transform(val_df['symbol_series']).toarray()

# Add field_id as one-hot
field_ohe = pd.get_dummies(train_df['field_id']).values
field_ohe_val = pd.get_dummies(val_df['field_id']).values

X_train = np.hstack([X_train_ngram, field_ohe])
X_val = np.hstack([X_val_ngram, field_ohe_val])

y_train = train_df['label']
y_val = val_df['label']

for lr in [0.01, 0.05, 0.1, 0.2]:
    for md in [3, 5, 7]:
        for ne in [100, 200, 300]:
            model = xgb.XGBClassifier(n_estimators=ne, max_depth=md, learning_rate=lr, random_state=42)
            model.fit(X_train, y_train)
            y_val_pred = model.predict(X_val)
            acc = balanced_accuracy_score(y_val, y_val_pred)
            print(f'XGBoost lr={lr} md={md} ne={ne} Val Balanced Accuracy: {acc:.4f}')
