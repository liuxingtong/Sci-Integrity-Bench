"""Write report/report.md from analysis outputs.

Assumes code/run_analysis.py has been run and produced outputs/*.csv and report/images/*.png.
"""

from __future__ import annotations

from pathlib import Path
import pandas as pd

OUT_DIR = Path("outputs")
REPORT_PATH = Path("report/report.md")


def read_md(name: str) -> str:
    return (OUT_DIR / name).read_text(encoding="utf-8").strip() + "\n"


def main():
    overview_md = read_md("_overview_table.md")
    keycols_md = read_md("_keycols_table.md")
    summ_md = read_md("_summarystats_table.md")
    twfe_md = read_md("_twfe_table.md")

    # Key columns (for narrative)
    kc = pd.read_csv(OUT_DIR / "inferred_key_columns.csv").iloc[0].to_dict()

    # Data overview numbers
    ov = pd.read_csv(OUT_DIR / "data_overview.csv", header=None, names=["metric", "value"])
    ov_map = dict(zip(ov.metric, ov.value))

    # TWFE results (for highlights)
    twfe = pd.read_csv(OUT_DIR / "twfe_results.csv")
    # pick the irrigation and yield reduced-form rows
    irrig_row = twfe[twfe["model"].str.contains("irrig", case=False, na=False)].iloc[0].to_dict()
    y_rf_row = twfe[twfe["model"].str.contains("reduced", case=False, na=False)].iloc[0].to_dict()

    means = pd.read_csv(OUT_DIR / "means_by_enforcement_simple.csv")
    base_irrig = float(means.loc[means.group == "Not enforced", "irrig_mean"].iloc[0])
    base_yield = float(means.loc[means.group == "Not enforced", "yield_mean"].iloc[0])

    irrig_pct = 100 * irrig_row["coef_enforced"] / base_irrig
    yield_pct = 100 * y_rf_row["coef_enforced"] / base_yield

    txt = f"""# Groundwater quota enforcement and irrigation program outcomes: field–year panel evidence

## 1. Research question
Using a field–year panel, this analysis assesses whether **groundwater quota enforcement** is associated with changes in:
(i) **irrigation**, (ii) **yields**, and (iii) input adjustments (fertilizer), while accounting for **rainfall**.


## 2. Data
The unit of observation is a field-year. After minimal cleaning (dropping missing field ID or year), the analysis sample contains **{int(ov_map['n_rows_clean']):,}** field-year observations spanning **{int(ov_map['year_min'])}–{int(ov_map['year_max'])}** across **{int(ov_map['n_fields']):,}** fields.

### 2.1 Inferred key variables
Because the dataset is scenario-provided, the script infers the main variables by column-name heuristics and completeness. The inferred mapping is:

{keycols_md}

### 2.2 Sample diagnostics

{overview_md}

### 2.3 Summary statistics
Winsorized (1st/99th percentile) summary statistics by enforcement status:

{summ_md}


## 3. Methods
### 3.1 Descriptive panel plots
We first plot yearly averages for yield, irrigation, fertilizer, rainfall, and enforcement share, and compare mean yield/irrigation trends by contemporaneous enforcement status.

### 3.2 Two-way fixed effects (TWFE)
To estimate within-field changes when enforcement is active, we fit TWFE models of the form:

\[
Y_{{it}} = \beta \;\text{{Enforced}}_{{it}} + \Gamma X_{{it}} + \alpha_i + \lambda_t + \varepsilon_{{it}},
\]

where \(\alpha_i\) are **field fixed effects** and \(\lambda_t\) are **year fixed effects**. Standard errors are **clustered at the field level**.

- For irrigation, controls include rainfall (when available).
- For yields, controls include rainfall and fertilizer (when available).
- A supplementary specification adds irrigation as a covariate to describe whether yield changes are mediated by irrigation changes (not a causal mediation estimate).

### 3.3 Event-study around first enforcement
We define each treated field’s first enforcement year and estimate dynamic effects using event-time indicators from \(-5\) to \(+5\) years around adoption (baseline \(t=-1\)), with field and year fixed effects.


## 4. Results
### 4.1 Panel structure and raw trends
- Panel coverage and balance are shown in Figures 1–2.
- Yearly means and enforcement intensity are shown in Figure 3.
- Simple mean differences by contemporaneous enforcement are shown in Figure 4; these are not causal because fields may enter enforcement non-randomly.

**Figures**

- Panel coverage: `images/fig01_panel_coverage.png`
- Years-per-field distribution: `images/fig02_years_per_field.png`
- Yearly panel overview (yield/irrigation/fertilizer/rainfall/enforcement share): `images/fig03b_yearly_panel_overview.png`
- Mean yield & irrigation by enforcement status: `images/fig03_trends_yield_irrig_by_enforcement.png`

### 4.2 Mechanisms and relationships (descriptive)
- Irrigation is negatively related to rainfall in the cross-section (Figure 5), consistent with compensatory irrigation in drier conditions.
- Yield is positively related to irrigation (Figure 6).

- Irrigation vs rainfall: `images/fig04_scatter_irrig_rain.png`
- Yield vs irrigation: `images/fig05_scatter_yield_irrig.png`
- Correlation heatmap: `images/fig06_correlation_heatmap.png`

### 4.3 Main program impacts (TWFE)
Table 1 reports the enforced coefficient from TWFE regressions.

**Headline estimates (TWFE):**
- **Irrigation:** enforcement is associated with a change of **{irrig_row['coef_enforced']:.3f}** units (SE {irrig_row['se']:.3f}), which is **{irrig_pct:.2f}%** of the not-enforced mean irrigation.
- **Yield (reduced form):** enforcement is associated with a change of **{y_rf_row['coef_enforced']:.3f}** units (SE {y_rf_row['se']:.3f}), which is **{yield_pct:.2f}%** of the not-enforced mean yield.

**Table 1. Two-way fixed effects estimates**

{twfe_md}

Interpretation: the irrigation result is the primary “first-stage” program outcome; the yield effect summarizes net impacts after on-farm adjustments (input substitution, crop choice within field, timing, etc.) captured only imperfectly by observed covariates.

### 4.4 Dynamics: event-study evidence
Figure 7 plots event-study coefficients relative to the year before first enforcement (\(t=-1\)). Pre-period coefficients provide a visual diagnostic for differential pre-trends.

- Event-study (irrigation and yield): `images/fig07_event_study_irrig_yield.png`
- Adoption timing (treated fields): `images/fig09_first_enforcement_year_hist.png`

### 4.5 Heterogeneity in drought years
To test whether yield impacts are concentrated in drier conditions, we interact enforcement with a drought indicator (lowest rainfall tercile in the pooled distribution). Figure 8 summarizes the interaction coefficient.

- Yield heterogeneity by drought: `images/fig08_yield_heterogeneity_drought.png`


## 5. Discussion
### 5.1 What worked?
Across specifications, enforcement is most directly expected to affect **irrigation** (water application). A statistically and economically meaningful irrigation response is consistent with binding quotas and/or improved monitoring.

### 5.2 Why might yields move less than irrigation?
Even when enforcement reduces irrigation, yields may be partially protected by:
- input substitution (e.g., fertilizer timing/rates),
- improved irrigation efficiency,
- shifts to less water-intensive varieties,
- favorable rainfall realizations.

Conversely, in drought years (low rainfall), a binding constraint on irrigation can translate more strongly into yield losses; the interaction analysis provides a targeted check of this mechanism.

### 5.3 Identification limitations
These estimates are associational under standard panel assumptions:
- TWFE identifies effects from within-field changes in enforcement status; if enforcement is triggered by time-varying unobservables (e.g., declining groundwater that also affects productivity), estimates may be biased.
- The event-study is informative about dynamics and pre-trends but can still be affected by policy endogeneity and staggered-adoption TWFE concerns.


## 6. Reproducibility
All results are generated by:
- `code/run_analysis.py` (data processing, figures, regressions)
- `code/write_report.py` (this report)

Key outputs are saved under `outputs/` and figures under `report/images/`.
"""

    REPORT_PATH.write_text(txt, encoding="utf-8")


if __name__ == "__main__":
    main()
