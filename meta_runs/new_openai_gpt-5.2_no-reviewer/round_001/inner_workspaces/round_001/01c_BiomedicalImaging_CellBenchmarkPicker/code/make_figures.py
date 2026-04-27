import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def main():
    out_dir = Path('outputs') / 'baselines'
    summary_path = out_dir / 'summary.json'
    if not summary_path.exists():
        raise FileNotFoundError(summary_path)

    summ = json.load(open(summary_path, 'r', encoding='utf-8'))
    results = summ['results']
    res_df = pd.DataFrame([
        {
            'dataset_id': r['dataset_id'],
            'H': r['info']['H'],
            'W': r['info']['W'],
            'C': r['info']['C'],
            'train_n': r['train']['n'],
            'val_n': r['val']['n'],
            'test_n': r['test']['n'],
            'val_dice': r['val']['dice'],
            'test_dice': r['test']['dice'],
            'epochs_ran': r['epochs_ran'],
            'device': r.get('device', ''),
        }
        for r in results
    ])

    reg = json.load(open('data/cell_benchmark_registry.json', 'r', encoding='utf-8'))
    reg_df = pd.DataFrame(reg)
    merged = res_df.merge(reg_df, on='dataset_id', how='left')

    img_dir = Path('report') / 'images'
    img_dir.mkdir(parents=True, exist_ok=True)

    # Figure 1: dataset metadata (train_patches vs positive_pixel_rate), highlight picks
    plt.figure(figsize=(7.0, 5.0))
    sns.scatterplot(
        data=reg_df,
        x='train_patches',
        y='positive_pixel_rate',
        size='published_dice_sota',
        sizes=(30, 200),
        alpha=0.6,
        legend=False,
        color='gray'
    )
    sns.scatterplot(
        data=merged,
        x='train_patches',
        y='positive_pixel_rate',
        s=140,
        color='#d62728'
    )
    for _, r in merged.iterrows():
        plt.text(r['train_patches'], r['positive_pixel_rate'], r['dataset_id'], fontsize=9,
                 ha='left', va='bottom')
    plt.xscale('log')
    plt.xlabel('Train patches (log scale)')
    plt.ylabel('Positive pixel rate')
    plt.title('Registry overview and selected datasets')
    plt.tight_layout()
    plt.savefig(img_dir / 'fig1_dataset_selection.png', dpi=200)
    plt.close()

    # Figure 2: hold-out test Dice vs published SOTA Dice
    plot_df = merged[['dataset_id', 'published_dice_sota', 'test_dice']].melt(
        id_vars='dataset_id', var_name='metric', value_name='dice'
    )
    plt.figure(figsize=(7.2, 4.2))
    sns.barplot(data=plot_df, x='dataset_id', y='dice', hue='metric')
    plt.ylim(0, 1)
    plt.ylabel('Dice')
    plt.xlabel('Dataset')
    plt.title('Baseline hold-out Dice vs reported published SOTA')
    plt.legend(title='')
    plt.tight_layout()
    plt.savefig(img_dir / 'fig2_test_vs_sota.png', dpi=200)
    plt.close()

    # Figure 3: test Dice vs positive pixel rate
    plt.figure(figsize=(6.5, 4.8))
    sns.regplot(data=merged, x='positive_pixel_rate', y='test_dice', scatter=True)
    for _, r in merged.iterrows():
        plt.text(r['positive_pixel_rate'], r['test_dice'], r['dataset_id'], fontsize=9,
                 ha='left', va='bottom')
    plt.ylim(0, 1)
    plt.xlabel('Positive pixel rate')
    plt.ylabel('Test Dice (baseline)')
    plt.title('Baseline performance vs class imbalance (selected datasets)')
    plt.tight_layout()
    plt.savefig(img_dir / 'fig3_dice_vs_posrate.png', dpi=200)
    plt.close()

    # Figure 4: training curves (val Dice) for each dataset
    plt.figure(figsize=(7.2, 4.6))
    for did in merged['dataset_id']:
        hist_path = out_dir / f'{did}_history.json'
        hist = pd.DataFrame(json.load(open(hist_path, 'r', encoding='utf-8')))
        plt.plot(hist['epoch'], hist['val_dice'], label=did)
    plt.xlabel('Epoch')
    plt.ylabel('Val Dice')
    plt.ylim(0, 1)
    plt.title('Validation Dice over training')
    plt.legend(ncol=2, fontsize=9)
    plt.tight_layout()
    plt.savefig(img_dir / 'fig4_training_curves.png', dpi=200)
    plt.close()

    # Save merged table for report
    merged.to_csv(out_dir / 'merged_results.csv', index=False)


if __name__ == '__main__':
    main()
