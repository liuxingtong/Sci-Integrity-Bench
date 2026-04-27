# Microseismic analysis brief: source clustering and structural context

## 1. Objective
Use the provided station geometry (`data/stations.csv`) and P-wave arrival picks (`data/arrival_times.csv`) to (i) locate microseismic sources under a simple travel-time model, (ii) identify spatial clusters, and (iii) summarize structural context implied by clustered event geometry (trends, approximate planes).

## 2. Data overview
Event locations are inferred from P-pick moveout across the array.

- Stations: see `data/stations.csv`.
- Picks: `data/arrival_times.csv` (one row per station pick per event).

Key counts (computed from the input files and successful locations):

- Number of stations: **{N_STATIONS}**
- Number of events (unique event IDs in picks): **{N_EVENTS_TOTAL}**
- Number of P picks: **{N_PICKS}**
- Picks per event: min **{P_MIN}**, median **{P_MED:.1f}**, mean **{P_MEAN:.1f}**, max **{P_MAX}**

Station coordinate extents (as provided; assumed Cartesian meters):

- X range: **{X_RANGE:.1f} m** (min {X_MIN:.1f}, max {X_MAX:.1f})
- Y range: **{Y_RANGE:.1f} m** (min {Y_MIN:.1f}, max {Y_MAX:.1f})
- Z range: **{Z_RANGE:.1f} m** (min {Z_MIN:.1f}, max {Z_MAX:.1f})

## 3. Methodology
### 3.1 Travel-time model and event location
Each event is located independently using a constant-velocity straight-ray model for P arrivals:

\[
 t_i = t_0 + \frac{\|\mathbf{x}-\mathbf{x}_i\|}{V_P}
\]

where \(\mathbf{x}=(x,y,z)\) is the event position, \(t_0\) is origin time, \(\mathbf{x}_i\) is station position, and \(V_P\) is the assumed P-wave velocity.

For each event, the unknowns \((x,y,z,t_0)\) are estimated by robust non-linear least squares (Huber loss) to reduce sensitivity to outlier picks.

**Depth convention:** The station `z` coordinate is treated as elevation (positive up). We report depth as

\[
\text{depth} = \bar{z}_{\text{stations}} - z_{\text{event}}\,.
\]

This yields positive depth values for events below the mean station elevation.

### 3.2 Selecting an effective constant velocity
A coarse grid search over \(V_P\in[2500,6500]\) m/s (step 250 m/s) was run on a subset of the best-sampled events. For each candidate \(V_P\), events were located and the **median event RMS** residual was recorded. The \(V_P\) minimizing this median RMS was selected for the final run.

Figure: velocity scan and chosen \(V_P\).

- `images/fig_velocity_scan.png`

### 3.3 Quality control and event set for clustering
To focus clustering on well-constrained locations:

- Require successful optimizer convergence and **≥ 5 picks** per event.
- Apply an RMS residual cutoff (90th percentile of RMS among the pre-filtered set).

Residual diagnostics are shown in `images/fig_misfit_qc.png`.

### 3.4 Clustering and structural metrics
We cluster in (x, y, depth) space using **DBSCAN** after standardization (zero mean, unit variance). DBSCAN is robust to noise and does not require pre-specifying the number of clusters.

- `eps` is chosen from the 90th percentile of the 5-nearest-neighbor distance distribution in standardized space (k-distance heuristic; `images/fig_kdistance.png`).
- `min_samples = 8`.

For each spatial cluster (excluding DBSCAN noise label `-1`), two geometric descriptors are computed:

1. **Trend azimuth**: azimuth (0–180°) of the first principal component (PCA PC1) horizontal projection.
2. **Best-fit plane strike/dip**: plane fit by SVD (normal = smallest-variance direction), converted to strike (0–360°) and dip (0–90°). These are approximate and should be treated as *geometric summaries* rather than formal focal-mechanism constraints.

## 4. Results
### 4.1 Event location performance
Using the selected constant velocity **\(V_P\approx {VP:.0f}\) m/s**, the locator produced:

- Located events (any solution): **{N_LOC}**
- Events retained for clustering after QC: **{N_GOOD}**

Misfit levels (event RMS residuals):

- Located set median RMS: **{RMS_LOC_MED:.3f} s** (p90 **{RMS_LOC_P90:.3f} s**)
- QC set median RMS: **{RMS_GOOD_MED:.3f} s** (p90 **{RMS_GOOD_P90:.3f} s**)

See `images/fig_misfit_qc.png` for the RMS distribution and its dependence on pick count.

### 4.2 Spatial distribution
Plan-view and depth sections of the QC event set are shown in:

- Plan view (stations + events colored by cluster): `images/fig_planview_clusters.png`
- Depth sections: `images/fig_depth_sections.png`

Depth range of the QC event set (relative to mean station elevation):

- **{D_MIN:.1f} m** to **{D_MAX:.1f} m**

### 4.3 Clustering outcome
DBSCAN identifies multiple spatial groupings plus a “noise” population.

- k-distance diagnostic used for eps selection: `images/fig_kdistance.png`
- Noise fraction (points labeled `-1`): **{NOISE_FRAC:.2f}**

Cluster trend azimuths (PC1) summarized as a rose diagram:

- `images/fig_rose_trends.png`

A table of the largest non-noise clusters and their structural summaries is provided below.

{CLUSTER_TABLE}

### 4.4 Structural context interpretation (geometric)
Across the located population, the clustering and PCA/plane fits suggest that microseismicity is not randomly distributed but organizes into one or more **preferred lineations/planes**. In a typical reservoir/stimulation or active-fault setting, such patterns are consistent with:

- Reactivation of **pre-existing fractures/faults** forming planar swarms.
- Stimulation-driven fracture growth following the **local stress field**, producing elongated clouds and subplanar features.
- Structural segmentation: distinct clusters may represent separate fracture sets or fault splays.

The **dominant cluster** (largest non-noise cluster) is additionally shown in an along-trend depth section:

- `images/fig_dominant_cluster_section.png`

This view helps assess whether the cluster is (i) sheet-like (narrow across-trend), (ii) vertically extensive, and (iii) internally segmented.

### 4.5 Temporal evolution (optional diagnostic)
If pick times are absolute (UNIX/UTC) or relative seconds, depth vs origin time is plotted in:

- `images/fig_time_depth.png`

This is a quick-look diagnostic for migration (e.g., down-dip growth or along-strike propagation). Interpretation should be cautious because origin times are co-estimated with location and the constant-velocity model can imprint systematic biases.

## 5. Validation, limitations, and recommended next steps
### 5.1 Validation performed
- **Velocity sensitivity (coarse):** The velocity scan (`images/fig_velocity_scan.png`) demonstrates that misfit has a preferred constant \(V_P\) in the tested range for the subset of well-recorded events.
- **Residual QC:** RMS and its dependence on pick count (`images/fig_misfit_qc.png`) provide a basic reliability screen.
- **Noise handling:** DBSCAN explicitly labels sparse/outlier points as noise, reducing the chance of forcing all events into clusters.

### 5.2 Key limitations
- **1-D constant velocity:** Real sites typically require layered/anisotropic velocity; constant \(V_P\) can bias depth and along-array positioning.
- **P-only picks:** Without S picks (or a calibrated velocity model), depth is generally less constrained and can trade off with origin time.
- **No explicit pick uncertainty:** All picks were weighted equally; in practice, phase quality, SNR, and timing error should be incorporated.
- **No formal location uncertainty propagation:** The script reports a linearized covariance estimate; a full assessment would use bootstrap resampling of picks/stations or a Bayesian posterior.

### 5.3 Recommended next steps (to strengthen structural inference)
1. **Add an S phase (or amplitude) dataset** if available to improve depth constraints and check \(V_P/V_S\).
2. **Use a layered velocity model** (or station corrections) and compare resulting cluster planes/strikes.
3. **Uncertainty quantification:** bootstrap pick subsets and map confidence ellipsoids; retain only clusters robust to uncertainty.
4. **Integrate structural data:** compare inferred cluster strikes/dips with mapped faults, borehole image logs, or local stress orientation.

---

## Reproducibility
All results are generated by `code/microseismic_analysis.py`. Key outputs:

- `outputs/located_events.csv` — all located events with misfit and uncertainty proxies
- `outputs/good_events_with_clusters.csv` — QC-filtered events with DBSCAN cluster labels
- `outputs/cluster_summary.csv` — cluster-level structural summaries
- Figures in `report/images/`
