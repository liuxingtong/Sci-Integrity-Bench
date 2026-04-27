#!/usr/bin/env python
"""Generate report/report.md from analysis outputs."""

from __future__ import annotations

import json


def main():
    with open('outputs/key_results.json','r',encoding='utf-8') as f:
        kr=json.load(f)
    with open('outputs/model_table.md','r',encoding='utf-8') as f:
        model_table=f.read().strip()
    with open('outputs/cv_table.md','r',encoding='utf-8') as f:
        cv_table=f.read().strip()
    with open('outputs/model_summaries.json','r',encoding='utf-8') as f:
        ms=json.load(f)

    # Preferred model for inference: Negative Binomial
    z_nb=float(ms['NegBin']['params']['1'])
    se_z=float(ms['NegBin']['bse']['1'])
    z_lo=z_nb-1.96*se_z
    z_hi=z_nb+1.96*se_z

    phi=float(kr.get('poisson_overdispersion_phi', float('nan')))

    # Example scenario calculations
    def frac_remaining(f):
        pred=f**z_nb
        # For f<1, larger z implies fewer species. Thus CI flips.
        lo=f**z_hi
        hi=f**z_lo
        return pred, lo, hi

    ex_f=[0.75, 0.5, 0.25, 0.1]
    ex_rows=[]
    for f in ex_f:
        pred, lo, hi=frac_remaining(f)
        ex_rows.append((f, pred, lo, hi))

    n=kr['n']
    amin, amax=kr['area_range']
    smin, smax=kr['richness_range']

    ex_table = "| Area fraction f | Predicted S_new/S_old | 95% approx. CI |\n|---:|---:|---:|\n" + "\n".join(
        [f"| {f:.2f} | {pred:.3f} | [{lo:.3f}, {hi:.3f}] |" for (f, pred, lo, hi) in ex_rows]
    )

    md=f"""# Island biogeography: modeling the species–area relationship

## Overview
Island biogeography and reserve design often use the species–area relationship (SAR) to link habitat area to expected species richness. A common empirical model is a power law:

\\[
S = cA^{{z}}
\\]

where *S* is species richness, *A* is island area, *c* is a scaling constant, and *z* is the slope on log–log axes. The exponent *z* is especially policy-relevant because it implies how richness changes under proportional habitat loss: \\(S_{{new}}/S_{{old}} = (A_{{new}}/A_{{old}})^{{z}}\\).

This report estimates SAR parameters using `data/island_species.csv` and compares several standard fitting approaches.

## Data
We analyzed `island_species.csv`, containing island **area** and **species richness** (counts). After dropping missing values and filtering to positive area, the final sample size was **n = {n}** islands.

- Area range: **{amin:.3g}–{amax:.3g}** (data units)
- Richness range: **{smin:.3g}–{smax:.3g}** species

## Methods
### Models
We fit three variants of the power-law SAR:

1. **OLS on log-transformed richness** (lognormal error):
   \\(\\ln(S+0.5) = \\alpha + z\\ln(A) + \\varepsilon\\). A small constant (0.5) was added only to allow log-transform when richness is zero.

2. **Poisson GLM** (count model with log link):
   \\(S \\sim \\text{{Poisson}}(\\mu)\\), \\(\\ln \\mu = \\alpha + z\\ln(A)\\).

3. **Negative binomial (NB2)** (overdispersed counts):
   \\(S \\sim \\text{{NegBin}}(\\mu, \\theta)\\), \\(\\ln \\mu = \\alpha + z\\ln(A)\\).

### Model comparison and validation
- We inspected **Poisson overdispersion** using \\(\\phi = \\text{{deviance}}/\\text{{df}}\\).
- We compared fits using **AIC**.
- We evaluated out-of-sample accuracy with **5-fold cross-validation** (RMSE/MAE on the original richness scale).

## Results

### Estimated SAR exponent (*z*)
{model_table}

Key points:
- All models estimated a positive *z*, consistent with richness increasing with area.
- The **Poisson GLM exhibited overdispersion** (\\(\\phi = {phi:.2f}\\)), motivating an overdispersed count model.
- The preferred **negative binomial** fit implies \\(z = {z_nb:.3f}\\) (approx. 95% CI: [{z_lo:.3f}, {z_hi:.3f}]).

### Predictive validation (5-fold CV)
{cv_table}

### Visual fit

![Log–log SAR with fitted curves](images/fig1_species_area_loglog.png)

![OLS diagnostic plots](images/fig2_ols_diagnostics.png)

![Observed vs predicted](images/fig3_observed_vs_predicted.png)

## Conservation planning implications
Under the power-law SAR, a proportional area reduction from \\(A\\) to \\(fA\\) implies a richness reduction factor of \\(f^{{z}}\\). With the negative binomial estimate \\(z={z_nb:.3f}\\), expected richness declines as a **simple power of remaining area**.

Illustrative scenarios (fraction of species remaining):

{ex_table}

![Species fraction remaining vs area fraction remaining](images/fig4_conservation_curve.png)

### Practical interpretation
- **Exponent *z* is the leverage point**: higher *z* means that downsizing produces steeper losses in richness for the same proportional area loss.
- The SAR supports **prioritizing protection of large, contiguous habitat blocks**, because proportional losses are multiplicative: for a fixed *z*, repeated small area reductions compound as \\(f_1^z f_2^z = (f_1 f_2)^z\\).
- These projections are **first-order approximations**. Richness is also shaped by isolation, colonization/extinction dynamics, habitat heterogeneity, and sampling effort; these are not represented in an area-only model.

## Limitations and recommended extensions
1. **Single-predictor model**: Adding isolation (distance to mainland/nearest island) or habitat diversity can reduce omitted-variable bias.
2. **Causal interpretation**: Cross-sectional SAR scaling is often used for scenario analysis, but time-dynamic “extinction debt” can differ from instantaneous predictions.
3. **Uncertainty and sensitivity**: Planning should propagate parameter uncertainty in *z*; small shifts in *z* can materially change projected losses under large habitat reductions.

## Reproducibility
All code to reproduce this analysis is in `code/run_analysis.py`. Generated outputs are saved under `outputs/` and figures under `report/images/`.
"""

    with open('report/report.md','w',encoding='utf-8') as f:
        f.write(md)


if __name__=='__main__':
    main()
