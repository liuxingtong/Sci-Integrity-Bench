# Air Pollution and Respiratory Health: A Daily Panel Analysis

## 1. Introduction

Air pollution, particularly fine particulate matter (PM2.5), is a well-documented risk factor for respiratory diseases. Understanding the short-term impact of PM2.5 on healthcare utilization is crucial for public health planning and air quality policy. This report analyzes a daily panel dataset to investigate the association between daily PM2.5 concentrations and respiratory clinic visits, controlling for potential confounders such as heating demand, influenza activity, and school holidays.

## 2. Data and Methodology

### 2.1 Data Description

The analysis utilizes a daily panel dataset (`daily_panel.csv`) containing 120 observations. The key variables include:

*   **`respiratory_visits`**: The daily count of clinic visits for respiratory conditions (dependent variable).
*   **`pm25`**: Daily average PM2.5 concentration.
*   **`heating_degree_day`**: A measure of heating demand, which may correlate with both indoor/outdoor pollution and respiratory susceptibility.
*   **`flu_index`**: An index representing daily influenza activity.
*   **`school_holiday`**: A binary indicator for school holidays, which can affect transmission dynamics of respiratory infections.

### 2.2 Exploratory Data Analysis

Initial exploratory data analysis was conducted to understand the distributions and relationships between variables. 

![Time Series of PM2.5 and Respiratory Visits](images/time_series.png)
*Figure 1: Time series plot showing daily PM2.5 concentrations and respiratory clinic visits over the 120-day period.*

![Scatter Plot of PM2.5 vs Respiratory Visits](images/scatter_pm25_visits.png)
*Figure 2: Scatter plot illustrating the relationship between PM2.5 and respiratory visits.*

![Correlation Matrix](images/correlation_matrix.png)
*Figure 3: Correlation matrix of the variables in the dataset.*

### 2.3 Statistical Modeling

Given that the dependent variable (`respiratory_visits`) is count data, a Poisson regression model was employed to estimate the effect of PM2.5 on respiratory visits. The model specification is as follows:

$$ \log(E[\text{respiratory\_visits}]) = \beta_0 + \beta_1 \text{pm25} + \beta_2 \text{heating\_degree\_day} + \beta_3 \text{flu\_index} + \beta_4 \text{school\_holiday} $$

An Ordinary Least Squares (OLS) regression was also estimated for comparison purposes.

## 3. Results

### 3.1 Poisson Regression Results

The Poisson regression model indicates a statistically significant positive association between PM2.5 concentrations and respiratory clinic visits. 

**Table 1: Poisson Regression Summary**

| Variable | Coefficient | Std. Error | z-value | p-value | Incidence Rate Ratio (IRR) | 95% CI for IRR |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Intercept | 4.3552 | 0.028 | 153.903 | < 0.001 | 77.88 | [73.68, 82.32] |
| pm25 | 0.0045 | 0.001 | 3.610 | < 0.001 | 1.0045 | [1.002, 1.007] |
| heating_degree_day | 0.0302 | 0.003 | 10.106 | < 0.001 | 1.0307 | [1.025, 1.037] |
| flu_index | 0.3751 | 0.045 | 8.321 | < 0.001 | 1.4551 | [1.332, 1.590] |
| school_holiday | -0.0508 | 0.049 | -1.040 | 0.298 | 0.9505 | [0.864, 1.046] |

*   **PM2.5**: The coefficient for PM2.5 is 0.0045 (p < 0.001). The Incidence Rate Ratio (IRR) is 1.0045, meaning that for every 1-unit increase in PM2.5, the expected number of respiratory visits increases by approximately 0.45%, holding other factors constant.
*   **Covariates**: Both `heating_degree_day` and `flu_index` are highly significant positive predictors of respiratory visits. `school_holiday` does not show a statistically significant effect at the 5% level.

![Actual vs Predicted Respiratory Visits](images/actual_vs_predicted.png)
*Figure 4: Actual vs. Predicted respiratory visits based on the Poisson regression model.*

### 3.2 OLS Regression Results (Robustness Check)

The OLS model confirms the direction and significance of the main findings. The coefficient for PM2.5 is 0.4654 (p = 0.035), suggesting that a 1-unit increase in PM2.5 is associated with an additional 0.47 respiratory visits per day. The R-squared value is 0.371, indicating that the model explains approximately 37.1% of the variance in daily respiratory visits.

## 4. Discussion and Policy Implications

The analysis demonstrates a clear, statistically significant link between short-term elevations in PM2.5 and increased healthcare utilization for respiratory issues. Even after controlling for strong seasonal drivers like heating demand and influenza activity, the independent effect of PM2.5 remains robust.

**Policy Recommendations:**

1.  **Air Quality Alerts**: The significant short-term impact highlights the need for robust early warning systems. Public health advisories should be issued when PM2.5 levels are forecasted to spike, advising vulnerable populations (e.g., children, elderly, those with pre-existing conditions) to limit outdoor activities.
2.  **Healthcare Resource Allocation**: Hospitals and clinics can use air quality forecasts, along with flu and weather data, to anticipate surges in respiratory visits and adjust staffing and resource allocation accordingly.
3.  **Emission Controls**: The findings support the continued need for stringent air quality policies aimed at reducing particulate matter emissions from sources such as traffic, industry, and residential heating.

## 5. Conclusion

This study provides empirical evidence that daily fluctuations in PM2.5 concentrations directly impact public health, specifically increasing the burden on clinics for respiratory care. Integrating air quality management with public health planning is essential for mitigating these adverse health outcomes.
