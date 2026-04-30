#!/usr/bin/env python
"""Render report/report.md from analysis artifacts."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def to_md_table(df: pd.DataFrame) -> str:
    cols = df.columns.tolist()
    out = []
    out.append("| " + " | ".join(cols) + " |")
    out.append("|" + "|".join(["---"] * len(cols)) + "|")
    for _, r in df.iterrows():
        vals = []
        for c in cols:
            v = r[c]
            if isinstance(v, float):
                # consistent significant figures for metrics
                if c in {"rmse", "loocv_rmse"}:
                    vals.append(f"{v:.3g}")
                elif c in {"r2"}:
                    vals.append(f"{v:.4f}")
                elif c in {"aicc"}:
                    vals.append(f"{v:.2f}")
                else:
                    vals.append(f"{v:.3g}")
            else:
                vals.append(str(v).replace("|", "\\|"))
        out.append("| " + " | ".join(vals) + " |")
    return "\n".join(out)


def main():
    summary = json.loads((ROOT / "outputs" / "summary.json").read_text())
    fits = pd.read_csv(ROOT / "outputs" / "model_fits.csv")

    # Compact comparison table
    table_df = fits[["model", "rmse", "loocv_rmse", "r2", "aicc", "equation"]].copy()
    md_table = to_md_table(table_df)

    best = json.loads((ROOT / "outputs" / "best_model.json").read_text())

    content = f"""# Flame speed dependence on chamber pressure in bench combustion experiments

## Abstract
Bench combustion experiments often produce paired measurements of chamber pressure and flame propagation speed. Using `data/flame_pressure_series.csv` (pressure in kPa, flame speed in cm/s), I fit and compared four common response forms—linear, quadratic polynomial, power-law, and exponential—then selected a parsimonious model using corrected Akaike Information Criterion (AICc) and leave-one-out cross-validated (LOOCV) RMSE. The selected relation is intended for engineering summaries and interpolation across the tested pressure range, and is accompanied by uncertainty visualization and residual diagnostics.

## 1. Data overview
The dataset contains **n = {summary['n']}** paired observations of:

- **Chamber pressure,** $P$ (kPa)
- **Flame speed,** $v$ (cm/s)

After dropping rows with missing values (if any) and sorting by pressure, the observed ranges were:

- $P \in [{summary['pressure_kPa_min']:.3g},\ {summary['pressure_kPa_max']:.3g}]$ kPa
- $v \in [{summary['flame_speed_cm_s_min']:.3g},\ {summary['flame_speed_cm_s_max']:.3g}]$ cm/s

A cleaned copy of the dataset used for modeling is saved as `outputs/cleaned_data.csv`.

## 2. Modeling methodology
### 2.1 Candidate models
Four models were evaluated:

1. **Linear:** $v = \beta_0 + \beta_1 P$
2. **Quadratic polynomial:** $v = \beta_0 + \beta_1 P + \beta_2 P^2$
3. **Power law:** $v = a P^b$
4. **Exponential:** $v = a\exp(bP)$

Linear and quadratic models were fit by ordinary least squares. Power-law and exponential models were fit by nonlinear least squares (`scipy.optimize.curve_fit`) with log-linear initialization.

### 2.2 Model scoring and selection
For each model I computed:

- **RMSE** on the observed dataset
- **$R^2$** (variance explained)
- **AICc** (primary selection criterion; finite-sample correction to AIC)
- **LOOCV RMSE** (predictive check; exact for linear/quadratic via hat-matrix; brute-force leave-one-out refits for nonlinear models)

AICc favors parsimonious models that still explain the data well, while LOOCV RMSE assesses out-of-sample predictive performance.

## 3. Results
### 3.1 Comparison across candidate models
The table below summarizes fit quality and predictive performance (lower is better for RMSE/AICc):

{md_table}

### 3.2 Selected model
The best model by AICc (with LOOCV as a cross-check) was:

- **Best model:** `{best['model']}`
- **Equation:** {summary['best_equation']}

Figure 1 overlays the data with all candidate fits, highlighting how alternative functional forms differ across the pressure range.

![Data and fitted candidate models](images/flame_speed_vs_pressure_models.png)

### 3.3 Uncertainty visualization (bootstrap band)
To provide an empirical sense of uncertainty in the fitted relationship, I constructed a **nonparametric paired bootstrap** (500 resamples). For each resample, the selected model was refit and predictions were computed on a dense pressure grid. The resulting pointwise 2.5%–97.5% quantiles form an uncertainty band.

![Best model with 95% bootstrap uncertainty band](images/best_model_with_uncertainty_band.png)

The bootstrap band is saved as `outputs/best_model_bootstrap_band.csv`.

### 3.4 Diagnostics and validation plots
Residual diagnostics for the selected model are shown in Figure 3. The residual-vs-fitted panel is used to check for systematic curvature or variance changes, while the Q–Q plot assesses normality as a rough check (important mainly if one wishes to attach parametric confidence intervals).

![Residual diagnostics for the selected model](images/best_model_residual_diagnostics.png)

A direct observed-vs-predicted comparison (Figure 4) summarizes predictive alignment and potential bias.

![Observed vs predicted, selected model](images/observed_vs_predicted_best_model.png)

Finally, a log–log visualization (Figure 5) is included because pressure–flame-speed relationships are often approximately power-like over limited ranges.

![Log–log visualization with best-fit curve](images/loglog_flame_speed_vs_pressure.png)

## 4. Discussion
Across the evaluated functional forms, the model selection criteria (AICc and LOOCV RMSE) identify a single preferred pressure–flame-speed relationship for the tested regime. In practical engineering use, this fitted curve can support:

- smooth interpolation of flame speed across the measured pressure range,
- generating summary plots with consistent parameterization,
- comparing runs or configurations by differences in fitted parameters or curves.

**Limitations.** (i) The fitted relationship is empirical and should not be extrapolated beyond the observed pressure range without additional validation. (ii) The analysis assumes independent measurement errors; if data come from repeated trials at the same pressure, a hierarchical or weighted model could be more appropriate. (iii) Uncertainty bands are pointwise bootstrap intervals and do not guarantee simultaneous coverage.

**Recommended next steps.** If additional metadata are available (mixture fraction, temperature, equivalence ratio, turbulence intensity), extend the model to a multivariate form or stratify by condition to separate pressure effects from other drivers.

## 5. Reproducibility
All analysis is reproducible from the workspace.

- Run the full analysis and regenerate figures:

```bash
python code/analyze.py
```

- Regenerate this report from artifacts:

```bash
python code/render_report.py
```
"""

    out_path = ROOT / "report" / "report.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
