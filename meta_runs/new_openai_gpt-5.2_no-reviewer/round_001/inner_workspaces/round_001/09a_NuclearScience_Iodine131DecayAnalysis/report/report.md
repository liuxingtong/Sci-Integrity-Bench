# Flame speed dependence on chamber pressure in bench combustion experiments

## Abstract
Bench combustion experiments often produce paired measurements of chamber pressure and flame propagation speed. Using `data/flame_pressure_series.csv` (pressure in kPa, flame speed in cm/s), I fit and compared four common response forms—linear, quadratic polynomial, power-law, and exponential—then selected a parsimonious model using corrected Akaike Information Criterion (AICc) and leave-one-out cross-validated (LOOCV) RMSE. The resulting best-fit relation provides an engineering-ready parameterization for summary plots and interpolation across the tested pressure range, along with residual diagnostics to assess adequacy.

## 1. Data overview
The dataset consists of paired observations:

- **Predictor:** chamber pressure, \(P\) (kPa)
- **Response:** flame speed, \(v\) (cm/s)

Basic descriptive statistics and cleaning:

- Rows with missing values were removed (none retained in `outputs/cleaned_data.csv`).
- Data were sorted by pressure for plotting.

Key ranges and sample size are recorded in `outputs/summary.json`.

## 2. Modeling methodology
### 2.1 Candidate models
Four models were evaluated:

1. **Linear:** \(v = \beta_0 + \beta_1 P\)
2. **Quadratic:** \(v = \beta_0 + \beta_1 P + \beta_2 P^2\)
3. **Power law:** \(v = a P^b\)
4. **Exponential:** \(v = a\exp(bP)\)

Linear and quadratic models were fit by least squares. Power-law and exponential models were fit by nonlinear least squares (`scipy.optimize.curve_fit`) using log-linear regressions to initialize parameters.

### 2.2 Model comparison and selection
For each model, I computed:

- **RMSE** on the observed data
- **\(R^2\)** (variance explained)
- **AIC, AICc, BIC** assuming independent Gaussian residuals with variance estimated from SSE
- **LOOCV RMSE**: exact via hat-matrix for linear/quadratic; brute-force leave-one-out refits for nonlinear models

The **primary selector** was **AICc** (finite-sample penalty for extra parameters), with **LOOCV RMSE** used as a predictive cross-check.

### 2.3 Diagnostics and validation plots
To validate adequacy of the selected model, I generated:

- Scatter plot with all fitted curves
- Residuals vs fitted and residual Q–Q plot
- Observed vs predicted plot with 1:1 reference
- Log–log visualization (useful to assess power-like trends)

All figures are saved under `report/images/`.

## 3. Results
### 3.1 Model comparison
The following table summarizes fit and predictive performance (lower is better for RMSE/AICc):

<!-- model table generated from outputs/model_fits.csv -->

| model | rmse | loocv_rmse | r2 | aicc | equation |
|---|---|---|---|---|---|
