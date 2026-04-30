from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns


def lift_curve(y_true, y_score, fracs=None):
    y_true = np.asarray(y_true).astype(int)
    y_score = np.asarray(y_score).astype(float)
    n = len(y_true)
    order = np.argsort(-y_score)
    y_sorted = y_true[order]
    base = y_true.mean()
    if fracs is None:
        fracs = np.linspace(0.01, 0.5, 50)
    lifts = []
    for f in fracs:
        k = max(1, int(np.floor(f * n)))
        prec = y_sorted[:k].mean()
        lift = prec / base if base > 0 else np.nan
        lifts.append(lift)
    return fracs, np.array(lifts), base


def main():
    Path('report/images').mkdir(parents=True, exist_ok=True)

    # Model comparison bar plot (val)
    comp = pd.read_csv('outputs/val_model_comparison.csv')
    comp_m = comp.melt(id_vars=['model'], value_vars=['spr', 'roc_auc', 'pr_auc', 'brier'], var_name='metric', value_name='value')
    plt.figure(figsize=(8, 3.8))
    sns.barplot(data=comp_m[comp_m['metric'].isin(['spr','roc_auc','pr_auc'])], x='metric', y='value', hue='model')
    plt.title('Validation metrics by model')
    plt.tight_layout()
    plt.savefig('report/images/val_model_comparison.png', dpi=200)
    plt.close()

    # Lift curve on test using saved predictions
    pred = pd.read_csv('outputs/test_predictions.csv')
    y_true = pred['label'].values
    y_score = pred['pred_prob'].values
    fracs, lifts, base = lift_curve(y_true, y_score)

    plt.figure(figsize=(5.5, 4))
    plt.plot(fracs*100, lifts, color='#4C72B0')
    plt.axhline(1.0, linestyle='--', color='gray', linewidth=1)
    plt.xlabel('Top fraction selected (%)')
    plt.ylabel('Lift = precision@top / base rate')
    plt.title('Lift curve (test)')
    plt.tight_layout()
    plt.savefig('report/images/lift_curve_test.png', dpi=200)
    plt.close()

    # Score distribution by class
    plt.figure(figsize=(6, 3.5))
    df = pd.DataFrame({'y': y_true, 'p': y_score})
    sns.kdeplot(data=df, x='p', hue='y', common_norm=False)
    plt.title('Predicted probability distribution (test)')
    plt.tight_layout()
    plt.savefig('report/images/pred_dist_test.png', dpi=200)
    plt.close()


if __name__ == '__main__':
    main()
