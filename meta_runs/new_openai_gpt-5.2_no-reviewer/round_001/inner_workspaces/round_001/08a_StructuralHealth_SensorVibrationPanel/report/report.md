# Structural Health / Reliability Analytics — Sensor Vibration Panel (08a)

## 1. Data, scope, and methods

### Dataset
The analysis uses `data/sensor_panel_timeseries.csv` with columns:

- `timestamp_utc` (UTC timestamp)
- `asset_id` (equipment identifier)
- `zone` (location/area)
- `vibration_rms_mm_s` (vibration velocity RMS, mm/s)
- `peak_accel_g` (peak acceleration, g)
- `bearing_temp_c` (bearing temperature, °C)
- `rpm` (rotational speed)
- `load_pct` (load, %)
- `quality_flag` (telemetry quality)

Timestamps were parsed as timezone-aware UTC datetimes. Summary statistics are computed on all rows, and also on a **“good-quality”** subset using a conservative heuristic:
- If `quality_flag` was binary (`{0,1}`), it was treated as 1=good.
- Otherwise, explicit “bad”-like tokens (e.g., `bad`, `invalid`, `fail`) were excluded; all other/unrecognized values were retained.

### Sampling and trend estimation
Sampling was inferred from timestamp spacing:
- For each asset: median/quantile/min/max inter-sample time deltas.
- A simple gap metric: fraction of deltas exceeding 2× the asset’s median delta.

To describe vibration evolution over time while limiting over-weighting from high-frequency assets, vibration time series were visualized using **hourly medians** with a **24-hour rolling median** overlay.

For a coarse trend ranking, a linear slope (mm/s per day) was fit to each asset’s **6-hour median** vibration series (after clipping extreme MAD-based outliers).

## 2. Observation window, assets, zones, and implied sampling

### Observation window and represented assets
Across all rows, the dataset spans the following observation window:

- Start/end (UTC): see `outputs/overview_all.json`
- Number of assets and zones: see `outputs/overview_all.json`

Figure 1 shows the per-asset time coverage.

![Observation window by asset](images/observation_window_by_asset.png)

**Figure 1.** Start/end timestamps by asset.

### Sampling implied by timestamps
Assets show heterogeneous timestamp spacing (often irregular), so the dataset should be treated as **panel telemetry** rather than a fixed-rate signal.

Figure 2 summarizes the distribution of **per-asset median sampling intervals**.

![Sampling interval histogram](images/sampling_interval_hist.png)

**Figure 2.** Histogram of median inter-sample spacing (per asset).

Operationally, this suggests that:
- Some assets are effectively near-continuous (small median delta), suitable for time-based trend monitoring.
- Others are sparse/irregular, where event-based changes (step increases, regime shifts) are more reliable than short-horizon spectral interpretations.

## 3. How vibration evolves over time (and comparisons across assets/zones)

### Vibration RMS evolution by asset
Figure 3 plots vibration RMS by asset (hourly median; dark line is a 24-hour rolling median).

![Vibration RMS time series by asset](images/vibration_rms_timeseries_by_asset.png)

**Figure 3.** Vibration RMS evolution by asset with a smoothed trend overlay.

From this extract, assets generally fall into three qualitative groups:
1. **Stable baseline**: vibration fluctuates around a consistent band.
2. **Regime-dependent**: vibration changes track operating conditions (speed/load changes).
3. **Drifting upward**: sustained increases in the smoothed median over weeks suggest progressive degradation (e.g., imbalance growth, looseness, lubrication/bearing wear), subject to confirmation that operating regime did not change.

A simple trend ranking (linear slope on 6-hour medians) is saved in `outputs/vibration_trend_slopes_good.csv`.

### Cross-zone comparison (where supported)
To avoid bias from assets with denser sampling, zone comparisons were based on **weekly median vibration per asset**.

![Vibration by zone weekly box](images/vibration_by_zone_weekly_box.png)

**Figure 4.** Distribution of weekly median vibration RMS by zone (per asset).

Interpretation guidance:
- Differences between zones in Figure 4 can reflect a mix of **asset mix**, **process duty**, and **installation/foundation** effects.
- Because this extract may have limited assets per zone, zone conclusions should be treated as **screening-level**: they identify where to focus review, not definitive root cause.

## 4. Relationships among vibration, temperature, speed, and load

### Vibration vs operating conditions
Figure 5 shows pooled (all assets) scatter relationships between vibration RMS and bearing temperature / speed / load for rows with acceptable quality.

![Vibration vs temperature/rpm/load](images/vibration_vs_temp_rpm_load.png)

**Figure 5.** Vibration RMS vs bearing temperature, rpm, and load (colored by asset; pooled regression in black).

Correlation summaries (overall and per asset) are provided in `outputs/correlations_good.csv`. In general:
- **Vibration–rpm correlation** indicates speed-driven excitation (imbalance/misalignment often increases with speed).
- **Vibration–load correlation** suggests process loading effects (hydraulic/aerodynamic forces, coupling/torque).
- **Vibration–bearing temperature correlation** is consistent with friction/lubrication issues, increased bearing losses, or reduced heat dissipation; however, both vibration and temperature can also co-vary with load.

### Example multichannel traces
For assets with good coverage across vibration, temperature, rpm, and load, Figure 6 shows hourly median multichannel time series (up to three best-covered assets were plotted).

- `images/multichannel_timeseries_asset_*.png`

These plots help distinguish:
- **Condition-driven increases** (vibration rises mainly when rpm/load rises)
- **Asset-health drift** (vibration and/or temperature rise at similar rpm/load)

## 5. Monitoring and maintenance recommendations (prioritized)

The following recommendations are aligned to what this extract supports (time trends, cross-asset comparisons, and coarse correlations), and avoid assuming full-resolution vibration waveform diagnostics.

1. **Prioritize assets with sustained upward vibration trends for near-term inspection**
   - Use `outputs/vibration_trend_slopes_good.csv` to shortlist assets with the highest positive slopes and meaningful weekly median increases.
   - Recommended follow-ups: verify operating regime stability (rpm/load), then check alignment, soft-foot, looseness, coupling condition, and lubrication/bearing condition.

2. **Introduce regime-aware alerting (rpm/load normalized) rather than absolute vibration alone**
   - Where rpm/load exist, build alerts on vibration residuals vs rpm/load (e.g., expected vibration at given rpm/load).
   - This reduces false positives when duty cycles change and improves detection of true degradation.

3. **Jointly monitor vibration and bearing temperature for early bearing/lubrication warnings**
   - Assets showing co-increases in vibration and temperature at similar rpm/load should be treated as higher risk.
   - Add rules for: (a) temperature high percentile excursions, (b) concurrent vibration elevation, and (c) persistence over multiple samples.

4. **Treat high peak-acceleration excursions as impact/looseness flags and trigger targeted checks**
   - If `peak_accel_g` shows intermittent spikes while RMS remains moderate, investigate looseness, impacts, or process transients.

5. **Improve data governance for quality and sampling consistency**
   - Enforce clearer `quality_flag` semantics and completeness checks (especially for rpm/load), since regime-aware analytics depend on these channels.
   - For sparse/irregular assets, standardize minimum sampling or add event-based sampling during high-risk regimes.

## 6. Limitations

- The dataset is a time-series **extract**; conclusions are constrained to observed windows and available channels.
- Asset duty cycles and sensor mounting details are not provided; comparisons across assets/zones may partially reflect operational differences.
- No waveform/spectral features are available; root-cause diagnosis (e.g., bearing defect frequency confirmation) is not possible here.

## Reproducibility

All analysis code is in `code/analyze.py`. Intermediate tables are written to `outputs/`, and figures to `report/images/`.
