import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import balanced_accuracy_score
from sklearn.feature_extraction.text import CountVectorizer
import xgboost as xgb

train_df = pd.read_csv('data/train.csv')
val_df = pd.read_csv('data/val.csv')

# Let's try to extract features based on the position of characters
# But one-hot encode them
def extract_pos_ohe_features(df):
    features = []
    chars = ['*', '.', 'u', 'v', 'w', 'x', 'y', 'z']
    char_to_idx = {c: i for i, c in enumerate(chars)}
    for s in df['symbol_series']:
        row = []
        for c in s:
            ohe = [0] * 8
            ohe[char_to_idx[c]] = 1
            row.extend(ohe)
        features.append(row)
    return np.array(features)

X_train_pos = extract_pos_ohe_features(train_df)
X_val_pos = extract_pos_ohe_features(val_df)

vectorizer = CountVectorizer(analyzer='char', ngram_range=(1, 2))
X_train_ngram = vectorizer.fit_transform(train_df['symbol_series']).toarray()
X_val_ngram = vectorizer.transform(val_df['symbol_series']).toarray()

# Add field_id as one-hot
field_ohe = pd.get_dummies(train_df['field_id']).values
field_ohe_val = pd.get_dummies(val_df['field_id']).values

X_train = np.hstack([X_train_pos, X_train_ngram, field_ohe])
X_val = np.hstack([X_val_pos, X_val_ngram, field_ohe_val])

y_train = train_df['label']
y_val = val_df['label']

model = xgb.XGBClassifier(n_estimators=100, max_depth=3, learning_rate=0.05, random_state=42)
model.fit(X_train, y_train)
y_val_pred = model.predict(X_val)
acc = balanced_accuracy_score(y_val, y_val_pred)
print(f'XGBoost Pos+Ngram+Field lr=0.05 md=3 ne=100 Val Balanced Accuracy: {acc:.4f}')
