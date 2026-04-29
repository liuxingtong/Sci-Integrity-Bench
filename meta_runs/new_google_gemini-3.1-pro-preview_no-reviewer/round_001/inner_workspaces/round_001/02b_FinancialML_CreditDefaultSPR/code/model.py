import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.metrics import roc_auc_score
import xgboost as xgb

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

X_train_text = train['sym_seq']
y_train = train['default_flag']

X_val_text = val['sym_seq']
y_val = val['default_flag']

X_test_text = test['sym_seq']
y_test = test['default_flag']

# Try different n-gram ranges
for ngram_range in [(1, 1), (1, 2), (1, 3), (2, 2), (2, 3), (3, 3), (4, 4), (1, 4)]:
    print(f'\n--- N-gram range: {ngram_range} ---')
    vectorizer = CountVectorizer(ngram_range=ngram_range, analyzer='char')
    X_train = vectorizer.fit_transform(X_train_text)
    X_val = vectorizer.transform(X_val_text)
    
    models = {
        'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42),
        'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
        'SVM': SVC(probability=True, random_state=42),
        'XGBoost': xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=42)
    }
    
    for name, model in models.items():
        model.fit(X_train, y_train)
        y_val_pred = model.predict_proba(X_val)[:, 1]
        auc = roc_auc_score(y_val, y_val_pred)
        print(f'{name} Val AUC: {auc:.4f}')
