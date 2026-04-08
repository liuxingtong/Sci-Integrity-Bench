import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Read data
data_path = '../data/field_year_panel.csv'
df = pd.read_csv(data_path)

# Create summary figure
fig, axes = plt.subplots(2, 2, figsize=(14, 12))
fig.suptitle('Summary of Key Findings: Irrigation Program Evaluation', fontsize=16, fontweight='bold')

# 1. Yield distribution by quota enforcement tercile
quota_bins = pd.qcut(df['groundwater_quota_enforcement'], q=3, labels=['Low', 'Medium', 'High'])
df['quota_category'] = quota_bins

axes[0, 0].boxplot([df[df['quota_category'] == 'Low']['yield_t_ha'],
                    df[df['quota_category'] == 'Medium']['yield_t_ha'],
                    df[df['quota_category'] == 'High']['yield_t_ha']],
                   labels=['Low', 'Medium', 'High'])
axes[0, 0].set_xlabel('Groundwater Quota Enforcement Level')
axes[0, 0].set_ylabel('Yield (t/ha)')
axes[0, 0].set_title('Yield Increases with Quota Enforcement')
axes[0, 0].grid(True, alpha=0.3)

# Add mean lines
for i, category in enumerate(['Low', 'Medium', 'High']):
    mean_yield = df[df['quota_category'] == category]['yield_t_ha'].mean()
    axes[0, 0].axhline(y=mean_yield, xmin=i/3+0.1, xmax=(i+1)/3-0.1, 
                      color='red', linestyle='--', alpha=0.7)

# 2. Marginal effects visualization
# Simulate yield response to irrigation at different quota levels
irrigation_range = np.linspace(df['irrigation_m3'].min(), df['irrigation_m3'].max(), 50)
quota_levels = [0.2, 0.5, 0.8]  # Low, medium, high

# Simplified model based on regression results: yield = 2.3 + 0.002*irrigation + 1.44*quota
for quota in quota_levels:
    predicted_yield = 2.3 + 0.002 * irrigation_range + 1.44 * quota
    axes[0, 1].plot(irrigation_range, predicted_yield, 
                   label=f'Quota = {quota}', linewidth=2.5)

axes[0, 1].set_xlabel('Irrigation (m³)')
axes[0, 1].set_ylabel('Predicted Yield (t/ha)')
axes[0, 1].set_title('Irrigation Response Varies by Quota Level')
axes[0, 1].legend()
axes[0, 1].grid(True, alpha=0.3)

# 3. Policy simulation bar chart
current_yield = 4.291
new_yield = 4.471
yield_change = new_yield - current_yield
percent_change = (yield_change / current_yield) * 100

categories = ['Current', 'With 25% Increase\nin Quota Enforcement']
yields = [current_yield, new_yield]

bars = axes[1, 0].bar(categories, yields, color=['skyblue', 'lightgreen'])
axes[1, 0].set_ylabel('Average Yield (t/ha)')
axes[1, 0].set_title(f'Policy Simulation: {percent_change:.1f}% Yield Increase')
axes[1, 0].grid(True, alpha=0.3, axis='y')

# Add value labels on bars
for bar, yield_val in zip(bars, yields):
    height = bar.get_height()
    axes[1, 0].text(bar.get_x() + bar.get_width()/2., height + 0.02,
                   f'{yield_val:.3f}', ha='center', va='bottom')

# Add change arrow
axes[1, 0].annotate(f'+{yield_change:.3f} t/ha', 
                   xy=(0.5, (current_yield + new_yield)/2), 
                   xytext=(0.7, (current_yield + new_yield)/2 + 0.1),
                   arrowprops=dict(arrowstyle='->', lw=1.5, color='red'),
                   fontsize=11, fontweight='bold', color='red')

# 4. Variable importance from regression
variables = ['Irrigation', 'Fertilizer', 'Rainfall', 'Quota Enforcement']
coefficients = [0.0020, 0.0032, 0.0013, 1.4428]
p_values = [0.000, 0.475, 0.000, 0.000]

# Create bar colors based on significance
colors = ['green' if p < 0.05 else 'gray' for p in p_values]

bars2 = axes[1, 1].bar(variables, coefficients, color=colors)
axes[1, 1].set_ylabel('Regression Coefficient')
axes[1, 1].set_title('Variable Importance in Yield Determination')
axes[1, 1].grid(True, alpha=0.3, axis='y')

# Add significance stars
for i, (coef, p_val) in enumerate(zip(coefficients, p_values)):
    if p_val < 0.001:
        star = '***'
    elif p_val < 0.01:
        star = '**'
    elif p_val < 0.05:
        star = '*'
    else:
        star = 'ns'
    
    axes[1, 1].text(i, coef + 0.05 * max(coefficients), star, 
                   ha='center', va='bottom', fontweight='bold')

plt.tight_layout()
plt.savefig('../report/images/summary_findings.png', dpi=300, bbox_inches='tight')
print("Summary visualization saved to report/images/summary_findings.png")

# Also create a simple text summary
summary_text = f"""
=== KEY FINDINGS SUMMARY ===

1. GROUNDWATER QUOTA ENFORCEMENT:
   - Strongest predictor of yield (coefficient: 1.44 t/ha per unit increase)
   - Statistically significant (p < 0.001)
   - High enforcement associated with 0.61-0.69 t/ha higher yields

2. IRRIGATION:
   - Positive effect (0.0020 t/ha per m³)
   - Statistically significant (p < 0.001)
   - Effect stronger at lower yield levels

3. RAINFALL:
   - Positive effect (0.0013 t/ha per mm)
   - Statistically significant (p < 0.001)

4. FERTILIZER:
   - Positive but not statistically significant (p = 0.475)

5. POLICY SIMULATION:
   - 25% increase in quota enforcement → 4.2% yield increase
   - From 4.291 to 4.471 t/ha average yield

=== RECOMMENDATIONS ===

1. Strengthen groundwater quota enforcement mechanisms
2. Maintain or increase irrigation water availability
3. Consider integrated water management (irrigation + rainfall)
4. Further research needed on fertilizer effectiveness
"""

with open('../outputs/key_findings_summary.txt', 'w') as f:
    f.write(summary_text)

print("Key findings summary saved to outputs/key_findings_summary.txt")