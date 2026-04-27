from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style='whitegrid')

inp = Path('outputs/top_features.csv')
if not inp.exists():
    raise SystemExit('missing outputs/top_features.csv')

df = pd.read_csv(inp)
# Take top 20 per direction by absolute coefficient magnitude
pos = df[df['direction']=='pos'].nlargest(20, 'coef').copy()
neg = df[df['direction']=='neg'].nsmallest(20, 'coef').copy()
plot_df = pd.concat([pos, neg], axis=0)
plot_df['feature'] = plot_df['feature'].astype(str)
plot_df = plot_df.sort_values('coef')

plt.figure(figsize=(10, 8))
sns.barplot(data=plot_df, y='feature', x='coef', hue='direction', dodge=False, palette={'pos':'#d62728','neg':'#1f77b4'})
plt.axvline(0, color='black', linewidth=1)
plt.title('Most influential n-grams (logistic regression coefficients)')
plt.xlabel('Coefficient (positive increases default probability)')
plt.ylabel('n-gram')
plt.legend(title='direction', loc='lower right')
plt.tight_layout()
plt.savefig('report/images/top_features.png', dpi=200)
