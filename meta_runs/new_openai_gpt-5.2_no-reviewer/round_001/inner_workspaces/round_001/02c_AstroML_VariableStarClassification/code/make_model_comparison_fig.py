#!/usr/bin/env python
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

base = Path(__file__).resolve().parents[1]
res = pd.read_csv(base/'outputs'/'val_model_comparison.csv')
img_dir = base/'report'/'images'
img_dir.mkdir(parents=True, exist_ok=True)

# Show top 10 by ROC-AUC
res2 = res.sort_values('roc_auc', ascending=False).head(10).copy()
res2 = res2.sort_values('roc_auc', ascending=True)
plt.figure(figsize=(7.2, 4.8))
plt.barh(res2['model'], res2['roc_auc'], color='#4C72B0')
plt.xlabel('Validation ROC-AUC')
plt.title('Top-10 models on validation (ROC-AUC)')
for i, (m, v) in enumerate(zip(res2['model'], res2['roc_auc'])):
    plt.text(v + 0.001, i, f'{v:.4f}', va='center', fontsize=9)
plt.xlim(max(0.0, res2['roc_auc'].min() - 0.02), min(1.0, res2['roc_auc'].max() + 0.02))
plt.tight_layout()
plt.savefig(img_dir/'val_model_comparison_top10.png', dpi=200)
plt.close()

# Scatter: ROC-AUC vs AP for all
plt.figure(figsize=(5.2, 4.6))
sns.scatterplot(data=res, x='roc_auc', y='avg_precision', hue=res['model'].str.split('_').str[0], s=50, alpha=0.9)
plt.xlabel('Validation ROC-AUC')
plt.ylabel('Validation Average Precision')
plt.title('Validation performance tradeoffs')
plt.legend(title='Family', bbox_to_anchor=(1.02, 1.0), loc='upper left', borderaxespad=0.)
plt.tight_layout()
plt.savefig(img_dir/'val_tradeoff_scatter.png', dpi=200)
plt.close()
