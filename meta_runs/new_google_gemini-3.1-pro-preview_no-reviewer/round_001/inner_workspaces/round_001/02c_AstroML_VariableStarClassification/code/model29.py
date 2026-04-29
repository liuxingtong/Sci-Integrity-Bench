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

X_train_all = np.hstack([X_train_ngram, field_ohe, X_train_simple])
X_val_all = np.hstack([X_val_ngram, field_ohe_val, X_val_simple])

y_train = train_df['label']
y_val = val_df['label']

for lr in [0.03, 0.05, 0.07]:
    for md in [2, 3, 4]:
        for ne in [50, 100, 150]:
            model = xgb.XGBClassifier(n_estimators=ne, max_depth=md, learning_rate=lr, random_state=42)
            model.fit(X_train_all, y_train)
            y_val_pred = model.predict(X_val_all)
            acc = balanced_accuracy_score(y_val, y_val_pred)
            print(f'XGBoost lr={lr} md={md} ne={ne} Val Balanced Accuracy: {acc:.4f}')
