import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import os

os.makedirs('report/images', exist_ok=True)

df = pd.read_csv('data/field_year_panel.csv')

fig, ax = plt.subplots(figsize=(8, 6))
ax.hist(df['yield_kg_ha'], bins=30, color='blue', alpha=0.7)
ax.set_title('Yield Distribution')
ax.set_xlabel('Yield (kg/ha)')
ax.set_ylabel('Frequency')
plt.savefig('report/images/test_plot.png', bbox_inches='tight')
plt.close()

with open('outputs/simple_plot_done.txt', 'w') as f:
    f.write('done')

print('Plot saved!')
