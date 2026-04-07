import pandas as pd
import numpy as np
import json
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
import warnings
warnings.filterwarnings('ignore')

# Load registry
with open('../data/benchmark_registry.json') as f:
    registry = json.load(f)

selected = ['FDLOT', 'RHHQD', 'ILULR', 'ZOBKB']

def load_benchmark(code):
    train = pd.read_csv(f'../data/{code}_train.csv')
    val = pd.read_csv(f'../data/{code}_val.csv')
    test = pd.read_csv(f'../data/{code}_test.csv')
    return train, val, test

def add_shape_color_features(df, token_cols):
    df = df.copy()
    shape_cols = []
    color_cols = []
    for col in token_cols:
        shape = df[col].str[0]
        color = df[col].str[1]
        df[f'{col}_shape'] = shape
        df[f'{col}_color'] = color
        shape_cols.append(f'{col}_shape')
        color_cols.append(f'{col}_color')
    # Additional features
    # Count of each shape across sequence
    shapes = ['S', 'C', 'T', 'D']
    for s in shapes:
        df[f'count_{s}'] = (df[shape_cols] == s).sum(axis=1)
    # Count of each color
    colors = ['r', 'g', 'b', 'y']
    for c in colors:
        df[f'count_color_{c}'] = (df[color_cols] == c).sum(axis=1)
    # Whether shape matches color at each position (if shape and color correspond?)
    for i, col in enumerate(token_cols):
        df[f'match_{i}'] = (df[shape_cols[i]] == df[color_cols[i]]).astype(int)  # nonsense, but maybe
    # Number of unique shapes
    df['unique_shapes'] = df[shape_cols].nunique(axis=1)
    df['unique_colors'] = df[color_cols].nunique(axis=1)
    # Equality between adjacent positions (shape and color)
    for i in range(len(token_cols)-1):
        df[f'shape_eq_{i}_{i+1}'] = (df[shape_cols[i]] == df[shape_cols[i+1]]).astype(int)
        df[f'color_eq_{i}_{i+1}'] = (df[color_cols[i]] == df[color_cols[i+1]]).astype(int)
    # Parity of counts
    for s in shapes:
        df[f'count_{s}_parity'] = df[f'count_{s}'] % 2
    for c in colors:
        df[f'count_color_{c}_parity'] = df[f'count_color_{c}'] % 2
    return df, shape_cols, color_cols

results = []
for code in selected:
    print(f'\n=== {code} ===')
    train, val, test = load_benchmark(code)
    token_cols = [c for c in train.columns if c.startswith('token_')]
    
    train_feat, shape_cols, color_cols = add_shape_color_features(train, token_cols)
    val_feat, _, _ = add_shape_color_features(val, token_cols)
    test_feat, _, _ = add_shape_color_features(test, token_cols)
    
    # Feature columns: shape and color categorical, plus numeric counts
    cat_cols = shape_cols + color_cols
    num_cols = [c for c in train_feat.columns if c not in cat_cols and c not in token_cols and c != 'label']
    feature_cols = cat_cols + num_cols
    
    X_train = train_feat[feature_cols]
    y_train = train_feat['label']
    X_val = val_feat[feature_cols]
    y_val = val_feat['label']
    X_test = test_feat[feature_cols]
    y_test = test_feat['label']
    
    # Preprocessing: one-hot encode categorical, pass through numeric
    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(handle_unknown='ignore'), cat_cols),
            ('num', 'passthrough', num_cols)
        ])
    
    model = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', RandomForestClassifier(random_state=42, n_estimators=200, max_depth=10))
    ])
    
    model.fit(X_train, y_train)
    y_val_pred = model.predict(X_val)
    val_acc = accuracy_score(y_val, y_val_pred)
    print(f'Validation accuracy: {val_acc:.4f}')
    
    # Tune hyperparameters quickly
    best_acc = val_acc
    best_params = {}
    for n_est in [100, 200]:
        for max_depth in [5, 10, 20]:
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
    print(f'Best validation accuracy: {best_acc:.4f}')
    
    # Retrain on train+val
    X_trainval = pd.concat([X_train, X_val], axis=0)
    y_trainval = pd.concat([y_train, y_val], axis=0)
    final_model = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', RandomForestClassifier(random_state=42, **best_params))
    ])
    final_model.fit(X_trainval, y_trainval)
    
    y_test_pred = final_model.predict(X_test)
    test_acc = accuracy_score(y_test, y_test_pred)
    sota = registry[code]['sota_accuracy']
    print(f'Test accuracy: {test_acc:.4f}')
    print(f'SOTA accuracy: {sota:.1f}%')
    print(f'Difference (ours - SOTA): {(test_acc*100 - sota):.2f}%')
    
    vocab_size = train[token_cols[0]].nunique()
    results.append({
        'benchmark': code,
        'test_accuracy': test_acc,
        'sota_accuracy': sota,
        'difference': test_acc*100 - sota,
        'sequence_length': len(token_cols),
        'vocab_size': vocab_size
    })

# Save results
df_results = pd.DataFrame(results)
df_results.to_csv('../outputs/shape_color_results.csv', index=False)
print('\n=== Summary ===')
print(df_results.to_string(index=False))