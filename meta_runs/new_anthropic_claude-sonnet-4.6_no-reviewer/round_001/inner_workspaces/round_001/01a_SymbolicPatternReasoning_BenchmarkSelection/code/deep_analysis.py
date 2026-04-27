import pandas as pd
import numpy as np
import json
from sklearn.preprocessing import OrdinalEncoder
from sklearn.metrics import accuracy_score
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier

# Analyze token structure: tokens appear to be 2-char codes
# First char: shape (C=Circle, S=Square, T=Triangle, D=Diamond)
# Second char: color (r=red, g=green, b=blue, y=yellow)

for code in ['OQMEA', 'ILULR', 'RHHQD', 'FDLOT']:
    df = pd.read_csv('data/{}_train.csv'.format(code))
    token_cols = [c for c in df.columns if c.startswith('token_')]
    print('\n=== {} ==='.format(code))
    
    # Decode tokens into shape and color features
    def decode_tokens(df, token_cols):
        rows = []
        for _, row in df.iterrows():
            feat = {}
            for col in token_cols:
                tok = row[col]
                feat[col + '_shape'] = tok[0] if len(tok) >= 1 else '?'
                feat[col + '_color'] = tok[1] if len(tok) >= 2 else '?'
            feat['label'] = row['label']
            rows.append(feat)
        return pd.DataFrame(rows)
    
    decoded = decode_tokens(df, token_cols)
    shape_cols = [c for c in decoded.columns if c.endswith('_shape')]
    color_cols = [c for c in decoded.columns if c.endswith('_color')]
    
    print('Unique shapes:', sorted(decoded[shape_cols[0]].unique()))
    print('Unique colors:', sorted(decoded[color_cols[0]].unique()))
    
    # Count shapes and colors per row
    def count_feature(df_dec, cols, feature_name):
        counts = {}
        for val in df_dec[cols[0]].unique():
            cnt = df_dec[cols].apply(lambda row: (row == val).sum(), axis=1)
            counts['count_' + feature_name + '_' + val] = cnt
        return pd.DataFrame(counts)
    
    shape_counts = count_feature(decoded, shape_cols, 'shape')
    color_counts = count_feature(decoded, color_cols, 'color')
    
    # Test if count-based features help
    from sklearn.preprocessing import LabelEncoder
    X_count = pd.concat([shape_counts, color_counts], axis=1)
    y = df['label'].values
    
    from sklearn.model_selection import cross_val_score
    dt = DecisionTreeClassifier(max_depth=None, random_state=42)
    scores = cross_val_score(dt, X_count, y, cv=5, scoring='accuracy')
    print('Count-based DT CV accuracy: {:.4f} +/- {:.4f}'.format(scores.mean(), scores.std()))
    
    rf = RandomForestClassifier(n_estimators=100, random_state=42)
    scores_rf = cross_val_score(rf, X_count, y, cv=5, scoring='accuracy')
    print('Count-based RF CV accuracy: {:.4f} +/- {:.4f}'.format(scores_rf.mean(), scores_rf.std()))
    
    # Also test on val/test
    val_df  = pd.read_csv('data/{}_val.csv'.format(code))
    test_df = pd.read_csv('data/{}_test.csv'.format(code))
    
    def make_count_features(df, token_cols):
        decoded = []
        for _, row in df.iterrows():
            feat = {}
            for col in token_cols:
                tok = row[col]
                feat[col + '_shape'] = tok[0] if len(tok) >= 1 else '?'
                feat[col + '_color'] = tok[1] if len(tok) >= 2 else '?'
            decoded.append(feat)
        dec_df = pd.DataFrame(decoded)
        shape_cols_l = [c for c in dec_df.columns if c.endswith('_shape')]
        color_cols_l = [c for c in dec_df.columns if c.endswith('_color')]
        all_shapes = sorted(dec_df[shape_cols_l[0]].unique())
        all_colors = sorted(dec_df[color_cols_l[0]].unique())
        result = {}
        for s in all_shapes:
            result['cnt_shape_' + s] = dec_df[shape_cols_l].apply(lambda r: (r == s).sum(), axis=1)
        for c in all_colors:
            result['cnt_color_' + c] = dec_df[color_cols_l].apply(lambda r: (r == c).sum(), axis=1)
        return pd.DataFrame(result)
    
    X_tr = make_count_features(df, token_cols)
    X_vl = make_count_features(val_df, token_cols)
    X_te = make_count_features(test_df, token_cols)
    
    # Align columns
    for col in X_tr.columns:
        if col not in X_vl.columns: X_vl[col] = 0
        if col not in X_te.columns: X_te[col] = 0
    X_vl = X_vl[X_tr.columns]
    X_te = X_te[X_tr.columns]
    
    y_tr = df['label'].values
    y_vl = val_df['label'].values
    y_te = test_df['label'].values
    
    for ModelClass, name, kwargs in [
        (DecisionTreeClassifier, 'DT_None', {'max_depth': None, 'random_state': 42}),
        (RandomForestClassifier, 'RF_100',  {'n_estimators': 100, 'random_state': 42}),
    ]:
        m = ModelClass(**kwargs)
        m.fit(X_tr, y_tr)
        val_acc  = accuracy_score(y_vl, m.predict(X_vl))
        test_acc = accuracy_score(y_te, m.predict(X_te))
        print('  {} count-feats: val={:.4f}  test={:.4f}'.format(name, val_acc, test_acc))
