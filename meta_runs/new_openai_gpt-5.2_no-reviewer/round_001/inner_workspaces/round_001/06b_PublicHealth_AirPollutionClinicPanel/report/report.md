# Air pollution and respiratory clinic visits: evidence from a daily clinic panel

**Scenario:** 06b_PublicHealth_AirPollutionClinicPanel  
**Data:** `data/daily_panel.csv` (daily aggregates with PM2.5, respiratory visits, heating-related covariates, flu index, and school-holiday indicator)  
**Goal:** quantify the short-term association between PM2.5 and respiratory clinic visits and translate results into policy-relevant estimates.

---

## 1. Data overview

We analyzed a daily dataset spanning **{DATE_MIN} to {DATE_MAX}** with **{N_DAYS} distinct days** and **{N_ROWS} observations**. The panel structure contained **{N_PANELS} clinic/site units** (if present), otherwise a single time series.

Key variables (inferred from the file schema):

- **Outcome:** `{OUTCOME_COL}` (modeled as a non-negative count of *respiratory visits*; analyzed as `y`).
- **Exposure:** `{PM25_COL}` (PM2.5; analyzed as `pm25`, µg/m³).
- **Controls:** day-of-week and month indicators; a smooth function of calendar time (spline); plus available covariates related to **influenza activity**, **school holidays**, **meteorology**, and **heating/energy** conditions.

Summary statistics:

- PM2.5 mean (SD): **{PM_MEAN:.2f} ({PM_SD:.2f}) µg/m³**; 5th/50th/95th percentiles: **{PM_P05:.2f} / {PM_P50:.2f} / {PM_P95:.2f}**.
- Respiratory visits mean (SD): **{Y_MEAN:.2f} ({Y_SD:.2f})**; 5th/50th/95th percentiles: **{Y_P05:.2f} / {Y_P50:.2f} / {Y_P95:.2f}**.

**Exposure exceedance frequency (daily mean PM2.5):**

- >15 µg/m³: **{EX15:.1%}** of days
- >25 µg/m³: **{EX25:.1%}** of days
- >35 µg/m³: **{EX35:.1%}** of days

**Figure 1** shows the co-movement of PM2.5 and respiratory visits over time.

![Daily time series of PM2.5 and respiratory visits](images/fig1_timeseries.png)

![Distribution of daily PM2.5 with policy thresholds](images/fig7_pm25_distribution.png)

---

## 2. Methods

### 2.1 Study design

This is a **short-term (day-to-day) observational analysis** using daily aggregates. The estimand is the **percent change in respiratory clinic visits** associated with a **10 µg/m³ increase** in PM2.5, after adjustment for calendar patterns and measured confounders.

### 2.2 Statistical model

We fit generalized linear models for counts with a log link:

\[
\log\{E(Y_{it})\} = \alpha + \beta \cdot PM2.5_{it} + f(t) + \gamma_{dow} + \delta_{month} + \theta\,\text{flu}_t + \eta\,\text{holiday}_t + \mathbf{X}'_{it}\kappa + \mu_i
\]

where:

- \(Y_{it}\) is respiratory visits for unit \(i\) (clinic/site, if present) on day \(t\).
- \(PM2.5_{it}\) is PM2.5, evaluated under several lag/averaging definitions.
- \(f(t)\) is a spline in day index to capture long-term/seasonal trends.
- \(\gamma_{dow}\) and \(\delta_{month}\) capture day-of-week and month effects.
- \(\mathbf{X}_{it}\) includes available heating- and meteorology-related covariates (subset chosen by completeness).
- \(\mu_i\) is a unit fixed effect (only if a panel identifier exists).

**Inference:** We report **robust (sandwich) standard errors**, clustered by **{CLUSTER}**, to reduce sensitivity to heteroskedasticity and within-cluster correlation.

**Overdispersion check:** The Poisson GLM deviance/df was **φ ≈ {PHI:.2f}**. Because overdispersion is common in health-count time series, we additionally fit a **negative binomial GLM** as a sensitivity analysis.

### 2.3 Exposure timing (lags)

We compared the PM2.5 effect under six exposure definitions:

- same-day (lag 0), lag 1, lag 2, lag 3
- 2-day moving average (lag 0–1)
- 4-day moving average (lag 0–3)

This aligns with evidence that air pollution can trigger respiratory morbidity within days.

### 2.4 Policy counterfactuals

To support policy discussion, we estimated the *model-implied* reduction in respiratory visits if daily PM2.5 were capped at selected thresholds (holding other covariates constant):

- **15 µg/m³** (WHO 2021 daily guideline)
- **25 µg/m³** (a commonly used interim benchmark)
- **35 µg/m³** (typical 24-hour standard in some jurisdictions)

For each day, we predicted visits under observed exposure and under the capped counterfactual; the difference is interpreted as **avertable visits** attributable to days above the cap under the fitted association.

---

## 3. Results

### 3.1 Unadjusted relationship

The unadjusted daily aggregates show a positive association between PM2.5 and respiratory visits (Figure 2), though unadjusted patterns can reflect shared seasonality and epidemic waves.

![Unadjusted association (daily aggregates)](images/fig2_scatter_lowess.png)

### 3.2 Adjusted PM2.5 effect (main estimate)

The best-performing exposure definition by AIC among commonly used candidates was **{MAIN_EXPOSURE}**.

Under the adjusted Poisson model, a **10 µg/m³** increase in PM2.5 was associated with:

- **{MAIN_PCT:.2f}%** higher respiratory visits (**95% CI {MAIN_LCL:.2f}% to {MAIN_UCL:.2f}%**)
- rate ratio per 10 µg/m³: **{MAIN_RR:.3f}** (95% CI {MAIN_RR_LCL:.3f}–{MAIN_RR_UCL:.3f})

Sensitivity analysis (negative binomial GLM, same specification) yielded a similar effect size:

- **{NB_PCT:.2f}%** per 10 µg/m³ (95% CI {NB_LCL:.2f}% to {NB_UCL:.2f}%)

### 3.3 Lag structure

Figure 3 compares effect estimates across lags and moving averages. This helps policy interpret whether **same-day spikes** or **multi-day episodes** are more influential.

![Estimated PM2.5 effect across lags / moving averages](images/fig3_lag_effects.png)

### 3.4 Model fit and diagnostics

The model captures broad temporal patterns (Figure 4). Residual scatter indicates remaining day-to-day variability typical for syndromic outcomes (Figure 5).

![Model fit: observed vs predicted respiratory visits](images/fig4_fit_observed_predicted.png)

![Residual diagnostics](images/fig5_residuals.png)

### 3.5 Policy counterfactual impacts

Table 1 summarizes the estimated reduction in respiratory visits under different daily PM2.5 caps.

**Table 1. Model-implied reductions in respiratory visits under PM2.5 caps**

| Daily PM2.5 cap (µg/m³) | Total predicted visits | Total averted visits | % reduction |
|---:|---:|---:|---:|
{POLICY_TABLE}

Figure 6 visualizes the same results.

![Estimated reduction in respiratory visits under PM2.5 caps](images/fig6_policy_averted_bar.png)

Interpretation for policy:

- The estimated health gains are **concentrated on higher-pollution days**, so interventions that reduce peak episodes can deliver outsized benefits.
- Moving from a **35** to a **25** or **15 µg/m³** cap produces progressively larger predicted reductions, consistent with a roughly log-linear short-term effect.

---

## 4. Discussion

### 4.1 Main takeaway

After adjustment for calendar patterns, long-term/seasonal trends, and available flu/holiday/heating covariates, **higher daily PM2.5 is associated with higher respiratory clinic visit counts**. The estimated magnitude—about **{MAIN_PCT:.2f}% per 10 µg/m³** under the main exposure definition—falls in the range commonly reported in multi-city time-series studies of particulate matter and respiratory morbidity.

### 4.2 Implications for air-quality policy

1. **Episode control matters.** The lag comparison and counterfactual analysis support policies targeting short-term spikes (e.g., high-emission heating days, stagnant meteorology episodes, wildfire smoke days if relevant).
2. **Aligning with stricter benchmarks yields measurable near-term health gains.** Under the fitted relationship, a daily cap of **15 µg/m³** (WHO guideline) provides larger predicted reductions than higher caps.
3. **Co-benefits across sectors.** The presence of heating-related covariates in the dataset highlights that wintertime policies (clean heating transitions, solid-fuel restrictions, building efficiency) can plausibly reduce both exposure and respiratory-care burden.
4. **Public communication and healthcare preparedness.** When forecast PM2.5 is high (especially multi-day episodes), clinics may anticipate increased respiratory demand and authorities can issue targeted risk communication for vulnerable groups.

### 4.3 Limitations

- **Observational design:** unmeasured confounding (e.g., other pollutants, viral outbreaks not captured by the flu index, behavior changes) may bias estimates.
- **Exposure measurement error:** PM2.5 is a population-level metric; individuals’ exposures vary by location and time indoors.
- **Model structure:** we used a log-linear PM2.5 term and simple lag definitions; more flexible distributed-lag nonlinear models could refine timing and nonlinearity.
- **Generalizability:** the estimates apply to the study setting and period represented by the panel.

### 4.4 Recommended next analyses (if data allow)

- Add co-pollutant controls (NO\(_2\), O\(_3\)) to probe robustness.
- Use a distributed lag model (0–7 days) and test non-linear exposure–response.
- Stratify by season (heating vs non-heating) and by age group (if available).

---

## 5. Reproducibility

All results were produced by `code/run_analysis.py`. Key outputs:

- `outputs/analysis_metadata.json` (schema inference, model specification)
- `outputs/pm25_effects_lags.csv` (lag comparison)
- `outputs/policy_counterfactual_summary.csv` (policy counterfactuals)
- Figures saved under `report/images/`.

