from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def main():
    out_root = Path('outputs')
    exp_root = out_root / 'experiments'
    fig_dir = Path('report') / 'images'
    fig_dir.mkdir(parents=True, exist_ok=True)

    res_path = out_root / 'summary_results.csv'
    df = pd.read_csv(res_path)

    # Figure: dataset sizes
    size_long = df.melt(id_vars=['code'], value_vars=['train_size','val_size','test_size'], var_name='split', value_name='n')
    plt.figure(figsize=(8,4))
    sns.barplot(data=size_long, x='code', y='n', hue='split')
    plt.title('Dataset sizes for selected benchmarks')
    plt.ylabel('Number of pairs')
    plt.tight_layout()
    plt.savefig(fig_dir / 'dataset_sizes.png', dpi=200)
    plt.close()

    # Figure: test scores
    plt.figure(figsize=(7,4))
    order = df.sort_values('test_chrfpp', ascending=False)['code']
    sns.barplot(data=df, x='code', y='test_chrfpp', order=order)
    plt.title('Test chrF++ by benchmark (higher is better)')
    plt.ylabel('chrF++')
    plt.ylim(0, 100)
    plt.tight_layout()
    plt.savefig(fig_dir / 'test_chrfpp.png', dpi=200)
    plt.close()

    # Figure: exact match rate (auxiliary diagnostic)
    err_path = out_root / 'error_summary.csv'
    if err_path.exists():
        err = pd.read_csv(err_path)
        tmp = df.merge(err, on='code', how='left')
        plt.figure(figsize=(7,4))
        sns.scatterplot(data=tmp, x='test_chrfpp', y='exact_match_rate', hue='code', s=80)
        plt.title('Diagnostic: chrF++ vs exact match rate')
        plt.xlabel('Test chrF++')
        plt.ylabel('Exact match rate')
        plt.ylim(0, 1)
        plt.tight_layout()
        plt.savefig(fig_dir / 'chrf_vs_exact.png', dpi=200)
        plt.close()

    # Figure: learning curves (val chrF++ vs epoch)
    logs = []
    for code in df.code.tolist():
        log_path = exp_root / code / 'train_log.jsonl'
        if not log_path.exists():
            continue
        for line in log_path.read_text(encoding='utf-8').splitlines():
            logs.append(json.loads(line))
    log_df = pd.DataFrame(logs)

    plt.figure(figsize=(8,4.5))
    sns.lineplot(data=log_df, x='epoch', y='val_chrfpp', hue='code', marker='o')
    plt.title('Validation chrF++ during training')
    plt.ylabel('chrF++')
    plt.ylim(0, 100)
    plt.tight_layout()
    plt.savefig(fig_dir / 'learning_curves.png', dpi=200)
    plt.close()


if __name__ == '__main__':
    sns.set_style('whitegrid')
    main()
