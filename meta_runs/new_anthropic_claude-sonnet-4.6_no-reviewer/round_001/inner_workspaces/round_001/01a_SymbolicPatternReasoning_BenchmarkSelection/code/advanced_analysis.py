import pandas as pd
import numpy as np
import json
from sklearn.preprocessing import OrdinalEncoder, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, ExtraTreesClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score
from itertools import combinations

SEED = 42
np.random.seed(SEED)

with open('data/benchmark_registry.json') as f:
    registry = json.load(f)

SELECTED = ['OQMEA', 'ILULR', 'RHHQD', 'FDLOT']

def make_rich_features(df, token_cols, fit_encoders=None):
    """Create rich feature set: ordinal + shape/color + bigrams + trigrams + counts."""
    n = len(token_cols)
    features = {}
    
    # 1. Ordinal encoding of raw tokens
    for i, col in enumerate(token_cols):
        features['ord_' + col] = df[col].values
    
    # 2. Shape and color features
    for col in token_cols:
        features['shape_' + col] = df[col].apply(lambda x: x[0]).values
        features['color_' + col] = df[col].apply(lambda x: x[1] if len(x) > 1 else '?').values
    
    # 3. Bigram features (adjacent pairs)
    for i in range(n - 1):
        c1, c2 = token_cols[i], token_cols[i+1]
        features['bigram_{}_{}'.format(i, i+1)] = (df[c1] + '_' + df[c2]).values
        features['shape_bigram_{}_{}'.format(i, i+1)] = (
            df[c1].apply(lambda x: x[0]) + '_' + df[c2].apply(lambda x: x[0])).values
        features['color_bigram_{}_{}'.format(i, i+1)] = (
            df[c1].apply(lambda x: x[1] if len(x)>1 else '?') + '_' + 
            df[c2].apply(lambda x: x[1] if len(x)>1 else '?')).values
    
    # 4. Trigram features
    for i in range(n - 2):
        c1, c2, c3 = token_cols[i], token_cols[i+1], token_cols[i+2]
        features['trigram_{}_{}_{}'.format(i,i+1,i+2)] = (
            df[c1] + '_' + df[c2] + '_' + df[c3]).values
    
    # 5. Count features
    shape_cols = ['shape_' + c for c in token_cols]
    color_cols = ['color_' + c for c in token_cols]
    shape_df = pd.DataFrame({k: features[k] for k in shape_cols})
    color_df = pd.DataFrame({k: features[k] for k in color_cols})
    
    for s in sorted(shape_df[shape_cols[0]].unique()):
        features['cnt_shape_' + s] = shape_df.apply(lambda r: (r == s).sum(), axis=1).values
    for c in sorted(color_df[color_cols[0]].unique()):
        features['cnt_color_' + c] = color_df.apply(lambda r: (r == c).sum(), axis=1).values
    
    # 6. Position of first occurrence of each shape/color
    for s in sorted(shape_df[shape_cols[0]].unique()):
        pos = []
        for _, row in shape_df.iterrows():
            found = -1
            for i, col in enumerate(shape_cols):
                if row[col] == s:
                    found = i
                    break
            pos.append(found)
        features['first_pos_shape_' + s] = np.array(pos)
    
    # 7. Same-token consecutive pairs
    for i in range(n - 1):
        c1, c2 = token_cols[i], token_cols[i+1]
        features['same_token_{}_{}'.format(i, i+1)] = (df[c1] == df[c2]).astype(int).values
        features['same_shape_{}_{}'.format(i, i+1)] = (
            df[c1].apply(lambda x: x[0]) == df[c2].apply(lambda x: x[0])).astype(int).values
        features['same_color_{}_{}'.format(i, i+1)] = (
            df[c1].apply(lambda x: x[1] if len(x)>1 else '?') == 
            df[c2].apply(lambda x: x[1] if len(x)>1 else '?')).astype(int).values
    
    feat_df = pd.DataFrame(features)
    
    # Encode string columns
    str_cols = feat_df.select_dtypes(include='object').columns.tolist()
    
    if fit_encoders is None:
        encoders = {}
        for col in str_cols:
            le = LabelEncoder()
            feat_df[col] = le.fit_transform(feat_df[col].astype(str))
            encoders[col] = le
        return feat_df.values, encoders
    else:
        for col in str_cols:
            if col in fit_encoders:
                le = fit_encoders[col]
                feat_df[col] = feat_df[col].astype(str).apply(
                    lambda x: le.transform([x])[0] if x in le.classes_ else -1)
            else:
                feat_df[col] = -1
        return feat_df.values, fit_encoders

results_advanced = {}

for code in SELECTED:
    print('\n=== {} (SOTA: {}%) ==='.format(code, registry[code]['sota_accuracy']))
    train_df = pd.read_csv('data/{}_train.csv'.format(code))
    val_df   = pd.read_csv('data/{}_val.csv'.format(code))
    test_df  = pd.read_csv('data/{}_test.csv'.format(code))
    
    token_cols = [c for c in train_df.columns if c.startswith('token_')]
    
    X_train, encoders = make_rich_features(train_df, token_cols)
    X_val,   _        = make_rich_features(val_df,   token_cols, encoders)
    X_test,  _        = make_rich_features(test_df,  token_cols, encoders)
    
    y_train = train_df['label'].values
    y_val   = val_df['label'].values
    y_test  = test_df['label'].values
    
    print('  Feature dim: {}'.format(X_train.shape[1]))
    
    candidates = {
        'DT_None':    DecisionTreeClassifier(max_depth=None, random_state=SEED),
        'DT_d10':     DecisionTreeClassifier(max_depth=10, random_state=SEED),
        'RF_100':     RandomForestClassifier(n_estimators=100, random_state=SEED),
        'RF_200':     RandomForestClassifier(n_estimators=200, random_state=SEED),
        'ET_100':     ExtraTreesClassifier(n_estimators=100, random_state=SEED),
        'GBT_100_d3': GradientBoostingClassifier(n_estimators=100, max_depth=3, random_state=SEED),
        'GBT_100_d5': GradientBoostingClassifier(n_estimators=100, max_depth=5, random_state=SEED),
        'GBT_200_d3': GradientBoostingClassifier(n_estimators=200, max_depth=3, random_state=SEED),
    }
    
    val_scores = {}
    for name, model in candidates.items():
        model.fit(X_train, y_train)
        val_acc = accuracy_score(y_val, model.predict(X_val))
        val_scores[name] = (model, val_acc)
        print('    {:20s}  val_acc={:.4f}'.format(name, val_acc))
    
    best_name = max(val_scores, key=lambda k: val_scores[k][1])
    best_model, best_val_acc = val_scores[best_name]
    test_acc = accuracy_score(y_test, best_model.predict(X_test)) * 100
    sota = registry[code]['sota_accuracy']
    delta = test_acc - sota
    
    print('  Best: {}  val={:.4f}  test={:.2f}%  SOTA={}%  delta={:+.2f}%'.format(
        best_name, best_val_acc, test_acc, sota, delta))
    
    results_advanced[code] = {
        'sota': sota, 'test_acc': test_acc, 'delta': delta,
        'best_model': best_name, 'best_val_acc': best_val_acc * 100,
        'seq_len': len(token_cols),
        'val_scores': {k: v[1]*100 for k, v in val_scores.items()}
    }

with open('outputs/results_advanced.json', 'w') as f:
    json.dump(results_advanced, f, indent=2)

print('\n=== ADVANCED SUMMARY ===')
print('{:8s} {:8s} {:8s} {:8s} {:8s} {:25s}'.format('Code','SeqLen','SOTA%','Test%','Delta','BestModel'))
print('-'*70)
for code in SELECTED:
    r = results_advanced[code]
    print('{:8s} {:8d} {:8.1f} {:8.2f} {:+8.2f} {:25s}'.format(
        code, r['seq_len'], r['sota'], r['test_acc'], r['delta'], r['best_model']))
