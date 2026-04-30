"""Generate report/report.md from analysis outputs.

This script reads outputs/ctd_summary.json and writes a publication-style
markdown report referencing figures in report/images/.

Run after code/analyze_ctd.py.
"""

from __future__ import annotations

import json
import os


def main():
    summ_path = "outputs/ctd_summary.json"
    if not os.path.exists(summ_path):
        raise FileNotFoundError("Run code/analyze_ctd.py first to create outputs/ctd_summary.json")

    s = json.load(open(summ_path))
    tr = s.get("temp_range_C", [None, None])
    sr = s.get("sal_range_PSU", [None, None])
    dr = s.get("sigma0_range", [None, None])

    def fnum(x, fmt):
        try:
            return format(float(x), fmt)
        except Exception:
            return "NA"

    # Optional richer stats from profile summary
    qstats = ""
    prof_path = "outputs/ctd_profiles_summary.csv"
    if os.path.exists(prof_path):
        import pandas as pd
        prof = pd.read_csv(prof_path)
        def qline(name, series):
            series = pd.to_numeric(series, errors='coerce')
            qq = series.quantile([0.1, 0.5, 0.9])
            return f"| {name} | {qq.iloc[0]:.2f} | {qq.iloc[1]:.2f} | {qq.iloc[2]:.2f} |\n"
        lines = "| Metric | p10 | p50 | p90 |\n|---|---:|---:|---:|\n"
        if 'max_depth_m' in prof:
            lines += qline('Profile max depth (m)', prof['max_depth_m'])
        if 'MLD_m' in prof:
            lines += qline('Mixed-layer depth, MLD (m)', prof['MLD_m'])
        if 'T_surf' in prof:
            lines += qline('Surface temperature (°C)', prof['T_surf'])
        if 'S_surf' in prof:
            lines += qline('Surface salinity (PSU)', prof['S_surf'])
        qstats = "\nQuantiles across profiles (p10/p50/p90):\n\n" + lines + "\n"

    md = f"""# Oceanography CTD Cruise Stations: Vertical Profile and Thermohaline Structure Analysis

## Abstract
This report integrates `data/cruise_ctd.csv` to characterize vertical hydrographic structure (temperature–salinity–density), along-track variability, and upper-ocean mixing/stratification metrics derived from CTD casts. We standardize station/cast identifiers into per-profile groups, compute TEOS-10 variables where possible (Absolute Salinity, Conservative Temperature, and potential density anomaly σ₀), and summarize thermohaline structure using representative profiles, T–S diagrams, and along-track sections.

## Data overview
`cruise_ctd.csv` is organized as **long-form CTD data**: multiple depth/pressure samples per station (profile). The analysis infers column roles (station/cast, latitude/longitude, vertical coordinate, temperature, salinity) and then aggregates to a per-profile summary.

Key dataset characteristics (computed):

- **Rows:** {int(s.get('n_rows_raw', 0)):,} raw; {int(s.get('n_rows_used', 0)):,} used after filtering missing temperature/salinity/vertical coordinate.
- **Profiles (stations/casts):** {int(s.get('n_profiles', 0)):,}.
- **Depth coverage:** maximum observed depth {fnum(s.get('depth_max_m'), '.1f')} m; 90th percentile of profile maximum depth {fnum(s.get('depth_p90_profile_max_m'), '.1f')} m.
- **Hydrographic ranges:** temperature {fnum(tr[0], '.2f')} to {fnum(tr[1], '.2f')} °C; salinity {fnum(sr[0], '.2f')} to {fnum(sr[1], '.2f')} PSU; σ₀ {fnum(dr[0], '.2f')} to {fnum(dr[1], '.2f')} kg m⁻³.
- **Upper-ocean mixing:** median mixed-layer depth (MLD) {fnum(s.get('mld_median_m'), '.1f')} m (density threshold criterion; see Methods).
{qstats}
Supporting sampling context:

- Station map / track: `images/fig01_station_map.png`
- Distribution of maximum profile depths: `images/fig02_max_depth_hist.png`
- Missingness summary of standardized analysis variables: `images/fig12_missingness.png`

## Methods
### 1. Column inference and standardization
CTD files vary in naming conventions, so columns are inferred by regex matching (e.g., `lat/latitude`, `press/pressure`, `temp/temperature`, `sal/salinity`). A `profile_id` is constructed from available station and cast fields (or a fallback based on location/time). Numeric fields are coerced with `pandas.to_numeric(..., errors='coerce')`.

### 2. Vertical coordinate handling
- If **pressure (dbar)** is present, it is used as the primary vertical coordinate.
- If only **depth (m)** is present, pressure is approximated as 1 dbar ≈ 1 m for TEOS-10 calculations.

Depth in meters is computed from pressure and latitude using TEOS-10 (`gsw.z_from_p`) when available.

### 3. TEOS-10 thermodynamic variables (thermohaline structure)
When the `gsw` (TEOS-10) package is available, we compute:

- **Absolute Salinity**: \(SA\) from Practical Salinity \(SP\)
- **Conservative Temperature**: \(CT\) from in-situ temperature \(t\)
- **Potential density anomaly**: \(\sigma_0\)

If TEOS-10 calculations fail (e.g., missing library), a simple proxy density is used to preserve workflow continuity; TEOS-10 outputs are preferred for physical interpretation.

### 4. Stratification and mixed-layer depth
- **Brunt–Väisälä frequency squared** \(N^2\) is computed per profile via TEOS-10 `gsw.Nsquared` and summarized as **maximum \(N^2\)** per cast (compact stratification index).
- **Mixed-layer depth (MLD)** is estimated as the shallowest depth where \(\sigma_0\) exceeds the near-surface reference (median over 0–10 m) by **0.03 kg m⁻³**.

### 5. Along-track sections
Profiles are ordered by time when available; otherwise by geographic progression. Along-track distance is computed from station coordinates using a haversine formula. For section plots, each profile is bin-averaged onto uniform depth bins (5 m) and displayed as a distance–depth field.

## Results

### Sampling geometry and depth coverage

![CTD station positions](images/fig01_station_map.png)

![Distribution of maximum profile depths](images/fig02_max_depth_hist.png)

### Vertical structure: representative profiles
Three casts spanning the cruise progression (early/mid/late by along-track distance) illustrate surface mixed-layer properties, thermocline/pycnocline development, and deeper water characteristics.

![Representative vertical profiles](images/fig03_profiles_T_S_sigma0.png)

### Thermohaline structure: T–S relationships
The T–S diagram compactly summarizes cruise hydrography and reveals whether variability is dominated by temperature, salinity, or both. Potential density contours (σ₀) are overlaid when TEOS-10 is available.

![T–S diagram](images/fig04_TS_diagram.png)

### Along-track thermohaline variability (sections)

![Along-track temperature section](images/fig05_section_temperature.png)

![Along-track salinity section](images/fig06_section_salinity.png)

![Along-track density section](images/fig07_section_sigma0.png)

### Mixed-layer depth and stratification

![MLD along track](images/fig08_MLD_alongtrack.png)

![max N2 along track](images/fig09_maxN2_alongtrack.png)

![Surface TS colored by MLD](images/fig10_surface_TS_MLD.png)

![MLD vs surface temperature](images/fig11_MLD_vs_surfaceT.png)

## Validation and quality checks

### Completeness of key variables

![Missingness summary](images/fig12_missingness.png)

### Pressure–depth consistency (when both fields exist)

![Pressure vs depth validation](images/fig13_pressure_vs_depth.png)

## Discussion
The integrated workflow converts a station-wise CSV into standard hydrographic products:

- **Profiles** (T/S/σ₀ vs depth) diagnose mixed-layer structure and deeper water masses.
- A **T–S diagram** provides a thermohaline fingerprint and a way to recognize mixing lines or multiple water masses.
- **Along-track sections** reveal lateral gradients and coherent subsurface structures.
- **MLD and \(N^2\)** offer physically interpretable summary metrics for upper-ocean mixing and stratification.

### Limitations
- If station coordinates or times are missing, along-track ordering and distance become approximate.
- MLD estimates depend on the chosen threshold (here Δσ₀ = 0.03 kg m⁻³) and near-surface sampling density.
- If TEOS-10 calculations cannot be performed, derived density/stratification should be treated as qualitative.

## Reproducibility
Run the full analysis pipeline:

```bash
python code/analyze_ctd.py
python code/make_report.py
```

Key outputs:
- Processed long-form CTD table: `outputs/ctd_processed_long.csv`
- Profile summary table: `outputs/ctd_profiles_summary.csv`
- Stratification table (if computed): `outputs/ctd_N2.csv`
- Figures: `report/images/*.png`
"""

    os.makedirs("report", exist_ok=True)
    with open("report/report.md", "w", encoding="utf-8") as f:
        f.write(md)


if __name__ == "__main__":
    main()
