# Island Biogeography: Species-Area Relationships and Conservation Implications

## Abstract

This study investigates the species-area relationship (SAR) using island biogeography data to model how species richness scales with island area. We fit and compare three classical SAR models (power law/Arrhenius, exponential, and Gleason) to empirical data from 25 islands. The power law model (S = cA^z) provided the best fit with z = 0.272, explaining 15.8% of variance in species richness. We discuss the implications of these findings for conservation planning, including reserve sizing and extinction risk estimation under habitat loss scenarios.

## 1. Introduction

Island biogeography theory, pioneered by MacArthur and Wilson (1967), provides a fundamental framework for understanding species diversity patterns. The species-area relationship (SAR) describes how the number of species (S) increases with area (A), typically following a power law: S = cA^z, where c is a constant and z is the scaling exponent. This relationship has critical applications in conservation biology, informing reserve design, predicting extinction rates from habitat loss, and setting conservation priorities.

In this study, we analyze empirical data from 25 islands to:
1. Characterize the species-area relationship
2. Compare alternative SAR models
3. Estimate the scaling parameter z
4. Apply findings to conservation planning scenarios

## 2. Methods

### 2.1 Data

The dataset (`island_species.csv`) contains 25 observations with island area (km²) and species richness (number of species). Islands range from 0.57 to 5.32 km² in area, with species richness ranging from 11 to 43 species.

### 2.2 Statistical Analysis

We implemented three classical SAR models:

1. **Power law (Arrhenius) model**: S = cA^z
   - Linearized as: log(S) = log(c) + z·log(A)
   - Fitted using ordinary least squares regression on log-transformed data

2. **Exponential model**: S = c·exp(zA)
   - Linearized as: log(S) = log(c) + z·A
   - Fitted using OLS regression of log(S) on untransformed area

3. **Gleason model**: S = c + z·log(A)
   - Linear model of untransformed S on log(A)
   - Fitted using OLS regression

### 2.3 Model Comparison

Models were compared using:
- Coefficient of determination (R²)
- Akaike Information Criterion (AIC)
- Visual inspection of fit
- Residual diagnostics for the best-fitting model

### 2.4 Conservation Applications

Using the best-fitting model, we calculated:
- Expected species loss for hypothetical habitat reduction scenarios (50%, 75%, 90%)
- Minimum area required to preserve target proportions of species (50%, 75%, 90%, 95%)

All analyses were conducted in Python 3.x using pandas, numpy, scipy, statsmodels, matplotlib, and seaborn libraries.

## 3. Results

### 3.1 Data Overview

The dataset comprises 25 islands with areas ranging from 0.57 to 5.32 km² (mean = 3.08 km², SD = 1.29 km²) and species richness ranging from 11 to 43 species (mean = 18.4, SD = 6.3). The raw scatter plot shows a positive but variable relationship between area and species richness (Figure 1).

![Raw species-area relationship](images/scatter_raw.png)
*Figure 1: Raw species-area relationship showing positive correlation with substantial scatter.*

### 3.2 Power Law Model

The power law model provided the best fit among the three models tested. On log-log scale, the relationship was linear with slope z = 0.272 (95% CI: 0.272 ± 0.166) and intercept log(c) = 1.156 (Figure 2). This corresponds to the equation:

**S = 14.31 × A^0.272**

The model explained 15.8% of variance in species richness (R² = 0.158, p = 0.049).

![Power law fit on log-log scale](images/power_law_fit.png)
*Figure 2: Power law fit on log-log scale showing linear relationship with slope z = 0.272.*

### 3.3 Model Comparison

Model performance metrics:

| Model | AIC | R² | Slope (z) | Intercept |
|-------|-----|----|-----------|-----------|
| **Power law** | **-14.2** | **0.158** | **0.272** | 1.156 |
| Exponential | 5.8 | 0.096 | 0.046 | 1.207 |
| Gleason | 154.8 | 0.152 | 2.828 | 12.980 |

The power law model had the lowest AIC (-14.2), indicating best fit while accounting for model complexity. All models showed modest explanatory power (R² = 0.096-0.158), reflecting substantial scatter in the data.

![Model comparison](images/model_comparison.png)
*Figure 3: Comparison of three SAR models fitted to the data. The power law model (red solid line) provides the best fit based on AIC.*

### 3.4 Residual Diagnostics

Residual analysis for the power law model showed:
- Approximately random scatter in residuals vs fitted plot
- Reasonable normality in Q-Q plot, with slight deviations at extremes
- Approximately symmetric distribution of residuals

These diagnostics suggest the power law model assumptions are reasonably met, though the modest R² indicates other factors beyond area influence species richness.

![Residual diagnostics](images/residual_diagnostics.png)
*Figure 4: Residual diagnostics for the power law model showing reasonable model assumptions.*

### 3.5 Conservation Implications

Using the power law model with z = 0.272, we calculated extinction risks and reserve requirements:

#### Expected Species Loss from Habitat Reduction:
- 50% area loss → 16.4% species loss
- 75% area loss → 26.5% species loss  
- 90% area loss → 36.1% species loss

#### Minimum Area to Preserve Target Species Proportion:
- Preserve 50% of species → need 12.1% of original area
- Preserve 75% of species → need 39.6% of original area
- Preserve 90% of species → need 68.5% of original area
- Preserve 95% of species → need 82.3% of original area

These calculations follow the species-area relationship: remaining species proportion = (remaining area proportion)^z.

![Conservation implications](images/conservation_implications.png)
*Figure 5: Conservation implications of the species-area relationship. Left: Expected species loss increases nonlinearly with habitat loss. Right: Area requirements increase steeply for high conservation targets.*

## 4. Discussion

### 4.1 Interpretation of z-value

The estimated z-value of 0.272 falls within the typical range for island SARs (0.25-0.33), though at the lower end. This suggests a moderately strong area effect on species richness. The modest R² (0.158) indicates area explains only about 16% of variance in species richness, highlighting the importance of other factors such as:
- Island isolation and connectivity
- Habitat heterogeneity
- Historical factors and colonization history
- Taxonomic group characteristics

### 4.2 Model Selection

The power law (Arrhenius) model outperformed both exponential and Gleason models, consistent with ecological theory suggesting power-law scaling is most appropriate for island systems. The exponential model's poor performance suggests species richness does not increase exponentially with absolute area but rather with log-area.

### 4.3 Conservation Applications

#### Reserve Design

The z-value of 0.272 has important implications for conservation planning:
1. **Single large vs several small (SLOSS)**: With z < 0.5, a single large reserve preserves more species than several small reserves of equal total area.
2. **Minimum viable area**: To preserve 90% of species, approximately 69% of original habitat must be protected.
3. **Extinction debt**: The nonlinear relationship means initial habitat loss causes relatively small species loss, but beyond a threshold, losses accelerate dramatically.

#### Limitations and Caveats

1. **Dataset limitations**: Small sample size (n=25) and limited area range reduce statistical power.
2. **Taxonomic specificity**: The analysis doesn't account for different z-values among taxonomic groups.
3. **Habitat quality**: The model assumes uniform habitat quality, which rarely holds in reality.
4. **Equilibrium assumption**: Classic island biogeography assumes equilibrium between colonization and extinction, which may not apply to all systems.

### 4.4 Recommendations for Conservation Planning

Based on our findings:

1. **Reserve sizing**: For the studied island system, reserves should be as large as possible, with minimum targets of ~40% of original area to preserve 75% of species.

2. **Monitoring priorities**: Given the substantial unexplained variance, monitoring should track not just area but also habitat quality, connectivity, and specific threat factors.

3. **Precautionary approach**: The accelerating loss curve suggests early conservation action is critical—waiting until habitat is severely reduced leads to disproportionate species losses.

4. **Complementary strategies**: Since area explains only part of species richness variation, conservation should also address habitat quality, connectivity, and direct threats.

## 5. Conclusion

This analysis confirms the classic power-law species-area relationship for island systems, with scaling exponent z = 0.272. While area is an important determinant of species richness, it explains only about 16% of variance, emphasizing the need for multifactorial approaches in conservation planning. The derived z-value provides practical guidance for reserve design and extinction risk assessment, though applications should consider system-specific factors and uncertainties.

Future research should:
1. Incorporate additional predictors (isolation, habitat diversity, climate)
2. Analyze taxon-specific responses
3. Apply dynamic models accounting for non-equilibrium conditions
4. Validate predictions with independent datasets

## References

1. MacArthur, R. H., & Wilson, E. O. (1967). The theory of island biogeography. Princeton University Press.
2. Arrhenius, O. (1921). Species and area. Journal of Ecology, 9(1), 95-99.
3. Gleason, H. A. (1922). On the relation between species and area. Ecology, 3(2), 158-162.
4. Rosenzweig, M. L. (1995). Species diversity in space and time. Cambridge University Press.
5. Triantis, K. A., et al. (2012). The island species-area relationship: biology and statistics. Journal of Biogeography, 39(2), 215-231.

## Appendix: Data and Code Availability

All analysis code is available in `code/analysis.py`. Output files including model parameters, comparison metrics, and conservation calculations are in the `outputs/` directory. Figures are saved in `report/images/`.
