import pandas as pd
import numpy as np
import json
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import warnings
warnings.filterwarnings('ignore')

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
    
    # Separate features and target
    token_cols = [c for c in train.columns if c.startswith('token_')]
    X_train = train[token_cols]
    y_train = train['label']
    X_val = val[token_cols]
    y_val = val['label']
    X_test = test[token_cols]
    y_test = test['label']
    
    # One-hot encode each token column
    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(handle_unknown='ignore'), token_cols)
        ])
    
    # Define model
    model = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', RandomForestClassifier(random_state=42, n_estimators=100))
    ])
    
    # Train
    model.fit(X_train, y_train)
    
    # Evaluate on validation set
    y_val_pred = model.predict(X_val)
    val_acc = accuracy_score(y_val, y_val_pred)
    print(f'Validation accuracy: {val_acc:.4f}')
    
    # Hyperparameter tuning (simple grid search)
    best_acc = val_acc
    best_params = {'n_estimators': 100, 'max_depth': None}
    for n_est in [50, 100, 200]:
        for max_depth in [None, 10, 20, 30]:
            model = Pipeline(steps=[
                ('preprocessor', preprocessor),
                ('classifier', RandomForestClassifier(random_state=42, n_estimators=n_est, max_depth=max_depth))
            ])
            model.fit(X_train, y_train)
            y_val_pred = model.predict(X_val)
            acc = accuracy_score(y_val, y_val_pred)
            if acc > best_acc:
                best_acc = acc
                best_params = {'n_estimators': n_est, 'max_depth': max_depth}
    print(f'Best validation accuracy after tuning: {best_acc:.4f}')
    print(f'Best params: {best_params}')
    
    # Retrain with best params on train+val combined for final model
    X_trainval = pd.concat([X_train, X_val], axis=0)
    y_trainval = pd.concat([y_train, y_val], axis=0)
    final_model = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', RandomForestClassifier(random_state=42, 
                                              n_estimators=best_params['n_estimators'], 
                                              max_depth=best_params['max_depth']))
    ])
    final_model.fit(X_trainval, y_trainval)
    
    # Predict on test
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
        'vocab_size': X_train[token_cols[0]].nunique()  # approximate
    })

# Save results
df_results = pd.DataFrame(results)
df_results.to_csv('../outputs/benchmark_results.csv', index=False)
print('\n=== Summary ===')
print(df_results.to_string(index=False))