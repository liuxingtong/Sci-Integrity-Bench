# Huangtupo site chronology from eight radiocarbon assays (F\u00b9\u2074) and stratigraphic context

## Overview
This report derives conventional radiocarbon ages (\u00b9\u2074C years BP) and calibrated calendar-age estimates for eight Huangtupo assays provided as fraction modern carbon (*F*\u00b9\u2074; `f14_residual_ratio`) with 1\u03c3 uncertainties. It then integrates these absolute estimates with the recorded stratigraphic units to sketch a relative site sequence and a coarse cultural periodization.

**Inputs**
- `data/radiocarbon_measurements.csv` (8 assays; sample IDs, materials, stratigraphic units, notes)
- `data/analysis_spec.txt` (conversion specification from *F*\u00b9\u2074 to conventional age)

**Key outputs**
- Derived table: `outputs/huangtupo_derived_dates.csv`
- Calibration grid: `outputs/huangtupo_calibration_grid.parquet` (or CSV fallback)
- Figures: `report/images/fig1_conventional_ages.png`, `fig2_calibrated_distributions.png`, `fig3_stratigraphy_vs_age.png`

## Methods

### 1) *F*\u00b9\u2074 \u2192 conventional radiocarbon age
Following the analysis specification, conventional radiocarbon age was computed from fraction modern carbon (*F*\u00b9\u2074) using the standard Libby-mean-life formulation:

\[
\text{Age}_{14\text{C}}\,(\text{BP}) = -8033\,\ln(F^{14})
\]

Uncertainty propagation used first-order error propagation:

\[
\sigma_{\text{Age}} = 8033\,\frac{\sigma_{F^{14}}}{F^{14}}
\]

where 8033 years is the conventional mean life corresponding to the Libby half-life (5568 years).

### 2) Calibration to calendar years
Each conventional age (BP \u00b1 1\u03c3) was calibrated against **IntCal20** using the `pyradiocarbon` package (probability grid over calibrated age in **cal BP**, i.e., years before 1950).

To summarize (potentially multimodal) calibrated distributions, we report:
- **Median** and mean calibrated age (cal BP)
- **68.27%** and **95.45%** highest-posterior-density (HPD) regions computed from the discrete calibration grid by selecting the set of calendar-year bins with the greatest probability mass until the target probability was reached, then merging contiguous bins into one or more intervals.

For readability, calibrated ages are also expressed as **BCE/CE** years using:
\[
\text{year} = 1950 - \text{calBP}
\]
with conversion to the historical BCE/CE system (no year 0).

### 3) Stratigraphic ordering (relative chronology)
A simple heuristic parser extracted a numeric ordering key from each `stratigraphic_unit` label when possible (e.g., \"Layer 3\" \u2192 3). The working assumption is that **higher layer numbers represent deeper/older deposits** (a common but not universal convention). This was used only to visualize stratigraphic\u2013chronometric consistency; interpretations below prioritize the recorded unit descriptions and the calibrated dates.

### 4) Periodization sketch
A coarse, China-wide period label was assigned based on the **median** calibrated year (BCE/CE). These labels are intentionally broad (e.g., \"Zhou period\") and should be refined using local ceramic/feature typologies.

## Results

### Assay-level conventional ages and calibrated ranges
Table 1 lists the computed conventional ages and calibrated calendar summaries. Across the eight assays, conventional ages span **~650\u20134630 \u00b9\u2074C years BP**, and median calibrated ages span **~640\u20135330 cal BP** (IntCal20), implying a long or multi-component chronology rather than a single short occupation.

**Table 1. Eight Huangtupo assays: *F*\u00b9\u2074, conventional ages, and calibrated calendar ranges (IntCal20).**

(Conventional ages are reported in \u00b9\u2074C years BP; calibrated ranges are reported as HPD regions in BCE/CE.)


{{TABLE_ASSAYS}}

### Visual summaries

**Figure 1** shows conventional radiocarbon ages with 1\u03c3 error bars.

![](images/fig1_conventional_ages.png)

**Figure 2** shows calibrated probability distributions (IntCal20) stacked by sample.

![](images/fig2_calibrated_distributions.png)

**Figure 3** compares stratigraphic ordering (heuristically parsed from unit labels) to median calibrated age; departures from monotonicity indicate potential stratigraphic mixing, residuality, or sample-specific biases (e.g., inbuilt age for wood/charcoal).

![](images/fig3_stratigraphy_vs_age.png)

### Stratigraphic synthesis
Grouping assays by their recorded stratigraphic units provides a first-pass relative sequence (Table 2). Units with older median calibrated ages are interpreted as earlier phases, subject to stratigraphic superposition.

**Table 2. Calibrated median ages summarized by stratigraphic unit.**

{{TABLE_STRAT}}

## Discussion

### 1) Absolute timeline and internal consistency
Across the eight assays, the calibrated estimates span multiple centuries/millennia (see Table 1 and Fig. 2), indicating either (i) a multi-period occupational history at Huangtupo, and/or (ii) incorporation of residual materials into later contexts.

Two consistency checks are informative:
1. **Conventional vs. calibrated ordering.** As expected, older conventional ages generally map to older calibrated ages, but the calibration curve introduces non-linearities and (sometimes) multimodal ranges.
2. **Stratigraphy vs. dates.** Where stratigraphic unit numbering could be parsed, Fig. 3 provides a quick assessment of reversals. Any cases where a deeper unit yields a younger calibrated median (or vice versa) should be treated as candidates for post-depositional disturbance, redeposition, or sample-specific offsets.

Because the assay set is small (n=8) and materials may differ in susceptibility to inbuilt age (e.g., wood/charcoal vs. short-lived seeds), the preferred interpretive stance is to regard the calibrated distributions as **terminus post quem** (TPQ) indicators unless short-lived material is explicitly confirmed.

### 2) Relative chronology from stratigraphic context
Even without a full Harris matrix, the stratigraphic_unit metadata supports a relative ordering. The unit-level summary (Table 2) should be read alongside the excavation notes:
- **Multiple assays within a unit** that agree within uncertainty strengthen that unit\u2019s placement.
- **Single-assay units** are inherently weaker; if such an assay is from wood/charcoal, its calibrated age may pre-date the associated activity (\"old wood\" effect).

Where date\u2013stratigraphy mismatches are observed, targeted follow-up could include:
- preferential dating of short-lived plant remains or articulated bone collagen (if preservation allows)
- replicate dating across the same feature/context
- explicit Bayesian modeling of a stratigraphic sequence (e.g., Phase/Sequence models) if additional assays become available

### 3) Cultural periodization (sketch)
Using the **median** calibrated date for each assay, we assigned broad period labels (Table 1). This is a *sketch* intended to guide discussion rather than replace artifact-based cultural attribution.

A practical way to use these results in site interpretation is to define provisional phases such as:
- **Early phase(s):** assays whose 95% HPD ranges fall wholly within the earlier part of the overall distribution (older cal BP; earlier BCE)
- **Middle phase(s):** assays clustering in an intermediate window
- **Late phase(s):** assays with young medians/ranges (later BCE to CE)

These chronometric phases should then be cross-tabulated against ceramics, architecture, and feature types recorded for each stratigraphic unit.

## Limitations
- **Calibration dependence:** results are conditional on IntCal20 and the calibration implementation.
- **Material effects:** without explicit short-lived vs. long-lived identification, some dates may be older than the target event.
- **Stratigraphic parsing heuristic:** numeric extraction from unit labels may not reflect true superposition if the labeling scheme is non-ordinal.

## Reproducibility
All computations and figures are generated by `code/run_analysis.py` from the provided input CSV. Derived outputs are saved under `outputs/` and figures under `report/images/`.
