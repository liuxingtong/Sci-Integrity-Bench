import json, os, glob
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

DATA_DIR = os.path.join('data')


def load_split(code, split):
    path = os.path.join(DATA_DIR, f"{code}_{split}.csv")
    df = pd.read_csv(path)
    X = df.drop(columns=[df.columns[-1]]).values
    y = df[df.columns[-1]].values
    return X, y


def eval_models(code, seed=0):
    Xtr, ytr = load_split(code, 'train')
    Xva, yva = load_split(code, 'val')

    models = {}
    models['logreg'] = Pipeline([
        ('scaler', StandardScaler()),
        ('clf', LogisticRegression(max_iter=5000, n_jobs=None, random_state=seed))
    ])
    models['rf'] = RandomForestClassifier(
        n_estimators=400, max_depth=None, min_samples_leaf=1,
        random_state=seed, n_jobs=-1
    )

    out = {}
    for name, m in models.items():
        m.fit(Xtr, ytr)
        pred = m.predict(Xva)
        out[name] = float(accuracy_score(yva, pred))
    return out


def main():
    with open(os.path.join(DATA_DIR, 'benchmark_registry.json'), 'r') as f:
        reg = json.load(f)

    codes = sorted(reg.keys())
    rows = []
    for code in codes:
        scores = eval_models(code)
        rows.append({
            'code': code,
            'train_size': reg[code]['train_size'],
            'val_size': reg[code]['val_size'],
            'test_size': reg[code]['test_size'],
            'sota_accuracy_pct': reg[code]['sota_accuracy'],
            **{f'val_{k}': v for k, v in scores.items()}
        })
        print(code, scores)

    df = pd.DataFrame(rows).sort_values('sota_accuracy_pct', ascending=False)
    os.makedirs('outputs', exist_ok=True)
    df.to_csv('outputs/scan_val_baselines.csv', index=False)
    print('\nSaved outputs/scan_val_baselines.csv')


if __name__ == '__main__':
    main()
