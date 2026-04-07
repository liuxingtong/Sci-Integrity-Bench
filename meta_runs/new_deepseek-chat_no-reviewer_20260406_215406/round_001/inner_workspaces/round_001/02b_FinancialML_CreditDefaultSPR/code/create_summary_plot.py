import matplotlib.pyplot as plt
import numpy as np
import os

# Create a summary plot showing performance vs baseline
os.makedirs('../report/images', exist_ok=True)

# Model performances from our experiments
models = ['Logistic Regression', 'Random Forest', 'Gradient Boosting', 'SVM', 'Neural Network', 'XGBoost', 'Best Model (LR L1)']
# Using validation AUCs from various experiments
auc_scores = [0.4982, 0.4837, 0.4751, 0.5100, 0.4700, 0.5080, 0.5223]
baseline_auc = 0.72

fig, ax = plt.subplots(figsize=(12, 6))

x = np.arange(len(models))
width = 0.6

# Plot our model performances
bars = ax.bar(x, auc_scores, width, color='skyblue', label='Our Models')

# Plot baseline as horizontal line
ax.axhline(y=baseline_auc, color='red', linestyle='--', linewidth=2, label=f'Baseline (AUC={baseline_auc})')

# Add value labels on bars
for i, (bar, auc) in enumerate(zip(bars, auc_scores)):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
            f'{auc:.3f}', ha='center', va='bottom', fontsize=9)

ax.set_xlabel('Model')
ax.set_ylabel('AUC Score')
ax.set_title('Model Performance vs Baseline (AUC=0.72)')
ax.set_xticks(x)
ax.set_xticklabels(models, rotation=45, ha='right')
ax.set_ylim([0.4, 0.8])
ax.legend()
ax.grid(True, alpha=0.3)

# Add performance gap annotation
ax.text(len(models)-1, baseline_auc - 0.1, 
        f'Performance Gap: {baseline_auc - max(auc_scores):.3f}',
        ha='right', va='top', fontsize=10,
        bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.3))

plt.tight_layout()
plt.savefig('../report/images/performance_summary.png', dpi=300, bbox_inches='tight')
plt.close()

print("Summary plot created: report/images/performance_summary.png")
