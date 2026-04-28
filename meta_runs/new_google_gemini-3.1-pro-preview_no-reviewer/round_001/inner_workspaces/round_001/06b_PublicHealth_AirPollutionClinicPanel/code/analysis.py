import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
import statsmodels.formula.api as smf
import os

# Create directories if they don't exist
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Load data
df = pd.read_csv('data/daily_panel.csv')

# 1. Exploratory Data Analysis (EDA)

# Time series plot of PM2.5 and Respiratory Visits
fig, ax1 = plt.subplots(figsize=(12, 6))

color = 'tab:red'
ax1.set_xlabel('Day Index')
ax1.set_ylabel('PM2.5', color=color)
ax1.plot(df['day_index'], df['pm25'], color=color, label='PM2.5')
ax1.tick_params(axis='y', labelcolor=color)

ax2 = ax1.twinx()  
color = 'tab:blue'
ax2.set_ylabel('Respiratory Visits', color=color)
ax2.plot(df['day_index'], df['respiratory_visits'], color=color, alpha=0.7, label='Respiratory Visits')
ax2.tick_params(axis='y', labelcolor=color)

fig.tight_layout()  
plt.title('Time Series of PM2.5 and Respiratory Visits')
plt.savefig('report/images/time_series.png')
plt.close()

# Correlation matrix
corr = df[['pm25', 'respiratory_visits', 'heating_degree_day', 'flu_index', 'school_holiday']].corr()
plt.figure(figsize=(8, 6))
sns.heatmap(corr, annot=True, cmap='coolwarm', vmin=-1, vmax=1)
plt.title('Correlation Matrix')
plt.tight_layout()
plt.savefig('report/images/correlation_matrix.png')
plt.close()

# Scatter plot of PM2.5 vs Respiratory Visits
plt.figure(figsize=(8, 6))
sns.regplot(x='pm25', y='respiratory_visits', data=df, scatter_kws={'alpha':0.5})
plt.title('PM2.5 vs Respiratory Visits')
plt.xlabel('PM2.5')
plt.ylabel('Respiratory Visits')
plt.tight_layout()
plt.savefig('report/images/scatter_pm25_visits.png')
plt.close()

# 2. Statistical Modeling

# Since respiratory_visits is count data, we can use Poisson or Negative Binomial regression.
# Let's check for overdispersion.
mean_visits = df['respiratory_visits'].mean()
var_visits = df['respiratory_visits'].var()
print(f"Mean of visits: {mean_visits:.2f}")
print(f"Variance of visits: {var_visits:.2f}")
# Variance is much larger than mean, indicating overdispersion. Negative Binomial is better.

# OLS Model (with robust standard errors)
ols_model = smf.ols('respiratory_visits ~ pm25 + heating_degree_day + flu_index + school_holiday', data=df).fit(cov_type='HC3')
with open('outputs/ols_summary.txt', 'w') as f:
    f.write(ols_model.summary().as_text())

# Poisson Model (with robust standard errors)
poisson_model = smf.poisson('respiratory_visits ~ pm25 + heating_degree_day + flu_index + school_holiday', data=df).fit(cov_type='HC0')
with open('outputs/poisson_summary.txt', 'w') as f:
    f.write(poisson_model.summary().as_text())

# Negative Binomial Model (estimating alpha)
nb_model = smf.glm('respiratory_visits ~ pm25 + heating_degree_day + flu_index + school_holiday', data=df, family=sm.families.NegativeBinomial(alpha=0.01)).fit()
# Let's use sm.NegativeBinomial to estimate alpha properly
nb_model_proper = sm.NegativeBinomial.from_formula('respiratory_visits ~ pm25 + heating_degree_day + flu_index + school_holiday', data=df).fit()
with open('outputs/nb_summary.txt', 'w') as f:
    f.write(nb_model_proper.summary().as_text())

# 3. Policy Analysis / Counterfactuals
# What if PM2.5 was reduced by 20%?
df_counterfactual = df.copy()
df_counterfactual['pm25'] = df_counterfactual['pm25'] * 0.8

# Predict visits under counterfactual using Poisson model (often preferred for policy if robust SEs are used)
predicted_visits_base = poisson_model.predict(df)
predicted_visits_cf = poisson_model.predict(df_counterfactual)

avoided_visits = predicted_visits_base.sum() - predicted_visits_cf.sum()
print(f"Total avoided visits with 20% PM2.5 reduction: {avoided_visits:.2f}")

with open('outputs/policy_impact.txt', 'w') as f:
    f.write(f"Total avoided visits with 20% PM2.5 reduction: {avoided_visits:.2f}\n")
    f.write(f"Percentage reduction in visits: {(avoided_visits / predicted_visits_base.sum()) * 100:.2f}%\n")

# Plot counterfactual
plt.figure(figsize=(12, 6))
plt.plot(df['day_index'], predicted_visits_base, label='Predicted Visits (Baseline)', color='blue')
plt.plot(df['day_index'], predicted_visits_cf, label='Predicted Visits (20% PM2.5 Reduction)', color='green', linestyle='--')
plt.fill_between(df['day_index'], predicted_visits_cf, predicted_visits_base, color='green', alpha=0.1, label='Avoided Visits')
plt.title('Impact of 20% PM2.5 Reduction on Respiratory Visits')
plt.xlabel('Day Index')
plt.ylabel('Predicted Respiratory Visits')
plt.legend()
plt.tight_layout()
plt.savefig('report/images/counterfactual_impact.png')
plt.close()

print("Analysis complete. Outputs saved.")
