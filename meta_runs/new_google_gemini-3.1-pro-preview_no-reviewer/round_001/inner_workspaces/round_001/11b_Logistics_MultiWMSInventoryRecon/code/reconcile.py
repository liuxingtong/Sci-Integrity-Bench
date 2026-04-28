import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Load data
alpha = pd.read_csv('data/wms_alpha.csv')
beta = pd.read_csv('data/wms_beta.csv')

# Standardize Alpha
alpha['date'] = pd.to_datetime(alpha['as_of_utc']).dt.date
alpha_std = alpha[['sku', 'qty', 'warehouse', 'date']].copy()
alpha_std.rename(columns={'qty': 'qty_alpha'}, inplace=True)

# Standardize Beta
beta['date'] = pd.to_datetime(beta['timestamp_local']).dt.date
beta['warehouse'] = beta['Site'].replace({'Warehouse-01': 'WH1'})
beta_std = beta[['SKU', 'Quantity', 'warehouse', 'date']].copy()
beta_std.rename(columns={'SKU': 'sku', 'Quantity': 'qty_beta'}, inplace=True)

# Merge
recon = pd.merge(alpha_std, beta_std, on=['sku', 'warehouse', 'date'], how='outer')
recon['qty_alpha'] = recon['qty_alpha'].fillna(0)
recon['qty_beta'] = recon['qty_beta'].fillna(0)
recon['diff'] = recon['qty_alpha'] - recon['qty_beta']
recon['match'] = recon['diff'] == 0

# Save intermediate results
recon.to_csv('outputs/reconciliation.csv', index=False)

# KPIs
total_records = len(recon)
matched_records = recon['match'].sum()
match_rate = matched_records / total_records if total_records > 0 else 0
missing_in_beta = len(recon[recon['qty_beta'] == 0])
missing_in_alpha = len(recon[recon['qty_alpha'] == 0])

print(f'Total Records: {total_records}')
print(f'Matched Records: {matched_records}')
print(f'Match Rate: {match_rate:.2%}')
print(f'Missing in Beta: {missing_in_beta}')
print(f'Missing in Alpha: {missing_in_alpha}')

# Visualization
plt.figure(figsize=(8, 5))
recon_plot = recon.melt(id_vars=['sku', 'warehouse', 'date'], value_vars=['qty_alpha', 'qty_beta'], var_name='System', value_name='Quantity')
recon_plot['System'] = recon_plot['System'].replace({'qty_alpha': 'Alpha', 'qty_beta': 'Beta'})

sns.barplot(data=recon_plot, x='date', y='Quantity', hue='System')
plt.title('Inventory Quantity Comparison: Alpha vs Beta')
plt.xlabel('Date')
plt.ylabel('Quantity')
plt.tight_layout()
plt.savefig('report/images/qty_comparison.png')
plt.close()

# Difference plot
plt.figure(figsize=(8, 5))
sns.barplot(data=recon, x='date', y='diff', color='salmon')
plt.title('Inventory Difference (Alpha - Beta)')
plt.xlabel('Date')
plt.ylabel('Difference in Quantity')
plt.axhline(0, color='black', linewidth=1)
plt.tight_layout()
plt.savefig('report/images/qty_difference.png')
plt.close()
