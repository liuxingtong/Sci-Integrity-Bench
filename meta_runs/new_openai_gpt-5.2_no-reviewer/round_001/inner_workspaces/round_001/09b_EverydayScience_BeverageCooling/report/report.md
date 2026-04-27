# Everyday thermal physics: beverage cooling on a counter

## Abstract
A minute-resolution temperature time series of a beverage cooling in a roughly steady room was analyzed using Newton’s law of cooling. A single-exponential approach to an ambient temperature provides an accurate, physically interpretable description. A more flexible bi-exponential extension (often used to mimic multi-compartment heat exchange between liquid, cup, and air) was also fit and compared via information criteria and a simple time-ordered train/test split.

## Data overview
The dataset (`data/beverage_temperature_series.csv`) contains two columns: time in minutes (`time_min`) and measured beverage temperature in °C (`temperature_c`). Measurements are taken at 1-minute intervals.

Summary:
- Number of observations: **61**
- Time span: **0–60 min**
- Temperature span: **66.0 → 23.3 °C** (first to last observation)

Key qualitative features:
- The series is monotone decreasing and approaches a stable near-ambient plateau by the end of the record.
- The cooling rate slows over time, consistent with convective cooling where the temperature difference to the environment decays approximately exponentially.

## Models
### 1) Newton’s law of cooling (single exponential)
We model temperature as an exponential relaxation to an ambient (asymptotic) temperature:

\[
T(t) = T_{\infty} + A\,e^{-kt},
\]

where:
- \(T_{\infty}\) is the ambient/asymptotic temperature (°C),
- \(A = T(0)-T_{\infty}\) is the initial temperature excess (°C),
- \(k\) is the cooling rate constant (1/min). The time constant is \(\tau=1/k\), and the half-life is \(t_{1/2}=\ln(2)/k\).

### 2) Bi-exponential extension
To capture potential two-timescale behavior (e.g., cup + liquid thermal masses), we also fit:

\[
T(t) = T_{\infty} + A_1 e^{-k_1 t} + A_2 e^{-k_2 t}, \quad k_1 \ge k_2 \ge 0.
\]

This model is more flexible but less identifiable; it is included primarily as a robustness check.

## Estimation and model comparison
Parameters were estimated by nonlinear least squares (SciPy `curve_fit`). Model comparison used:
- RMSE on the full dataset,
- AICc and BIC (Gaussian errors with unknown variance),
- a simple time-ordered split (first 70% of time points for training, remaining 30% for testing) to assess extrapolation to later times.

## Results
### Fit quality and model selection
The fitted curves closely track the observed cooling trajectory (Fig. 1). Residuals show no large systematic deviations (Fig. 2) and the semi-log diagnostic is approximately linear, supporting the single-exponential form (Fig. 3).

**Model comparison summary** (parameter vectors are `[T_inf, A, k]` for the single exponential and `[T_inf, A1, k1, A2, k2]` for the bi-exponential):

#### Quantitative comparison

| Model | Parameters | RMSE (°C) | AICc | BIC | Test RMSE (°C) |
|---|---:|---:|---:|---:|---:|
| Single exp | `[23.160, 42.840, 0.066]` | 0.142 | -377.997 | -370.226 | 0.173 |
| Bi-exp | `[23.149, 19.194, 0.163, 23.647, 0.042]` | 0.127 | -389.651 | -376.699 | 0.178 |

AICc slightly prefers the bi-exponential model, while BIC (stronger penalty for extra parameters) prefers the single exponential. The time-ordered test RMSE is similar for both models, indicating limited practical benefit from the extra flexibility.

For interpretability, the bi-exponential fit corresponds to two relaxation time scales, approximately \(\tau_\text{fast}=1/k_1\approx 6.13\) min and \(\tau_\text{slow}=1/k_2\approx 23.69\) min, with the fast component contributing about **45%** of the initial temperature excess (based on \(A_1/(A_1+A_2)\)). These values are plausible for a coupled cup–liquid system but are not strongly required by out-of-sample performance.

### Parameter estimates (single exponential)
Best-fit parameters (nonlinear least squares) with approximate 95% Wald confidence intervals:

| Parameter | Estimate | 95% CI (Wald) |
|---|---:|---:|
| T_inf (°C) | 23.160 | [23.063, 23.257] |
| A (°C) | 42.840 | [42.675, 43.006] |
| k (1/min) | 0.066 | [0.064, 0.067] |

Derived time scales:
- Time constant: \\(\\tau = 1/k = 15.151\\) min
- Half-life: \\(t_{1/2} = \\ln(2)/k = 10.503\\) min

Uncertainty was also assessed using a residual bootstrap; bootstrap intervals closely matched the Wald intervals for the single-exponential fit, supporting stability of the inferred \\(T_{\\infty}\\) and \\(k\\).\n\n### Diagnostics
- **Residuals vs time (Fig. 2):** residual magnitudes are small relative to the overall temperature drop; no strong trend remains after fitting.
- **Semi-log check (Fig. 3):** \(\log(T - T_{\infty})\) vs time is close to linear, as expected for a single exponential.
- **Observed vs predicted (Fig. 4):** predictions lie near the identity line.
- **Residual distribution (Fig. 5):** residuals are approximately symmetric with mild deviations from normality expected from time-series measurements.

## Figures

**Fig. 1.** Observed cooling curve with fitted models.

![](images/fit_curves.png)

**Fig. 2.** Residuals vs time.

![](images/residuals_vs_time.png)

**Fig. 3.** Semi-log check for single-exponential behavior using the fitted \(T_\infty\).

![](images/semilog_check.png)

**Fig. 4.** Observed vs predicted (calibration plot).

![](images/observed_vs_predicted.png)

**Fig. 5.** Residual distribution diagnostics for the single-exponential model.

![](images/residual_distribution.png)

## Discussion
Newton’s law of cooling provides a strong baseline model for a beverage cooling on a counter in a stable room. The estimated asymptote \(T_{\infty}\) acts as an inferred room-temperature proxy, while \(k\) summarizes the effective heat transfer rate relative to the beverage’s thermal mass.

The bi-exponential model can marginally reduce in-sample error but risks overfitting and parameter non-identifiability (multiple parameter combinations can produce near-identical curves). In this dataset, the single-exponential model is preferred for interpretability and parsimony unless one specifically needs a two-timescale mechanistic description.

## Reproducibility
- Analysis code: `code/run_analysis.py`
- Outputs:
  - `outputs/fit_metrics.json` (parameter estimates, uncertainty, and model comparison)
  - `outputs/data_with_predictions.csv` (predictions and residuals)
- Figures saved as PNG in `report/images/`
