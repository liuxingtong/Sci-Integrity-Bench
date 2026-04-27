# RetailAnalytics AdSpendStoreSales (RET-ADV-ROLL)

## Abstract
We analyze a longitudinal **store-month panel** linking online advertising spend to sales revenue under policy **RET-ADV-ROLL**, where each store’s month-*t* ad budget is mechanically tied to a **fixed share of prior-month same-store sales**. This roll-forward rule provides a strong predictor of ad spend but also creates dynamics and potential endogeneity (ad responds to lagged sales, which may proxy persistent demand shocks). Using store and month fixed effects, a dynamic specification (lagged sales), and an IV design that instruments current ad spend with policy-implied spend (estimated store-specific share × lagged sales), we estimate the incremental sales generated per ad dollar and translate results into actionable budgeting guidance for next year’s monthly planning.

## Data overview
**Source:** `data/store_monthly_sales.csv` (store × month panel)

**Key variables:** `ad_spend_usd`, `sales_revenue_usd`, `foot_traffic`, `is_holiday_month`, `local_population`, `competitor_count`.

Panel size (from `outputs/data_overview.csv`):
- Observations: **36,000**
- Stores: **500**
- Coverage: **2019-01-01 00:00:00** to **2024-12-01 00:00:00**
- Mean monthly sales: **$202,737**
- Mean monthly ad spend: **$5,118**

## Policy mechanics (RET-ADV-ROLL) and diagnostics
RET-ADV-ROLL links budgets to lagged sales:

\[
\mathrm{ad}_{i,t} = s_i \cdot \mathrm{sales}_{i,t-1},
\]

where \(s_i\) is a store-specific “policy share”. We estimate \(\hat s_i\) as the **median** of \(\mathrm{ad}_{i,t}/\mathrm{sales}_{i,t-1}\) over time for each store and construct a policy-implied prediction \(\widehat{\mathrm{ad}}_{i,t}=\hat s_i\,\mathrm{sales}_{i,t-1}\).

**Diagnostics** (from `outputs/policy_diagnostics.csv`):
- Policy-share dispersion (p05 / p50 / p95): **0.0117 / 0.0251 / 0.0475**
- Corr(actual ad, policy-pred ad): **0.939**
- Within-store corr after demeaning: **0.812**
- Simple \(R^2\) for predicting ad with the policy rule: **0.871**

Figures show substantial cross-store heterogeneity in implied share, and that ad spend closely tracks policy-implied levels:

![Estimated policy-share distribution](images/policy_share_hist.png)

![Actual vs policy-predicted ad spend](images/policy_pred_vs_actual_ad.png)

## Empirical strategy
### Main challenge: endogeneity and dynamics
Even with store and month fixed effects, contemporaneous ad spend can be correlated with unobserved demand shocks, and the policy explicitly uses **lagged sales**, inducing persistence. We therefore report a sequence of specifications:

1. **Pooled OLS + store & month fixed effects** (baseline association)
2. **Two-way fixed effects (FE)**: store and month effects, plus covariates
3. **Dynamic FE**: adds lagged sales to absorb persistence/mean-reversion
4. **IV (2SLS)**: instruments current ad spend using **policy-implied spend** \(\widehat{\mathrm{ad}}_{i,t}=\hat s_i\,\mathrm{sales}_{i,t-1}\), controlling for lagged sales and fixed effects.

### Identification intuition for the IV
The instrument exploits variation generated mechanically by RET-ADV-ROLL: conditional on store and month effects, and controlling for lagged sales and observed covariates, policy-implied ad spend shifts the month-*t* budget in ways that are plausibly orthogonal to contemporaneous shocks to month-*t* sales.

Instrument strength (first-stage diagnostics from the fitted 2SLS model):
- Partial \(R^2\): **0.751**
- Partial F-statistic: **10,342.7**

## Results
### Marginal return to advertising (sales per ad dollar)
Estimated ad effects across level specifications (95% CI):

| Model | Ad effect estimate (sales $ per ad $) | 95% CI |
|---|---:|---:|
| Panel FE (entity+time) | 0.8077 | [0.7666, 0.8488] |
| Dynamic Panel FE (+ lag sales) | 0.5014 | [0.4603, 0.5425] |
| 2SLS IV (policy instrument) | 0.4749 | [0.4298, 0.5200] |

Visualization of cross-specification stability:

![Ad→Sales effects across level specifications](images/ad_effect_comparison_levels.png)

**Interpretation (preferred IV):** the point estimate implies **≈0.475 dollars of incremental sales per additional $1 of ad spend** on average (short-run, within store-month, conditional on controls and fixed effects). This is a *revenue* ROAS; profitability requires multiplying by gross margin (not observed here).

### Elasticity (log-log robustness)
A log-log FE model provides an elasticity-style summary (percent changes):

- Estimated elasticity of sales with respect to ad: **0.047** (95% CI [0.041, 0.053])

![Log-log elasticity estimate](images/ad_elasticity_loglog.png)

### Diminishing returns check
We fit a quadratic FE model \(\mathrm{sales} \sim b_1\,\mathrm{ad} + b_2\,\mathrm{ad}^2\) (ad scaled in $1,000s). The implied marginal ROAS declines with spend when \(b_2<0\). The estimated curve implies a **turning point** around **$12,235/month** (where the marginal effect crosses zero; interpret cautiously as an in-sample curvature diagnostic, not a literal optimum).

![Marginal ROAS vs spend (quadratic FE)](images/marginal_roas_quadratic.png)

## Validation
A simple holdout exercise trains a two-way FE model on all but the last 6 months and evaluates predictive accuracy on held-out months:
- Holdout RMSE: **64,593**
- Holdout MAE: **49,030**

![Holdout predictions vs actual](images/holdout_pred_vs_actual.png)

This validation is **predictive**, not causal; it is included to confirm that the controls and fixed effects capture substantial systematic variation.

## Implications for next-year monthly budget decisions
### 1) Portfolio-level guidance (total monthly budget)
- The preferred IV estimate suggests **positive short-run incremental sales per ad dollar** on average. For planning, translate a candidate monthly budget change \(\Delta B\) into expected incremental revenue \(\approx \hat\beta\,\Delta B\) with \(\hat\beta\approx 0.475\).
- The quadratic diagnostic implies **diminishing returns** at higher spend levels, so incremental dollars should not be concentrated entirely in already-high-spend store-months.

### 2) Store-level roll-up under RET-ADV-ROLL (choosing shares \(s_i\))
Because the policy sets \(\mathrm{ad}_{i,t} = s_i\,\mathrm{sales}_{i,t-1}\), changing \(s_i\) scales each store’s budget proportionally with its own lagged sales.

Practical recommendations:
- **Audit and normalize shares:** implied shares vary substantially across stores (p05–p95: 0.0117–0.0475; Figure 1). Stores at extreme shares should be reviewed for measurement issues (e.g., missing channels) or true structural differences.
- **Reallocate from likely-saturated spend:** where current spend is already high, the quadratic FE check predicts lower marginal returns; consider modestly reducing \(s_i\) for those stores and re-allocating to lower-spend stores.
- **Use store-level lift normalization:** even with a common \(\hat\beta\), the *percentage* lift from a given % increase in ad depends on the store’s baseline ad-to-sales ratio. The generated file `outputs/store_level_roi_iv.csv` ranks stores by predicted percent lift from a 10% ad increase.

Visualization of dispersion in implied shares vs store scale:

![Implied share vs mean sales](images/store_share_vs_sales.png)

### 3) A simple operational decision rule
For monthly planning with a fixed total budget increase \(\Delta B\):
1. **Cap increases** for stores already at/above the curvature turning point (diagnostic threshold \(~$12.2k/month\)).
2. Allocate remaining \(\Delta B\) to stores below the cap, prioritizing those with lower current spend (to hedge against diminishing returns) and stable operational capacity (traffic) to convert demand.

## Limitations and next steps
- **Instrument construction uses \(\hat s_i\):** we estimate shares from the same data, which introduces generated-regressor noise; clustered SEs help but do not fully address finite-sample uncertainty.
- **IV exclusion restriction:** if lagged sales contain persistent unobserved demand shocks that also directly affect current sales beyond the included lag control, the IV estimate may still be biased.
- **Channel aggregation:** `ad_spend_usd` is treated as a single input; budget recommendations would improve with channel-level data and conversion attribution.

Next analytical upgrades (if data become available):
- Explicit **distributed-lag** ad effects and decay.
- Store-level **heterogeneous treatment effects** (e.g., by population, competitor density).
- Profit impact using gross margin to convert sales lift into contribution.

---

## Reproducibility
All analysis code is in `code/run_analysis.py`. Key outputs are saved under `outputs/` and figures under `report/images/`.
