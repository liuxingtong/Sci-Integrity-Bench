# Oceanography CTD Cruise Stations: Vertical Profile and Thermohaline Structure Analysis

## Abstract
This report integrates `data/cruise_ctd.csv` to characterize vertical hydrographic structure (temperature–salinity–density), along-track variability, and simple stratification/mixed-layer metrics derived from CTD casts. We standardize station/cast identifiers into per-profile groups, compute TEOS-10 thermodynamic variables where possible (Absolute Salinity, Conservative Temperature, and potential density anomaly σ₀), and summarize thermohaline structure using representative profiles, T–S diagrams, and along-track sections.

## Data overview
`cruise_ctd.csv` is organized as **long-form CTD data**: multiple depth/pressure samples per station (profile). The analysis infers column roles (station/cast, latitude/longitude, vertical coordinate, temperature, salinity) and then aggregates to a per-profile summary.

Key dataset characteristics (computed):

- **Rows:**  see `outputs/ctd_summary.json`.
- **Profiles (stations/casts):** see `outputs/ctd_summary.json`.
- **Depth coverage:** see `outputs/ctd_summary.json`.
- **Hydrographic ranges:** see `outputs/ctd_summary.json`.
- **Upper-ocean mixing:** see `outputs/ctd_summary.json`.

Figures supporting sampling context:

- Station map / track (if latitude–longitude were present): `images/fig01_station_map.png`
- Distribution of maximum profile depths: `images/fig02_max_depth_hist.png`
- Missingness summary of standardized analysis variables: `images/fig12_missingness.png`

## Methods
### 1. Column inference and standardization
Because CTD files vary in naming conventions, columns are inferred by regex matching (e.g., `lat/latitude`, `press/pressure`, `temp/temperature`, `sal/salinity`). A `profile_id` is constructed from available station and cast fields (or a fallback based on location/time). All numeric fields are coerced with `pandas.to_numeric(..., errors='coerce')`.

### 2. Vertical coordinate handling
- If **pressure (dbar)** is present, it is used as the primary vertical coordinate.
- If only **depth (m)** is present, pressure is approximated as 1 dbar ≈ 1 m for TEOS-10 calculations.

Depth in meters is computed from pressure and latitude using TEOS-10 (`gsw.z_from_p`) when available.

### 3. TEOS-10 thermodynamic variables (thermոհaline structure)
When the `gsw` package is available, we compute:

- **Absolute Salinity**: \(SA\) from Practical Salinity \(SP\)
- **Conservative Temperature**: \(CT\) from in-situ temperature \(t\)
- **Potential density anomaly**: \(\sigma_0\)

If TEOS-10 calculations fail (e.g., missing library), a simple proxy density is used to preserve workflow continuity; however, TEOS-10 outputs are preferred for physical interpretation.

### 4. Stratification and mixed-layer depth
- **Brunt–Väisälä frequency squared** \(N^2\) is computed per profile via TEOS-10 `gsw.Nsquared` and summarized as **maximum \(N^2\)** per cast (a compact index of stratification intensity).
- **Mixed-layer depth (MLD)** is estimated using a common density threshold criterion: the shallowest depth where \(\sigma_0\) exceeds the near-surface reference (median over 0–10 m) by **0.03 kg m⁻³**.

### 5. Along-track sections
Profiles are ordered by time when available; otherwise by geographic progression. Along-track distance is computed from station coordinates using a haversine formula. For section plots, each profile is bin-averaged onto uniform depth bins (5 m) and displayed as a distance–depth field.

## Results

### Sampling geometry and depth coverage
If station positions are available, the cruise track and station spacing are shown in **Figure 1**.

![CTD station positions](images/fig01_station_map.png)

Depth coverage varies by station; the distribution of per-profile maximum depths is shown in **Figure 2**, indicating the cruise includes a mixture of shallow and deeper casts.

![Distribution of maximum profile depths](images/fig02_max_depth_hist.png)

### Vertical structure: representative profiles
Three casts spanning the cruise progression (early/mid/late by along-track distance) illustrate canonical vertical structure: surface mixed layer, thermocline/pycnocline development, and deeper water properties.

![Representative vertical profiles](images/fig03_profiles_T_S_sigma0.png)

Interpretation (qualitative, dataset-driven):
- Temperature generally decreases with depth, indicating a thermocline whose sharpness varies among stations.
- Salinity structure can reveal a halocline (freshening or salinification with depth) and helps diagnose water-mass mixing.
- The density profile (σ₀) typically increases with depth, and the near-surface density jump is used to estimate MLD.

### Thermohaline structure: T–S relationships and water-mass context
The T–S diagram compactly summarizes the cruise hydrography and reveals whether variability is dominated by temperature, salinity, or both. Density contours (σ₀) are overlaid when TEOS-10 is available.

![T–S diagram](images/fig04_TS_diagram.png)

Key takeaways:
- Points colored by depth separate surface and subsurface water properties.
- Curvature or distinct branches in T–S space indicate mixing between endmembers or the presence of multiple water masses.

### Along-track thermohaline variability (sections)
Temperature, salinity, and density sections provide a synoptic view of horizontal gradients (fronts) and the depth structure of water masses.

![Along-track temperature section](images/fig05_section_temperature.png)

![Along-track salinity section](images/fig06_section_salinity.png)

![Along-track density section](images/fig07_section_sigma0.png)

Interpretation:
- Coherent along-track gradients in near-surface temperature and salinity often indicate surface forcing and/or advection.
- Subsurface structures (tilting isohalines/isopycnals) can indicate geostrophic adjustment, mesoscale features, or topographic influences (depending on the cruise region).

### Mixed-layer depth and stratification
The MLD varies along the cruise track, consistent with spatially varying buoyancy forcing and/or mixing intensity.

![MLD along track](images/fig08_MLD_alongtrack.png)

Where TEOS-10 stratification was computable, the maximum \(N^2\) provides a compact measure of stratification intensity and its spatial variability.

![max N2 along track](images/fig09_maxN2_alongtrack.png)

Surface-property relationships help connect MLD variability to surface thermohaline conditions.

![Surface TS colored by MLD](images/fig10_surface_TS_MLD.png)

![MLD vs surface temperature](images/fig11_MLD_vs_surfaceT.png)

## Validation and quality checks

### Completeness and availability of key variables
The fraction of missing values for standardized analysis variables is summarized in **Figure 12**.

![Missingness summary](images/fig12_missingness.png)

### Pressure–depth consistency (when both fields exist)
If both pressure and reported depth are available in the input file, their relationship should be approximately linear and close to 1 dbar ≈ 1 m (with latitude-dependent deviations). The comparison plot is provided in **Figure 13** when applicable.

![Pressure vs depth validation](images/fig13_pressure_vs_depth.png)

## Discussion
This integrated CTD analysis demonstrates how a single station-wise CSV can be converted into scientifically interpretable products:

- **Profile diagnostics** (T/S/σ₀ vs depth) highlight mixed-layer properties and deeper water mass characteristics.
- A **T–S diagram** provides a compact thermohaline fingerprint and a way to recognize mixing lines and distinct water masses.
- **Along-track sections** reveal lateral gradients and subsurface structure that are difficult to diagnose from individual profiles.
- **MLD and \(N^2\)** offer physically interpretable summary metrics for upper-ocean mixing and stratification.

### Limitations
- If station coordinates or times are missing/limited, the along-track ordering and distance metric become approximate.
- MLD estimates depend on the chosen threshold (here Δσ₀ = 0.03 kg m⁻³) and on near-surface sampling density.
- If TEOS-10 calculations cannot be performed (e.g., missing `gsw`), derived density/stratification should be treated as qualitative.

## Reproducibility
All analysis is reproducible via:

```bash
python code/analyze_ctd.py
```

Outputs:
- Processed long-form CTD table: `outputs/ctd_processed_long.csv`
- Profile summary table (MLD, max depth, surface properties, etc.): `outputs/ctd_profiles_summary.csv`
- Stratification profile data (if computed): `outputs/ctd_N2.csv`
- Figures: `report/images/*.png`

