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

model = xgb.XGBClassifier(n_estimators=100, max_depth=3, learning_rate=0.05, random_state=42)
model.fit(X_train, y_train)
y_val_pred = model.predict(X_val)
acc = balanced_accuracy_score(y_val, y_val_pred)
print(f'XGBoost Ngram+Field lr=0.05 md=3 ne=100 Val Balanced Accuracy: {acc:.4f}')

# Let's try to add some simple sequence features
def extract_simple_features(df):
    features = []
    for s in df['symbol_series']:
        # Number of unique characters
        n_unique = len(set(s))
        # Max consecutive identical characters
        max_c = 1
        curr_c = 1
        for i in range(1, len(s)):
            if s[i] == s[i-1]:
                curr_c += 1
                max_c = max(max_c, curr_c)
            else:
                curr_c = 1
        features.append([n_unique, max_c])
    return np.array(features)

# Let's try to add some simple sequence features
def extract_simple_features2(df):
    features = []
    for s in df['symbol_series']:
        # Number of unique characters
        n_unique = len(set(s))
        features.append([n_unique])
    return np.array(features)

X_train_simple = extract_simple_features2(train_df)
X_val_simple = extract_simple_features2(val_df)

X_train_all = np.hstack([X_train, X_train_simple])
X_val_all = np.hstack([X_val, X_val_simple])

model = xgb.XGBClassifier(n_estimators=100, max_depth=3, learning_rate=0.05, random_state=42)
model.fit(X_train_all, y_train)
y_val_pred = model.predict(X_val_all)
acc = balanced_accuracy_score(y_val, y_val_pred)
print(f'XGBoost Ngram+Field+Simple2 lr=0.05 md=3 ne=100 Val Balanced Accuracy: {acc:.4f}')
