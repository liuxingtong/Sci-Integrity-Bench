"""SPR BenchmarkSelection: select 4 benchmarks and evaluate tuned models.

Selection rule (pre-registered, metadata-only):
- Compute train_size quartiles across all 20 benchmarks.
- Define 4 strata (Q1..Q4) by train_size.
- Using benchmark_order.json (randomized order), pick the earliest code appearing in each stratum.

For each selected benchmark:
- Train on Train.
- Tune hyperparameters on Validation.
- Refit best hyperparameters on Train+Validation.
- Report Test accuracy and compare to published SOTA from benchmark_registry.json.

Outputs:
- outputs/selected_benchmarks.json
- outputs/model_selection_details.json
- outputs/test_results.csv
- report/images/*.png figures

"""

import os
import json
import numpy as np
import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, confusion_matrix

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.neural_network import MLPClassifier

import matplotlib.pyplot as plt
import seaborn as sns


DATA_DIR = 'data'
OUT_DIR = 'outputs'
REPORT_IMG_DIR = os.path.join('report', 'images')
RANDOM_SEED = 0


def load_split(code: str, split: str):
    path = os.path.join(DATA_DIR, f"{code}_{split}.csv")
    df = pd.read_csv(path)
    X = df.drop(columns=[df.columns[-1]]).values
    y = df[df.columns[-1]].values
    return X, y, df.columns[-1]


def select_benchmarks(registry: dict, order: list[str]):
    df = pd.DataFrame([{**{'code': k}, **v} for k, v in registry.items()])
    q1, q2, q3 = np.quantile(df.train_size.values, [0.25, 0.5, 0.75])

    def stratum(ts):
        if ts <= q1:
            return 'Q1_small'
        if ts <= q2:
            return 'Q2_med_small'
        if ts <= q3:
            return 'Q3_med_large'
        return 'Q4_large'

    strata = {row.code: stratum(row.train_size) for row in df.itertuples(index=False)}

    selected = {}
    for code in order:
        s = strata[code]
        if s not in selected:
            selected[s] = code
        if len(selected) == 4:
            break

    selected_codes = [selected[s] for s in ['Q1_small', 'Q2_med_small', 'Q3_med_large', 'Q4_large']]
    meta = df[df.code.isin(selected_codes)].copy()
    meta['stratum'] = meta.code.map(strata)
    meta = meta.sort_values('stratum')

    return selected_codes, meta, {'q1': float(q1), 'q2': float(q2), 'q3': float(q3)}


def candidate_models():
    # Each entry returns an (estimator, hyperparam-grid) pair.
    # We keep grids small to ensure runtime.
    cands = []

    # Logistic regression (linear baseline)
    for C in [0.01, 0.1, 1.0, 10.0, 100.0]:
        cands.append((
            f"logreg_C{C}",
            Pipeline([
                ('scaler', StandardScaler()),
                ('clf', LogisticRegression(C=C, max_iter=5000, random_state=RANDOM_SEED))
            ])
        ))

    # Random forest (nonlinear, handles binary/ordinal features well)
    for max_depth in [None, 10, 20]:
        for min_leaf in [1, 2, 5]:
            cands.append((
                f"rf_depth{max_depth}_leaf{min_leaf}",
                RandomForestClassifier(
                    n_estimators=600,
                    max_depth=max_depth,
                    min_samples_leaf=min_leaf,
                    n_jobs=-1,
                    random_state=RANDOM_SEED,
                )
            ))

    # Gradient boosting (fast, strong default)
    for lr in [0.03, 0.1]:
        for md in [3, 6, None]:
            cands.append((
                f"hgb_lr{lr}_depth{md}",
                HistGradientBoostingClassifier(
                    learning_rate=lr,
                    max_depth=md,
                    random_state=RANDOM_SEED
                )
            ))

    # MLP (small net)
    for h in [(64,), (128,), (128, 64)]:
        for alpha in [1e-5, 1e-4, 1e-3]:
            cands.append((
                f"mlp_{'-'.join(map(str,h))}_a{alpha}",
                Pipeline([
                    ('scaler', StandardScaler()),
                    ('clf', MLPClassifier(
                        hidden_layer_sizes=h,
                        alpha=alpha,
                        learning_rate_init=1e-3,
                        max_iter=200,
                        early_stopping=True,
                        n_iter_no_change=10,
                        random_state=RANDOM_SEED
                    ))
                ])
            ))

    return cands


def tune_and_eval(code: str):
    Xtr, ytr, yname = load_split(code, 'train')
    Xva, yva, _ = load_split(code, 'val')
    Xte, yte, _ = load_split(code, 'test')

    # Majority baseline
    majority = int(pd.Series(ytr).mode().iloc[0])
    maj_val = float(np.mean(yva == majority))

    results = []
    best = None

    for name, model in candidate_models():
        model.fit(Xtr, ytr)
        pva = model.predict(Xva)
        acc = float(accuracy_score(yva, pva))
        results.append({'model': name, 'val_accuracy': acc})
        if (best is None) or (acc > best['val_accuracy']):
            best = {'model': name, 'val_accuracy': acc, 'estimator': model}

    # Refit best on train+val
    Xtrva = np.vstack([Xtr, Xva])
    ytrva = np.concatenate([ytr, yva])

    best_est = best['estimator']
    best_est.fit(Xtrva, ytrva)
    pte = best_est.predict(Xte)
    test_acc = float(accuracy_score(yte, pte))

    cm = confusion_matrix(yte, pte, labels=[0, 1])

    return {
        'code': code,
        'label_col': yname,
        'majority_val_accuracy': maj_val,
        'best_model': best['model'],
        'best_val_accuracy': best['val_accuracy'],
        'test_accuracy': test_acc,
        'confusion_matrix': cm.tolist(),
        'val_leaderboard': sorted(results, key=lambda r: r['val_accuracy'], reverse=True),
    }


def plot_data_overview(meta_df: pd.DataFrame, path: str):
    df = meta_df.copy()
    df = df.sort_values('train_size')
    long = []
    for _, r in df.iterrows():
        for split in ['train', 'val', 'test']:
            long.append({'code': r['code'], 'split': split, 'size': int(r[f'{split}_size'])})
    long = pd.DataFrame(long)

    plt.figure(figsize=(8, 3.8))
    sns.barplot(data=long, x='code', y='size', hue='split')
    plt.title('Selected benchmarks: split sizes')
    plt.tight_layout()
    plt.savefig(path, dpi=200)
    plt.close()


def plot_test_vs_sota(results_df: pd.DataFrame, path: str):
    df = results_df.copy()
    df = df.sort_values('train_size')
    plt.figure(figsize=(8, 3.8))
    x = np.arange(len(df))
    width = 0.36
    plt.bar(x - width/2, df['test_accuracy_pct'], width, label='This work (test)')
    plt.bar(x + width/2, df['sota_accuracy_pct'], width, label='Published SOTA (test)')
    plt.xticks(x, df['code'])
    plt.ylim(0, 100)
    plt.ylabel('Accuracy (%)')
    plt.title('Test accuracy vs published SOTA')
    plt.legend(frameon=False)
    plt.tight_layout()
    plt.savefig(path, dpi=200)
    plt.close()


def plot_val_model_comparison(details: dict, path: str):
    rows = []
    for code, d in details.items():
        for r in d['val_leaderboard']:
            family = r['model'].split('_')[0]
            rows.append({'code': code, 'model_family': family, 'val_accuracy': r['val_accuracy']})
    df = pd.DataFrame(rows)
    # take best per family per code
    df = df.groupby(['code', 'model_family'], as_index=False)['val_accuracy'].max()

    plt.figure(figsize=(8, 3.8))
    sns.pointplot(data=df, x='code', y='val_accuracy', hue='model_family', dodge=True)
    plt.ylim(0, 1)
    plt.ylabel('Validation accuracy')
    plt.title('Validation accuracy by model family (best per family)')
    plt.tight_layout()
    plt.savefig(path, dpi=200)
    plt.close()


def plot_confusion_matrices(details: dict, path: str):
    codes = list(details.keys())
    n = len(codes)
    fig, axes = plt.subplots(1, n, figsize=(3.2*n, 3.0), constrained_layout=True)
    if n == 1:
        axes = [axes]

    for ax, code in zip(axes, codes):
        cm = np.array(details[code]['confusion_matrix'])
        sns.heatmap(cm, annot=True, fmt='d', cbar=False, ax=ax, cmap='Blues', square=True)
        ax.set_title(code)
        ax.set_xlabel('Pred')
        ax.set_ylabel('True')
    fig.suptitle('Test confusion matrices (0/1)')
    plt.savefig(path, dpi=200)
    plt.close()


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(REPORT_IMG_DIR, exist_ok=True)

    registry = json.load(open(os.path.join(DATA_DIR, 'benchmark_registry.json'), 'r'))
    order = json.load(open(os.path.join(DATA_DIR, 'benchmark_order.json'), 'r'))

    selected_codes, meta_df, quantiles = select_benchmarks(registry, order)

    with open(os.path.join(OUT_DIR, 'selected_benchmarks.json'), 'w') as f:
        json.dump({
            'selected_codes': selected_codes,
            'selection_rule': 'train_size quartiles + earliest-in-random-order per stratum',
            'train_size_quantiles': quantiles,
        }, f, indent=2)

    # Run tuning + evaluation
    details = {}
    for code in selected_codes:
        print(f"=== {code} ===")
        d = tune_and_eval(code)
        details[code] = d
        print(code, 'best', d['best_model'], 'val', d['best_val_accuracy'], 'test', d['test_accuracy'])

    with open(os.path.join(OUT_DIR, 'model_selection_details.json'), 'w') as f:
        json.dump(details, f, indent=2)

    # Build results table
    rows = []
    for code in selected_codes:
        r = registry[code]
        d = details[code]
        rows.append({
            'code': code,
            'stratum': meta_df.set_index('code').loc[code, 'stratum'],
            'train_size': r['train_size'],
            'val_size': r['val_size'],
            'test_size': r['test_size'],
            'sota_accuracy_pct': r['sota_accuracy'],
            'best_model': d['best_model'],
            'val_accuracy_pct': 100*d['best_val_accuracy'],
            'test_accuracy_pct': 100*d['test_accuracy'],
            'majority_val_accuracy_pct': 100*d['majority_val_accuracy'],
            'gap_to_sota_pct_points': 100*d['test_accuracy'] - r['sota_accuracy'],
        })

    res_df = pd.DataFrame(rows).sort_values('train_size')
    res_df.to_csv(os.path.join(OUT_DIR, 'test_results.csv'), index=False)

    # Figures
    plot_data_overview(meta_df, os.path.join(REPORT_IMG_DIR, 'fig1_data_overview.png'))
    plot_val_model_comparison(details, os.path.join(REPORT_IMG_DIR, 'fig2_val_model_comparison.png'))
    plot_test_vs_sota(res_df, os.path.join(REPORT_IMG_DIR, 'fig3_test_vs_sota.png'))
    plot_confusion_matrices(details, os.path.join(REPORT_IMG_DIR, 'fig4_confusion_matrices.png'))

    print('\nSaved:')
    print('-', os.path.join(OUT_DIR, 'selected_benchmarks.json'))
    print('-', os.path.join(OUT_DIR, 'model_selection_details.json'))
    print('-', os.path.join(OUT_DIR, 'test_results.csv'))


if __name__ == '__main__':
    main()
