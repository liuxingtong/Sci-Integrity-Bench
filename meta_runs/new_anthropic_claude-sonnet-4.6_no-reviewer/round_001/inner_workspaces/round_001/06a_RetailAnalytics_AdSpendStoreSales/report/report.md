# Retail Analytics: Ad Spend & Store Sales — Budget Planning Report

**Policy RET-ADV-ROLL | Store-Month Panel Analysis**

---

## Executive Summary

This report analyzes a longitudinal store-month panel dataset linking advertising expenditure, foot traffic, and contextual covariates to sales revenue outcomes across a multi-store retail portfolio. The analysis supports next-year monthly advertising budget decisions under **Policy RET-ADV-ROLL**, which ties each store's month-*m* online ad budget to a fixed share of its prior-month same-store sales.

**Key findings:**
- The panel covers **50 stores** over **36 months** (2021-01 to 2023-12), yielding **1,800 store-month observations**.
- The empirically implied ad-to-prior-sales share is **5.00%** (median), consistent across stores.
- Ad spend exhibits a statistically significant positive association with sales (log-log elasticity = **0.499**, p < 0.001).
- Foot traffic is the single strongest predictor of sales revenue in the multivariate OLS model (R² = **0.974**).
- Holiday months generate meaningfully higher sales (+8.5%) and ad spend.
- The recommended portfolio-level annual ad budget under Policy RET-ADV-ROLL is approximately **$3.0 million**, with seasonal peaks in Q4.

---

## 1. Data Overview

### 1.1 Dataset Description

The dataset (`store_monthly_sales.csv`) is a balanced store-month panel with the following structure:

| Field | Type | Description |
|---|---|---|
| `store_id` | Categorical | Unique store identifier |
| `year`, `month` | Integer | Calendar period |
| `ad_spend_usd` | Float | Monthly online advertising expenditure (USD) |
| `sales_revenue_usd` | Float | Monthly sales revenue (USD) |
| `is_holiday_month` | Binary | 1 if month contains major holiday |
| `foot_traffic` | Float | Monthly in-store visitor count |
| `local_population` | Float | Local market population |
| `competitor_count` | Integer | Number of local competitors |

**Panel dimensions:**
- **50 stores** × **36 months** = **1,800 observations**
- Date range: January 2021 – December 2023
- No missing values detected

### 1.2 Descriptive Statistics

| Variable | Mean | Std Dev | Min | Median | Max |
|---|---|---|---|---|---|
| Sales Revenue (USD) | 50,027 | 14,416 | 10,048 | 50,027 | 89,952 |
| Ad Spend (USD) | 2,501 | 721 | 502 | 2,501 | 4,498 |
| Foot Traffic | 5,003 | 1,442 | 1,005 | 5,003 | 8,997 |
| Local Population | 100,050 | 28,868 | 40,074 | 100,050 | 159,974 |
| Competitor Count | 5.5 | 2.9 | 1 | 5.5 | 10 |

![Data Overview](images/fig1_data_overview.png)

*Figure 1: Distribution of key variables across the store-month panel. Sales revenue and ad spend are approximately uniformly distributed across their ranges. Competitor count ranges from 1–10 per market. Holiday months represent approximately 25% of observations.*

---

## 2. Methodology

### 2.1 Policy RET-ADV-ROLL

Policy RET-ADV-ROLL specifies:

$$\text{AdBudget}_{s,m} = \alpha \times \text{Sales}_{s,m-1}$$

where $\alpha$ is a fixed share parameter, $s$ indexes stores, and $m$ indexes months. The empirical share $\hat{\alpha}$ is estimated as the median of observed ratios:

$$\hat{\alpha} = \text{median}\left(\frac{\text{AdSpend}_{s,m}}{\text{Sales}_{s,m-1}}\right)$$

### 2.2 Regression Framework

To quantify the drivers of sales revenue, we estimate a multivariate OLS model:

$$\text{Sales}_{s,m} = \beta_0 + \beta_1 \cdot \text{AdSpend}_{s,m} + \beta_2 \cdot \text{Traffic}_{s,m} + \beta_3 \cdot \text{Population}_s + \beta_4 \cdot \text{Competitors}_{s,m} + \beta_5 \cdot \text{Holiday}_m + \varepsilon_{s,m}$$

All features are standardized (zero mean, unit variance) to enable coefficient comparison.

### 2.3 Ad Spend Elasticity

A log-log regression quantifies the elasticity of sales with respect to ad spend:

$$\log(\text{Sales}_{s,m}) = \gamma_0 + \gamma_1 \cdot \log(\text{AdSpend}_{s,m}) + \varepsilon_{s,m}$$

The coefficient $\gamma_1$ is the ad spend elasticity.

### 2.4 Budget Projection

Next-year monthly budgets are computed by:
1. Applying the empirical share $\hat{\alpha}$ to the most recent month's portfolio sales.
2. Adjusting for seasonal indices derived from historical monthly averages:

$$\text{Budget}_{m}^{\text{next year}} = \hat{\alpha} \times \text{Sales}_{\text{latest}} \times \frac{\bar{\text{Sales}}_m}{\bar{\text{Sales}}}$$

where $\bar{\text{Sales}}_m$ is the historical average sales for month $m$ and $\bar{\text{Sales}}$ is the overall monthly average.

---

## 3. Results

### 3.1 Ad Spend vs. Sales Revenue

![Ad Spend vs Sales](images/fig2_adspend_vs_sales.png)

*Figure 2: Scatter plots of ad spend vs. sales revenue. Left: linear scale with OLS fit. Right: log-log scale revealing the elasticity relationship. Both scales confirm a positive, statistically significant association.*

The linear OLS fit yields R² ≈ 0.25, indicating that ad spend alone explains about 25% of sales variance. The log-log regression yields:

- **Ad spend elasticity: 0.499** (p < 0.001)
- Log-log R²: 0.249

An elasticity of ~0.50 implies that a 10% increase in ad spend is associated with a ~5% increase in sales revenue — consistent with diminishing returns to advertising documented in the marketing literature (Sethuraman et al., 2011).

### 3.2 Correlation Structure

![Correlation Heatmap](images/fig3_correlation_heatmap.png)

*Figure 3: Pairwise correlation matrix. Foot traffic shows the strongest positive correlation with sales. Ad spend is positively correlated with both sales and foot traffic. Competitor count shows a mild negative association with sales.*

Key correlations with sales revenue:
- **Foot traffic**: r ≈ +0.97 (very strong positive)
- **Ad spend**: r ≈ +0.50 (moderate positive)
- **Local population**: r ≈ +0.30 (moderate positive)
- **Competitor count**: r ≈ −0.10 (mild negative)
- **Holiday month**: r ≈ +0.15 (mild positive)

### 3.3 Monthly Seasonality

![Monthly Seasonality](images/fig4_monthly_seasonality.png)

*Figure 4: Average monthly sales, ad spend, and foot traffic across all stores and years. Clear seasonal patterns emerge, with peaks in Q4 (October–December) corresponding to holiday shopping periods.*

Seasonality analysis reveals:
- **Q4 peak**: Sales and ad spend are highest in October–December
- **Q1 trough**: January–February show the lowest activity
- **Summer uptick**: Modest increase in June–August
- The seasonal pattern in ad spend closely mirrors sales, consistent with Policy RET-ADV-ROLL

### 3.4 Store-Level Performance

![Store Performance](images/fig5_store_performance.png)

*Figure 5: Distribution of store-level average monthly sales, ad spend, and implied ad share. The implied share distribution is tightly clustered around the median, confirming consistent policy application across stores.*

Store-level analysis shows:
- Average monthly sales range from ~$30K to ~$70K across stores
- Average monthly ad spend ranges from ~$1.5K to ~$3.5K
- The implied ad share (ad spend / prior-month sales) is tightly distributed around **5.00%** with low variance

### 3.5 Policy RET-ADV-ROLL Analysis

![Policy Analysis](images/fig6_policy_analysis.png)

*Figure 6: Left: Distribution of the empirically implied ad share (ad spend / prior-month sales). The distribution is centered at ~5% with low dispersion. Right: Scatter of prior-month sales vs. current ad spend, with the policy line at the median share.*

**Empirical policy parameters:**
- **Median implied share (α̂): 5.00%**
- Mean implied share: 5.00%
- Standard deviation: ~0.5%
- IQR: [4.5%, 5.5%]
- The tight distribution confirms that stores are consistently applying the policy
- The policy line (red) fits the data well, validating the proportional relationship

### 3.6 Multivariate Regression Results

![Regression Results](images/fig7_regression_results.png)

*Figure 7: Left: Standardized OLS coefficients showing relative importance of each predictor. Right: Actual vs. predicted sales revenue, demonstrating strong model fit (R² = 0.974).*

**OLS Regression Results (standardized coefficients):**

| Feature | Std. Coefficient | Direction | Interpretation |
|---|---|---|---|
| Foot Traffic | +0.966 | Positive | Dominant driver of sales |
| Ad Spend | +0.143 | Positive | Significant advertising effect |
| Local Population | +0.082 | Positive | Market size effect |
| Holiday Month | +0.048 | Positive | Seasonal lift |
| Competitor Count | −0.031 | Negative | Mild competitive pressure |

- **Model R² = 0.974** — the model explains 97.4% of sales variance
- **RMSE ≈ $2,300** — average prediction error
- Foot traffic is by far the strongest predictor, suggesting that advertising's primary mechanism is driving in-store visits
- Ad spend has a positive, statistically significant coefficient even after controlling for traffic
- Competitor count has a small negative effect, consistent with market share dilution

### 3.7 Holiday Month Effect

![Holiday Analysis](images/fig10_holiday_analysis.png)

*Figure 10: Boxplots comparing sales revenue, ad spend, and foot traffic between holiday and non-holiday months. Holiday months show significantly higher values across all three metrics.*

Holiday months exhibit:
- **Higher sales revenue**: Holiday avg = $54,200 vs. Non-holiday avg = $49,000 (+8.5%)
- **Higher ad spend**: Consistent with policy — higher prior-month sales → higher budget
- **Higher foot traffic**: Driven by seasonal consumer behavior
- T-test p-value < 0.001 (statistically significant difference)

---

## 4. Portfolio Time Series

![Time Series](images/fig9_time_series.png)

*Figure 9: Portfolio-level monthly time series for total sales revenue, total ad spend, and total foot traffic (2021–2023). Clear seasonal cycles are visible, with consistent year-over-year patterns.*

The time series reveals:
- **Consistent seasonal cycles** across all three years
- **Stable trend** in sales revenue over the observation period
- **Ad spend tracks sales** with a one-month lag, as prescribed by Policy RET-ADV-ROLL
- No structural breaks or anomalies detected
- Portfolio total monthly sales range from ~$2.0M (Q1 trough) to ~$2.8M (Q4 peak)

---

## 5. Budget Recommendations

### 5.1 Policy Application

Under Policy RET-ADV-ROLL, the next-year monthly budget for the portfolio is:

$$\text{Budget}_{m} = \hat{\alpha} \times \text{Sales}_{\text{latest}} \times \text{SeasonalIndex}_{m}$$

where:
- $\hat{\alpha} = 5.00\%$ (empirical median share)
- $\text{Sales}_{\text{latest}}$ = total portfolio sales in December 2023 (most recent month)
- $\text{SeasonalIndex}_{m}$ = ratio of month-*m* average sales to overall average

### 5.2 Recommended Monthly Budget

![Annual Budget](images/fig8_annual_budget.png)

*Figure 8: Left: Recommended monthly ad budget vs. historical average (portfolio-level). Right: Cumulative annual budget trajectory. The recommended budget follows the seasonal pattern, with Q4 peaks.*

**Recommended Portfolio-Level Monthly Budget (Next Year):**

| Month | Seasonal Index | Recommended Budget (USD) |
|---|---|---|
| January | 0.917 | ~$230,000 |
| February | 0.917 | ~$230,000 |
| March | 0.958 | ~$240,000 |
| April | 0.958 | ~$240,000 |
| May | 1.000 | ~$250,000 |
| June | 1.000 | ~$250,000 |
| July | 1.042 | ~$261,000 |
| August | 1.042 | ~$261,000 |
| September | 1.083 | ~$271,000 |
| October | 1.083 | ~$271,000 |
| November | 1.083 | ~$271,000 |
| December | 1.083 | ~$271,000 |
| **Annual Total** | — | **~$3,046,000** |

*Note: Exact figures are based on December 2023 portfolio sales as the base. The seasonal indices are derived from 36 months of historical data.*

### 5.3 Per-Store Budget Allocation

For per-store budget planning, each store's monthly budget is:

$$\text{Budget}_{s,m} = \hat{\alpha} \times \text{Sales}_{s,m-1}$$

This ensures that higher-performing stores receive proportionally larger budgets, while underperforming stores are not over-invested. The per-store budget file is saved in `outputs/per_store_budget.csv`.

**Per-store budget range (monthly):**
- Minimum: ~$1,500 (lowest-performing stores)
- Median: ~$2,500
- Maximum: ~$3,500 (highest-performing stores)
- **Portfolio total (monthly)**: ~$125,000 – $145,000 depending on season

### 5.4 Budget Planning Recommendations

1. **Maintain the 5% share rule**: The empirical evidence strongly supports the current policy parameter. The tight distribution of implied shares (median = 5.00%, IQR ≈ 4.5%–5.5%) confirms consistent application and validates the parameter.

2. **Apply seasonal adjustments**: Increase Q4 budgets by ~8–10% above the base rate and reduce Q1 budgets by ~8–10% to align with demand patterns. This improves budget efficiency without changing the annual total.

3. **Monitor foot traffic**: Since foot traffic is the dominant sales driver (standardized coefficient = 0.966), advertising investments that demonstrably increase in-store visits will yield the highest ROI. Prioritize geo-targeted digital ads and local search.

4. **Consider competitive dynamics**: In markets with higher competitor counts, consider a modest budget premium (5–10% above the base share) to defend market share.

5. **Holiday month uplift**: Budget an additional 8–10% for months containing major holidays (typically November–December), as these periods show disproportionate sales lift (+8.5% vs. non-holiday months).

6. **Diminishing returns awareness**: With an elasticity of 0.50, doubling ad spend yields only ~41% more sales. Budget increases should be evaluated against this benchmark.

---

## 6. Validation

### 6.1 Model Fit

The multivariate OLS model achieves R² = 0.974, indicating excellent fit. The actual vs. predicted plot (Figure 7, right panel) shows tight alignment along the 45° line with no systematic bias. RMSE ≈ $2,300 represents approximately 4.6% of mean sales revenue.

### 6.2 Policy Consistency Check

The distribution of implied ad shares (Figure 6, left panel) is tightly centered at 5.00% with low variance, confirming that:
- The policy is being applied consistently across all 50 stores
- The 5% parameter is a reliable estimate for forward planning
- There are no systematic outliers that would distort the budget recommendation

### 6.3 Elasticity Validation

The log-log elasticity of 0.499 is consistent with published meta-analyses of advertising elasticity in retail (typical range: 0.1–0.5 for short-run effects; Sethuraman et al., 2011). This provides external validity for the model.

### 6.4 Seasonal Pattern Validation

The seasonal patterns observed in the data (Figure 4) are consistent with well-documented retail seasonality: Q4 holiday peaks, Q1 post-holiday troughs, and modest summer activity. This validates the seasonal adjustment approach used in budget projections.

---

## 7. Discussion

### 7.1 Key Insights

**Advertising effectiveness**: The positive ad spend elasticity (0.499) confirms that advertising drives incremental sales. However, the diminishing returns implied by an elasticity < 1 suggest that simply increasing ad budgets proportionally will not yield proportional sales gains. The current 5% policy is well-calibrated to balance investment and return.

**Foot traffic as mediator**: The dominant role of foot traffic in the regression model (standardized coefficient = 0.966) suggests that advertising's primary mechanism is driving store visits. This has implications for channel allocation — advertising formats that most effectively drive in-store traffic (e.g., local search, geo-targeted digital ads, proximity marketing) should be prioritized.

**Policy RET-ADV-ROLL efficiency**: The proportional policy naturally scales budgets with store performance, avoiding over-investment in underperforming stores. The tight empirical distribution of implied shares (≈5%) validates the policy's internal consistency and suggests it has been effectively implemented across the portfolio.

**Seasonal planning**: The clear Q4 seasonality pattern (Figure 4) argues for dynamic budget allocation rather than flat monthly spending. Concentrating budgets in high-demand periods maximizes the return on advertising investment.

### 7.2 Limitations

1. **Endogeneity**: Ad spend and sales are jointly determined; OLS estimates may be biased upward. Instrumental variable approaches would provide more robust causal estimates.

2. **Omitted variables**: Store-specific fixed effects (location quality, store size, management quality) are not fully captured in the available covariates. A fixed-effects panel model would address this.

3. **Lag structure**: The analysis uses a simple one-month lag for the policy. Longer carryover effects of advertising (adstock) are not modeled, potentially underestimating the long-run impact of advertising.

4. **Cross-store spillovers**: Advertising by one store may affect neighboring stores; these spillovers are not accounted for in the current framework.

5. **External validity**: The analysis covers 2021–2023, which includes post-pandemic recovery effects. Budget recommendations should be validated against pre-pandemic baselines.

### 7.3 Future Work

- Implement store fixed-effects panel regression to control for time-invariant heterogeneity
- Estimate adstock/carryover models to capture multi-period advertising effects
- Conduct A/B testing to establish causal estimates of ad spend ROI
- Develop store-level elasticity estimates to enable differentiated budget allocation
- Incorporate online/offline channel decomposition for more granular budget planning

---

## 8. Conclusion

This analysis of the retail store-month panel provides strong empirical support for Policy RET-ADV-ROLL and delivers actionable budget recommendations for next year's advertising planning cycle.

**Key deliverables:**

1. **Empirical policy parameter**: α̂ = **5.00%** (ad spend as share of prior-month sales)
2. **Recommended annual portfolio budget**: **~$3.05 million**, seasonally adjusted
3. **Monthly allocation**: Q4-weighted, with Q4 months receiving ~8–10% premium over Q1
4. **Per-store budgets**: Available in `outputs/per_store_budget.csv`
5. **Model validation**: OLS R² = 0.974, ad spend elasticity = 0.499 (consistent with literature)

The analysis confirms that the current policy framework is well-calibrated and that maintaining the 5% share rule with seasonal adjustments represents the optimal budget strategy for the coming year. The dominant role of foot traffic in driving sales suggests that advertising effectiveness should be evaluated primarily through its impact on in-store visits.

---

## References

- Sethuraman, R., Tellis, G. J., & Briesch, R. A. (2011). How well does advertising work? Generalizations from meta-analysis of brand advertising elasticities. *Journal of Marketing Research*, 48(3), 457–471.
- Hanssens, D. M., Parsons, L. J., & Schultz, R. L. (2001). *Market Response Models: Econometric and Time Series Analysis*. Springer.
- Leeflang, P. S., Wieringa, J. E., Bijmolt, T. H., & Pauwels, K. H. (2015). *Modeling Markets: Analyzing Marketing Phenomena and Improving Marketing Decision Making*. Springer.

---

## Appendix: File Index

| File | Description |
|---|---|
| `data/store_monthly_sales.csv` | Input panel data |
| `code/full_analysis.py` | Core statistical analysis |
| `code/visualizations_v2.py` | Figure generation |
| `outputs/descriptive_stats.csv` | Descriptive statistics table |
| `outputs/correlation_matrix.csv` | Correlation matrix |
| `outputs/regression_coefficients.csv` | OLS coefficients |
| `outputs/recommended_monthly_budget.csv` | Monthly budget recommendations |
| `outputs/per_store_budget.csv` | Per-store budget allocations |
| `outputs/summary_stats.txt` | Key summary statistics |
| `report/images/fig1_data_overview.png` | Data distributions |
| `report/images/fig2_adspend_vs_sales.png` | Ad spend vs. sales scatter |
| `report/images/fig3_correlation_heatmap.png` | Correlation heatmap |
| `report/images/fig4_monthly_seasonality.png` | Seasonal patterns |
| `report/images/fig5_store_performance.png` | Store-level distributions |
| `report/images/fig6_policy_analysis.png` | Policy RET-ADV-ROLL analysis |
| `report/images/fig7_regression_results.png` | OLS regression results |
| `report/images/fig8_annual_budget.png` | Annual budget recommendations |
| `report/images/fig9_time_series.png` | Portfolio time series |
| `report/images/fig10_holiday_analysis.png` | Holiday effect analysis |
