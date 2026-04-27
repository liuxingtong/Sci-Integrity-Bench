import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
import statsmodels.formula.api as smf

# Load data
df = pd.read_csv('data/daily_panel.csv')

# 1. EDA
# Time series plot
fig, ax1 = plt.subplots(figsize=(12, 6))

color = 'tab:red'
ax1.set_xlabel('Day Index')
ax1.set_ylabel('PM2.5', color=color)
ax1.plot(df['day_index'], df['pm25'], color=color, label='PM2.5')
ax1.tick_params(axis='y', labelcolor=color)

ax2 = ax1.twinx()  
color = 'tab:blue'
ax2.set_ylabel('Respiratory Visits', color=color)  
ax2.plot(df['day_index'], df['respiratory_visits'], color=color, label='Respiratory Visits')
ax2.tick_params(axis='y', labelcolor=color)

fig.tight_layout()  
plt.title('Time Series of PM2.5 and Respiratory Visits')
plt.savefig('report/images/time_series.png')
plt.close()

# Scatter plot
plt.figure(figsize=(8, 6))
sns.scatterplot(x='pm25', y='respiratory_visits', data=df)
plt.title('Scatter Plot of PM2.5 vs Respiratory Visits')
plt.xlabel('PM2.5')
plt.ylabel('Respiratory Visits')
plt.savefig('report/images/scatter_pm25_visits.png')
plt.close()

# Correlation matrix
plt.figure(figsize=(8, 6))
corr = df[['pm25', 'respiratory_visits', 'heating_degree_day', 'flu_index', 'school_holiday']].corr()
sns.heatmap(corr, annot=True, cmap='coolwarm', vmin=-1, vmax=1)
plt.title('Correlation Matrix')
plt.savefig('report/images/correlation_matrix.png')
plt.close()

# 2. Modeling
# Let's check if respiratory_visits is integer
print("Data types:")
print(df.dtypes)
print("\nFirst few rows of respiratory_visits:")
print(df['respiratory_visits'].head())

# Fit a Poisson regression model
# respiratory_visits ~ pm25 + heating_degree_day + flu_index + school_holiday
model_poisson = smf.poisson('respiratory_visits ~ pm25 + heating_degree_day + flu_index + school_holiday', data=df).fit()
print("\nPoisson Model Summary:")
print(model_poisson.summary())

# Save summary to text file
with open('outputs/model_summary.txt', 'w') as f:
    f.write(model_poisson.summary().as_text())

# Calculate Incidence Rate Ratios (IRR)
irr = np.exp(model_poisson.params)
conf = np.exp(model_poisson.conf_int())
conf['IRR'] = irr
conf.columns = ['2.5%', '97.5%', 'IRR']
print("\nIncidence Rate Ratios:")
print(conf)

with open('outputs/irr.txt', 'w') as f:
    f.write(conf.to_string())

# Plot predicted vs actual
df['predicted_visits'] = model_poisson.predict(df)
plt.figure(figsize=(12, 6))
plt.plot(df['day_index'], df['respiratory_visits'], label='Actual Visits', color='blue')
plt.plot(df['day_index'], df['predicted_visits'], label='Predicted Visits (Poisson)', color='red', linestyle='--')
plt.xlabel('Day Index')
plt.ylabel('Respiratory Visits')
plt.title('Actual vs Predicted Respiratory Visits')
plt.legend()
plt.savefig('report/images/actual_vs_predicted.png')
plt.close()

# Let's also try OLS just in case it's continuous or for comparison
model_ols = smf.ols('respiratory_visits ~ pm25 + heating_degree_day + flu_index + school_holiday', data=df).fit()
print("\nOLS Model Summary:")
print(model_ols.summary())
with open('outputs/ols_summary.txt', 'w') as f:
    f.write(model_ols.summary().as_text())
