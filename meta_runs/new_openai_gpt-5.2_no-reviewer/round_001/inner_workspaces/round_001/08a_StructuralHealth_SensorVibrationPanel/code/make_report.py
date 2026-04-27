from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

DATA_PATH = Path('data/sensor_panel_timeseries.csv')
REPORT_PATH = Path('report/report.md')


def parse_quality_good(df: pd.DataFrame) -> pd.Series:
    if 'quality_flag' not in df.columns:
        return pd.Series(True, index=df.index)
    q_str = df['quality_flag'].astype(str).str.strip().str.lower()
    unique = set(q_str.dropna().unique().tolist())
    if unique.issubset({'0', '1'}):
        return q_str == '1'
    bad = {'bad','poor','invalid','fail','fault','suspect','questionable','0','false','f','reject'}
    good = {'good','ok','okay','valid','pass','1','true','t','accept'}
    is_bad = q_str.isin(bad)
    is_good = q_str.isin(good)
    return is_good | (~is_bad)


def fmt_dt(s: str | None) -> str:
    if s is None:
        return 'NA'
    # shorten ISO-ish strings for readability
    return s.replace('+00:00','Z')


def md_table(df: pd.DataFrame, float_fmt: str = '{:.3g}') -> str:
    d = df.copy()
    for c in d.columns:
        if pd.api.types.is_float_dtype(d[c]):
            d[c] = d[c].map(lambda x: '' if pd.isna(x) else float_fmt.format(float(x)))
    return d.to_markdown(index=False)


def main():
    df = pd.read_csv(DATA_PATH)
    df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'], utc=True, errors='coerce')

    # overview
    tmin = df['timestamp_utc'].min()
    tmax = df['timestamp_utc'].max()

    assets = sorted(df['asset_id'].dropna().unique().tolist())
    zones = sorted(df['zone'].dropna().unique().tolist())

    good_mask = parse_quality_good(df)
    good_rate = float(good_mask.mean())

    # sampling by asset
    asset_sampling = pd.read_csv('outputs/asset_sampling_all.csv')
    valid = asset_sampling['median_dt_s'].dropna()
    sampling_summary = {
        'n_assets_with_sampling': int(valid.shape[0]),
        'median_of_asset_medians_min': float(valid.median()/60.0) if len(valid) else np.nan,
        'p10_asset_medians_min': float(valid.quantile(0.1)/60.0) if len(valid) else np.nan,
        'p90_asset_medians_min': float(valid.quantile(0.9)/60.0) if len(valid) else np.nan,
        'min_asset_median_min': float(valid.min()/60.0) if len(valid) else np.nan,
        'max_asset_median_min': float(valid.max()/60.0) if len(valid) else np.nan,
    }

    # channel coverage
    cols = ['vibration_rms_mm_s','peak_accel_g','bearing_temp_c','rpm','load_pct']
    coverage_pct = (df[cols].notna().mean()*100.0).round(1)
    complete_regime_pct = float(df[['vibration_rms_mm_s','bearing_temp_c','rpm','load_pct']].notna().all(axis=1).mean()*100.0)

    # zone weekly medians
    d = df.loc[good_mask].dropna(subset=['timestamp_utc','vibration_rms_mm_s','asset_id','zone']).copy()
    weekly = (
        d.set_index('timestamp_utc')
        .groupby(['asset_id','zone'])['vibration_rms_mm_s']
        .resample('7D')
        .median()
        .reset_index()
        .dropna(subset=['vibration_rms_mm_s'])
    )
    zone_summary = (
        weekly.groupby('zone')['vibration_rms_mm_s']
        .agg(n_weekly_points='count', median_weekly_med='median', p75=lambda s: np.nanpercentile(s,75), p95=lambda s: np.nanpercentile(s,95))
        .reset_index()
        .sort_values('median_weekly_med', ascending=False)
    )

    # vibration stats by asset
    asset_vib = (
        d.groupby(['asset_id'])
        .agg(
            vib_n=('vibration_rms_mm_s','size'),
            vib_median=('vibration_rms_mm_s','median'),
            vib_p95=('vibration_rms_mm_s', lambda s: np.nanpercentile(s,95)),
            peak_p95=('peak_accel_g', lambda s: np.nanpercentile(s.dropna(),95) if s.notna().any() else np.nan),
            temp_p95=('bearing_temp_c', lambda s: np.nanpercentile(s.dropna(),95) if s.notna().any() else np.nan),
        )
        .reset_index()
    )
    asset_vib = asset_vib[asset_vib['vib_n'] >= 50].sort_values('vib_p95', ascending=False)

    top_vib = asset_vib.head(6)
    top_temp = asset_vib.dropna(subset=['temp_p95']).sort_values('temp_p95', ascending=False).head(6)

    # trend slopes
    trend = pd.read_csv('outputs/vibration_trend_slopes_good.csv')
    top_slopes = trend.head(6)

    # correlations overall
    corr = pd.read_csv('outputs/correlations_good.csv')
    ov = corr[corr.asset_id=='__overall__'].iloc[0]
    corr_overall = {
        'n_complete_rows': int(ov['n_complete']),
        'corr(vib, peak_accel)': float(ov.get('corr_vibration_rms_mm_s__peak_accel_g', np.nan)),
        'corr(vib, bearing_temp)': float(ov.get('corr_vibration_rms_mm_s__bearing_temp_c', np.nan)),
        'corr(vib, rpm)': float(ov.get('corr_vibration_rms_mm_s__rpm', np.nan)),
        'corr(vib, load)': float(ov.get('corr_vibration_rms_mm_s__load_pct', np.nan)),
    }

    # compose report
    md = []
    md.append('# Structural Health / Reliability Analytics — Sensor Vibration Panel (08a)')
    md.append('')

    md.append('## 1. Data overview')
    md.append('')
    md.append(f"**Rows:** {len(df):,}  ")
    md.append(f"**Assets:** {len(assets)} ({', '.join(map(str, assets))})  ")
    md.append(f"**Zones:** {len(zones)} ({', '.join(map(str, zones))})  ")
    md.append(f"**Observation window (UTC):** {tmin} to {tmax} (≈{(tmax-tmin)/pd.Timedelta(days=1):.2f} days)  ")
    md.append(f"**Quality-flag retained (heuristic):** {good_rate*100:.1f}% of rows")
    md.append('')

    md.append('**Channel availability (non-missing, % of rows):**')
    md.append('')
    md.append(md_table(coverage_pct.reset_index().rename(columns={'index':'channel',0:'coverage_%'}), float_fmt='{:.1f}'))
    md.append('')
    md.append(f"Rows with all of vibration+temperature+rpm+load present: **{complete_regime_pct:.1f}%**")
    md.append('')

    md.append('## 2. Sampling implied by timestamps')
    md.append('')
    md.append('Timestamps are not uniformly spaced; the data behave as irregular panel telemetry. Per-asset median inter-sample spacing provides a practical implied sampling rate:')
    md.append('')
    md.append(
        f"- Median of per-asset medians: **{sampling_summary['median_of_asset_medians_min']:.2f} min**  \n"
        f"- 10th–90th percentile of per-asset medians: **{sampling_summary['p10_asset_medians_min']:.2f}–{sampling_summary['p90_asset_medians_min']:.2f} min**  \n"
        f"- Range (min to max per-asset median): **{sampling_summary['min_asset_median_min']:.2f}–{sampling_summary['max_asset_median_min']:.2f} min**"
    )
    md.append('')
    md.append('![Observation window by asset](images/observation_window_by_asset.png)')
    md.append('')
    md.append('![Sampling interval histogram](images/sampling_interval_hist.png)')
    md.append('')

    md.append('## 3. Vibration behavior over time and comparisons')
    md.append('')
    md.append('### 3.1 Vibration RMS evolution by asset')
    md.append('Figure 3 shows hourly medians (light) and a 24-hour rolling median (dark), which is a trend-friendly representation for irregular telemetry.')
    md.append('')
    md.append('![Vibration RMS time series by asset](images/vibration_rms_timeseries_by_asset.png)')
    md.append('')

    md.append('**Assets with the highest 95th-percentile vibration RMS (good-quality rows; assets with ≥50 vibration points):**')
    md.append('')
    md.append(md_table(top_vib[['asset_id','vib_n','vib_median','vib_p95','peak_p95','temp_p95']].rename(columns={'vib_n':'n_vib'}), float_fmt='{:.3g}'))
    md.append('')

    if len(top_slopes):
        md.append('**Assets with the strongest increasing vibration trend** (linear slope on 6-hour medians; higher = faster increase):')
        md.append('')
        md.append(md_table(top_slopes[['asset_id','n_points_6h','slope_mm_s_per_day','end_minus_start_mm_s','median_mm_s']], float_fmt='{:.3g}'))
        md.append('')

    md.append('### 3.2 Zone comparisons (screening-level)')
    md.append('Zone comparisons were computed using **weekly median vibration per asset** to avoid overweighting densely sampled assets. Figure 4 and the table below summarize zone-level distributions.')
    md.append('')
    md.append('![Vibration by zone weekly box](images/vibration_by_zone_weekly_box.png)')
    md.append('')
    md.append(md_table(zone_summary, float_fmt='{:.3g}'))
    md.append('')

    md.append('## 4. Relationships among vibration, temperature, speed, and load')
    md.append('')
    md.append('Overall (pooled across assets; complete-case rows), the following Pearson correlations were observed (good-quality rows):')
    md.append('')
    md.append('\n'.join([
        f"- Complete-case rows used: **{corr_overall['n_complete_rows']:,}**",
        f"- corr(vibration RMS, peak acceleration): **{corr_overall['corr(vib, peak_accel)']:.3f}**",
        f"- corr(vibration RMS, bearing temperature): **{corr_overall['corr(vib, bearing_temp)']:.3f}**",
        f"- corr(vibration RMS, rpm): **{corr_overall['corr(vib, rpm)']:.3f}**",
        f"- corr(vibration RMS, load %): **{corr_overall['corr(vib, load)']:.3f}**",
    ]))
    md.append('')
    md.append('![Vibration vs temperature/rpm/load](images/vibration_vs_temp_rpm_load.png)')
    md.append('')

    # multichannel figures
    multichannel = sorted(Path('report/images').glob('multichannel_timeseries_asset_*.png'))
    if multichannel:
        md.append('### 4.1 Multichannel examples')
        md.append('For assets with the best simultaneous coverage of vibration, bearing temperature, rpm, and load, the following hourly-median multichannel plots were generated:')
        md.append('')
        for p in multichannel[:3]:
            md.append(f"![]({p.as_posix().replace('report/','')})")
            md.append('')

    md.append('**Interpretation:** correlations and scatter trends can reflect both physics (e.g., vibration increases with rpm) and operational regimes; for maintenance prioritization, assets where vibration increases *without* corresponding rpm/load increases are of highest concern.')
    md.append('')

    md.append('## 5. Monitoring and maintenance recommendations (prioritized)')
    md.append('')
    md.append('1. **Act on assets with both high vibration and increasing trend.** Use the “top vib” table plus the slope table to shortlist candidates for near-term inspection; confirm the rise is not solely due to rpm/load regime shifts.')
    md.append('2. **Implement regime-aware alerting** (vibration expected vs rpm/load) where rpm/load are present; alert on residuals and persistence rather than raw vibration alone.')
    md.append('3. **Escalate when vibration and bearing temperature rise together at similar rpm/load.** This pattern is consistent with lubrication/bearing friction issues and merits targeted lubrication checks, bearing condition verification, and alignment review.')
    md.append('4. **Use peak-acceleration excursions as impact/looseness triggers.** Intermittent high `peak_accel_g` warrants checks for looseness, rubs, or mechanical impacts even if RMS is moderate.')
    md.append('5. **Strengthen telemetry quality governance.** Clarify `quality_flag` semantics and improve completeness for rpm/load; these channels materially improve interpretability and reduce false alarms.')
    md.append('')

    md.append('## 6. Limitations')
    md.append('')
    md.append('- This extract provides time trends and cross-sectional comparisons but not waveform/spectral diagnostics; root-cause confirmation (bearing defect frequencies, etc.) is out of scope.')
    md.append('- Zone differences may reflect asset mix and duty cycles; treat zone results as screening signals.')
    md.append('')

    md.append('## Reproducibility')
    md.append('')
    md.append('Analysis code: `code/analyze.py` (figures and tables) and `code/make_report.py` (this report). Intermediate results are stored in `outputs/`, and figures in `report/images/`.')

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text('\n'.join(md), encoding='utf-8')


if __name__ == '__main__':
    main()
