# Annual Load Forecast and Reliability-Oriented Operations Commentary (15‑minute series)

## Abstract
This analysis uses a 15‑minute system load time series (`data/load_15min.csv`) to develop an **annual load outlook** and **reliability-oriented commentary** appropriate for an operations review. We (i) clean and gap-fill the 15‑minute series, (ii) quantify historical annual energy and peak demand, (iii) extract operationally relevant variability metrics (load factor, ramp rates, load duration), and (iv) produce a **next-calendar-year** forecast of annual energy and annual peak using a **calendar-only daily regression** with residual bootstrap uncertainty.

## Data overview
The input dataset is a single-column (load) 15‑minute series with timestamps.

Key coverage and quality indicators (from the cleaned, reindexed 15‑minute grid):

- Study period: **{START}** to **{END}**
- Sampling: nominal **15 minutes** (after deduplication/reindexing)
- Reindexed missingness (pre-fill): **{MISS_PCT:.2f}%** of intervals
- Years represented: **{YMIN}–{YMAX}** ({NYEARS} annual points)

Figure 1 provides a daily mean overview of the period.

![Daily mean load time series](images/fig1_daily_mean_timeseries.png)

## Methodology
### Cleaning and regularization
1. Parse the timestamp field and coerce load to numeric.
2. Aggregate duplicate timestamps by averaging.
3. Reindex to a complete 15‑minute grid.
4. Fill missing intervals using (a) time interpolation for short gaps (≤1 hour), (b) median by time-of-week for remaining gaps, and finally (c) forward/back fill.

### Derived metrics
From the cleaned 15‑minute load series (assumed in **MW**):

- **Daily mean (MW)**: average of 15‑minute values.
- **Daily peak (MW)**: daily maximum of 15‑minute values.
- **Daily energy (MWh/day)**: \(\sum_t \text{MW}_t \times 0.25\,\text{h}\).
- **Annual energy (MWh/year)**: sum of daily energy.
- **Annual peak (MW/year)**: maximum of daily peaks.
- **Ramps (MW/h)**: absolute 1‑step ramp \(|\Delta\text{MW}_{15m}|\times 4\).

### Forecast model (calendar-only)
To support an annual operations outlook without exogenous weather/economic drivers, we fit two **daily** regression models:

- Daily energy model: \(E_d = f(\text{trend},\,\text{day-of-week},\,\text{annual Fourier seasonality}) + \varepsilon_d\)
- Daily peak model: \(P_d = f(\text{trend},\,\text{day-of-week},\,\text{annual Fourier seasonality}) + \eta_d\)

where annual seasonality is represented by Fourier terms (K=3). Models are estimated by OLS.

### Uncertainty quantification (residual bootstrap)
For the **next calendar year** (forecast year = last observed year + 1), we:

1. Generate daily predictions for all days in the forecast year.
2. Sample historical daily residuals with replacement and add them to predicted days.
3. Compute simulated annual totals and annual maxima.

We report **P10/P50/P90** for annual energy and annual peak.

### Validation
If the dataset contains a complete last calendar year and at least one preceding year, we backtest by training through the end of the penultimate year and predicting the last year.

![Backtest on last full year](images/fig3_backtest_daily_models.png)

## Results
### Historical annual energy and peak
Historical annual energy and annual peak are shown in Figure 2.

![Historical annual energy and peak](images/fig2_annual_energy_and_peak.png)

Selected historical context:
- First year ({YMIN}): energy **{E0_TWH:.3f} TWh**, peak **{P0_MW:.1f} MW**
- Last year ({YLAST}): energy **{ELAST_TWH:.3f} TWh**, peak **{PLAST_MW:.1f} MW**
- Approx. multi-year growth (CAGR, first→last): energy **{CAGR_E_PCT:.2f}%/yr**, peak **{CAGR_P_PCT:.2f}%/yr**

### Reliability-oriented operating characteristics
System-level variability metrics from the full 15‑minute series:

- Overall maximum (15‑min): **{PEAK_OVERALL_MW:.1f} MW** at **{PEAK_TIME}**
- Overall minimum (15‑min): **{MIN_OVERALL_MW:.1f} MW** at **{MIN_TIME}**
- Mean load: **{MEAN_MW:.1f} MW**
- Load factor (mean/peak): **{LOAD_FACTOR:.3f}**
- 99th percentile absolute ramp rate: **{RAMP_P99:.1f} MW/h**
- Maximum observed absolute ramp rate: **{RAMP_MAX:.1f} MW/h**

Figure 5 summarizes the **load duration curve** (capacity adequacy context) and the **ramp distribution** (flexibility/reserve context).

![Load duration and ramp distribution](images/fig5_duration_curve_and_ramps.png)

Operational interpretation (reliability lens):
- A **low load factor** (mean far below peak) implies adequacy is driven by a relatively small number of high-load intervals; planning margins should be anchored to peak-risk periods rather than annual averages.
- The **upper-tail ramp rates** (P99 and max) indicate the magnitude of intra-hour flexibility required from regulating and load-following resources.

### Seasonal and diurnal structure
Figure 6 shows the typical monthly-by-hour profile (hourly-averaged) over the last full year if available (otherwise the most recent ~12 months).

![Month-hour heatmap](images/fig6_month_hour_heatmap.png)

This view supports seasonal readiness reviews (e.g., morning/evening ramps; summer vs winter peak timing).

### Next-year annual forecast (energy and peak)
The calendar-only regression plus residual bootstrap yields the following **next calendar year** outlook (P10/P50/P90):

- Forecast year: **{FC_YEAR}**
- Annual energy (TWh): **P10 {FC_E_P10_TWH:.3f}**, **P50 {FC_E_P50_TWH:.3f}**, **P90 {FC_E_P90_TWH:.3f}**
- Annual peak (MW): **P10 {FC_P_P10:.1f}**, **P50 {FC_P_P50:.1f}**, **P90 {FC_P_P90:.1f}**

A compact summary table (bootstrap; calendar-only model) is provided below.

| Metric | P10 | P50 | P90 | Mean |
|---|---:|---:|---:|---:|
| Annual energy (TWh) | {FC_E_P10_TWH:.3f} | {FC_E_P50_TWH:.3f} | {FC_E_P90_TWH:.3f} | {FC_E_MEAN_TWH:.3f} |
| Annual peak (MW) | {FC_P_P10:.1f} | {FC_P_P50:.1f} | {FC_P_P90:.1f} | {FC_P_MEAN:.1f} |

Figure 4 visualizes the bootstrap distributions.

![Forecast distributions](images/fig4_forecast_distributions.png)

Figure 7 compares historical annual energy/peak against the next-year forecast with P10–P90 uncertainty.

![Historical vs forecast annual metrics](images/fig7_historical_vs_forecast.png)

Backtest accuracy (if available) provides an empirical check on the calendar-only approach:
- Daily energy: MAE **{BT_E_MAE:.1f} MWh/day**, MAPE **{BT_E_MAPE:.2f}%**
- Daily peak: MAE **{BT_P_MAE:.1f} MW**, MAPE **{BT_P_MAPE:.2f}%**

## Discussion (operations/reliability commentary)
1. **Adequacy is peak-driven**: historical peaks are materially above the mean (load factor {LOAD_FACTOR:.3f}). For reliability reviews, the relevant annual forecast product is the distribution of **annual peak** (P50 for planning baseline; P90 as a conservative stress point).
2. **Flexibility needs are evident in ramp tails**: the P99 absolute ramp ({RAMP_P99:.1f} MW/h) and maximum observed ramp ({RAMP_MAX:.1f} MW/h) provide a practical starting point for reserve sufficiency checks (regulation and load-following). Any resource outages during high-ramp windows can disproportionately increase operational risk.
3. **Seasonal readiness**: the month–hour heatmap highlights when typical daily peaks and ramps occur. Operations preparations (maintenance scheduling, reserve procurement, fuel assurance) should avoid periods with historically high peaks and steep ramps.
4. **Forecast limitations**: absent temperature/economic drivers, the calendar-only model captures **structural seasonality and weekday effects** but cannot anticipate extreme-weather-driven peaks. For reliability studies, this argues for pairing the baseline forecast with explicit stress scenarios (e.g., heat wave / cold snap) and derates/outage assumptions.

## Reproducibility
All results are generated by `code/run_analysis.py` and written to `outputs/` and `report/images/`.

Key output files:
- `outputs/historical_annual_metrics.csv`
- `outputs/forecast_summary.csv`
- `outputs/reliability_metrics.csv`
- `outputs/model_summaries.txt`

---

## Appendix: Figures
- Figure 1: Daily mean load time series (`images/fig1_daily_mean_timeseries.png`)
- Figure 2: Historical annual energy and peak (`images/fig2_annual_energy_and_peak.png`)
- Figure 3: Last-year backtest (if available) (`images/fig3_backtest_daily_models.png`)
- Figure 4: Next-year forecast distributions (`images/fig4_forecast_distributions.png`)
- Figure 5: Load duration curve and ramp distribution (`images/fig5_duration_curve_and_ramps.png`)
- Figure 6: Month–hour heatmap (`images/fig6_month_hour_heatmap.png`)
- Figure 7: Historical vs forecast annual metrics (`images/fig7_historical_vs_forecast.png`)
