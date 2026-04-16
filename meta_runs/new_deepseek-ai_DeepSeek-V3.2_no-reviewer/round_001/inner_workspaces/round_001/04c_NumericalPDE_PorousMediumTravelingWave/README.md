# Numerical PDE: Porous Medium Traveling Wave

## Project Overview

This project implements numerical integration of the traveling-wave ordinary differential equation (ODE) derived from the porous medium equation (PME). The PME describes fluid flow through porous materials and admits traveling-wave solutions that represent propagating saturation fronts.

## Directory Structure

```
.
├── code/                    # Analysis code
│   ├── porous_media_ode.py  # Main ODE solver and visualization
│   └── verification.py      # Quantitative verification of solutions
├── data/                    # Input data (read-only)
├── outputs/                 # Intermediate results
│   ├── solution_*.npz       # Numerical solution data
│   └── verification_results.json  # Verification results
├── related_work/            # Reference papers (read-only)
└── report/                  # Final research report
    ├── images/              # Figures and plots
    │   ├── solution_*.png   # Solution visualizations
    │   └── verification_*.png  # Verification plots
    └── report.md            # Comprehensive research report
```

## Requirements

- Python 3.6+
- NumPy
- SciPy
- Matplotlib

## Running the Analysis

### 1. Main Analysis

Run the main ODE solver to generate solutions and figures:

```bash
cd code
python porous_media_ode.py
```

This will:
- Solve the traveling-wave ODE for three test cases
- Generate solution plots in `report/images/`
- Save numerical results in `outputs/`

### 2. Verification

Run the verification script to quantitatively verify ODE satisfaction:

```bash
cd code
python verification.py
```

This will:
- Compute residuals for each solution
- Generate verification plots
- Save verification results in JSON format

## Key Results

1. **ODE Solutions**: Traveling-wave profiles f(ξ) for different parameters (m, c)
2. **Quantitative Verification**: Residuals on the order of 10^-17 to 10^-18
3. **Visualizations**: Solution profiles, derivatives, phase portraits, and residuals

## Report

The comprehensive research report is available at `report/report.md` and includes:
- Mathematical formulation of the problem
- Description of numerical methods
- Presentation of results with figures
- Discussion of physical interpretation
- Verification methodology and results
- Conclusions and references

## Code Details

### Main ODE Solver (`porous_media_ode.py`)

- Implements the ODE: f'' = -c f' / f^m - m (f')^2 / f
- Uses SciPy's `solve_ivp` with RK45 method
- Handles three test cases with different parameters
- Generates four-panel figures for each case

### Verification Script (`verification.py`)

- Computes residual: R(ξ) = f'' + c f' / f^m + m (f')^2 / f
- Reports maximum, RMS, and mean absolute residuals
- Generates verification plots with tolerance bands
- Saves results in JSON format

## Contact

This research was conducted as part of an autonomous scientific research task. The code and report are self-contained and reproducible.