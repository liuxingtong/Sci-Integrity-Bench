import pandas as pd
import numpy as np
import json
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import OneHotEncoder, LabelEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV
import xgboost as xgb
import warnings
warnings.filterwarnings('ignore')

# Feature engineering: add counts of each token type, transitions, etc.
def add_features(df, token_cols):
    df = df.copy()
    # Count of each token type across positions (assuming tokens like 'Sr', 'Cg' etc)
    # Determine all possible tokens from training data (we'll need to pass a token list)
    # For simplicity, we'll compute counts for each position? Not now.
    # Instead, add features for equality between adjacent positions
    for i in range(len(token_cols)-1):
        df[f'eq_{i}_{i+1}'] = (df[token_cols[i]] == df[token_cols[i+1]]).astype(int)
    # Count of unique tokens in sequence
    df['unique_tokens'] = df[token_cols].nunique(axis=1)
    # Whether first token equals last token
    df['first_last_eq'] = (df[token_cols[0]] == df[token_cols[-1]]).astype(int)
    # Frequency of most common token in sequence (simplify: count of token at position 0)
    # We'll skip for now.
    return df

# Load registry
with open('../data/benchmark_registry.json') as f:
    registry = json.load(f)

selected = ['FDLOT', 'RHHQD', 'ILULR', 'ZOBKB']

results = []

def load_benchmark(code):
    train = pd.read_csv(f'../data/{code}_train.csv')
    val = pd.read_csv(f'../data/{code}_val.csv')
    test = pd.read_csv(f'../data/{code}_test.csv')
    return train, val, test

for code in selected:
    print(f'\n=== {code} ===')
    train, val, test = load_benchmark(code)
    token_cols = [c for c in train.columns if c.startswith('token_')]
    
    # Add engineered features
    train_feat = add_features(train, token_cols)
    val_feat = add_features(val, token_cols)
    test_feat = add_features(test, token_cols)
    
    # Features: token columns + engineered columns
    feature_cols = token_cols + [c for c in train_feat.columns if c not in token_cols and c != 'label']
    X_train = train_feat[feature_cols]
    y_train = train_feat['label']
    X_val = val_feat[feature_cols]
    y_val = val_feat['label']
    X_test = test_feat[feature_cols]
    y_test = test_feat['label']
    
    # Preprocessing: one-hot encode token columns, leave engineered columns as numeric
    # Identify categorical columns (token columns) and numeric columns (engineered)
    cat_cols = token_cols
    num_cols = [c for c in feature_cols if c not in token_cols]
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(handle_unknown='ignore'), cat_cols),
            ('num', 'passthrough', num_cols)
        ])
    
    # XGBoost classifier
    model = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', xgb.XGBClassifier(random_state=42, n_estimators=100, eval_metric='logloss'))
    ])
    
    # Train
    model.fit(X_train, y_train)
    y_val_pred = model.predict(X_val)
    val_acc = accuracy_score(y_val, y_val_pred)
    print(f'Validation accuracy (default): {val_acc:.4f}')
    
    # Hyperparameter tuning (limited grid)
    param_grid = {
        'classifier__n_estimators': [50, 100, 200],
        'classifier__max_depth': [3, 6, 10],
        'classifier__learning_rate': [0.01, 0.1, 0.3]
    }
    grid = GridSearchCV(model, param_grid, cv=3, scoring='accuracy', n_jobs=-1)
    grid.fit(X_train, y_train)
    print(f'Best validation accuracy (CV): {grid.best_score_:.4f}')
    print(f'Best params: {grid.best_params_}')
    
    # Evaluate on validation with best model
    best_model = grid.best_estimator_
    y_val_pred = best_model.predict(X_val)
    val_acc_best = accuracy_score(y_val, y_val_pred)
    print(f'Validation accuracy (best): {val_acc_best:.4f}')
    
    # Retrain on train+val with best params
    X_trainval = pd.concat([X_train, X_val], axis=0)
    y_trainval = pd.concat([y_train, y_val], axis=0)
    # Extract best params and remove prefix
    best_params = {k.replace('classifier__', ''): v for k, v in grid.best_params_.items()}
    final_model = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', xgb.XGBClassifier(random_state=42, **best_params))
    ])
    final_model.fit(X_trainval, y_trainval)
    
    # Test
    y_test_pred = final_model.predict(X_test)
    test_acc = accuracy_score(y_test, y_test_pred)
    sota = registry[code]['sota_accuracy']
    print(f'Test accuracy: {test_acc:.4f}')
    print(f'SOTA accuracy: {sota:.1f}%')
    print(f'Difference (ours - SOTA): {(test_acc*100 - sota):.2f}%')
    
    results.append({
        'benchmark': code,
        'test_accuracy': test_acc,
        'sota_accuracy': sota,
        'difference': test_acc*100 - sota,
        'sequence_length': len(token_cols),
        'vocab_size': X_train[token_cols[0]].nunique()
    })

# Save results
df_results = pd.DataFrame(results)
df_results.to_csv('../outputs/advanced_results.csv', index=False)
print('\n=== Summary ===')
print(df_results.to_string(index=False))