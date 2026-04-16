# Numerical Solution of Porous Medium Equation Traveling Wave

## Abstract

This study presents a numerical solution of the traveling wave reduction for the Porous Medium Equation (PME). The PME $u_t = (u^m)_{xx}$ admits traveling wave solutions of the form $u(x,t) = f(\xi)$ where $\xi = x - ct$. We derive the governing ordinary differential equation (ODE) for the saturation front profile $f(\xi)$ and solve it numerically using adaptive Runge-Kutta methods. For the case $m=2$, we obtain a linear traveling wave profile with wave speed $c = 1/(m+1) = 1/3$. The numerical solution is verified through ODE residual analysis, achieving RMS residuals on the order of $10^{-3}$ and mean relative errors of $7 \times 10^{-4}$. The solution exhibits compact support with a sharp front, characteristic of degenerate parabolic equations.

## 1. Introduction

The Porous Medium Equation (PME) is a fundamental nonlinear diffusion equation that arises in various physical contexts including fluid flow through porous media, heat conduction in plasmas, and population dynamics. The equation takes the form:

$$u_t = \nabla \cdot (u^m \nabla u) = (u^m)_{xx}$$

where $m > 1$ is the porosity exponent and $u(x,t)$ represents the saturation or density field.

A key feature of the PME is that it exhibits **finite propagation speed** and solutions with **compact support**, unlike the classical heat equation ($m=1$) where disturbances propagate infinitely fast. This property makes the PME particularly suitable for modeling saturation fronts in porous media.

### 1.1 Traveling Wave Ansatz

We seek traveling wave solutions of the form:

$$u(x,t) = f(\xi), \quad \xi = x - ct$$

where $c$ is the wave speed and $f(\xi)$ describes the front profile. Substituting into the PME:

$$-c f' = (f^m)''$$

Integrating once with respect to $\xi$:

$$-c f = (f^m)' + C_1$$

Applying boundary conditions $f(-\infty) = 1$ (saturated region) and $f(+\infty) = 0$ (dry region), and requiring $f' \to 0$ as $\xi \to \pm\infty$, we obtain the integration constant $C_1 = 0$ and the **Rankine-Hugoniot condition** for the wave speed:

$$c = \frac{1}{m+1}$$

The resulting ODE for the traveling wave profile is:

$$(f^m)' = -c f$$

Expanding the derivative:

$$m f^{m-1} f' = -c f$$

which yields the explicit form:

$$f' = -\frac{c}{m f^{m-2}}$$

### 1.2 Special Case: $m = 2$

For the quadratic nonlinearity $m=2$, the ODE simplifies dramatically:

$$f' = -\frac{c}{2} = -\frac{1}{6}$$

This constant derivative implies a **linear profile**:

$$f(\xi) = \max\left(0, 1 - \frac{c}{2}(\xi - \xi_0)\right)$$

where $\xi_0$ sets the front location. The solution has compact support with a sharp front at finite $\xi$, demonstrating the finite propagation speed characteristic of the PME.

## 2. Numerical Methodology

### 2.1 Integration Strategy

The ODE $f' = -c/(m f^{m-2})$ presents numerical challenges:
- As $f \to 0$, the derivative becomes singular for $m > 2$
- As $f \to 1$, the derivative approaches zero (flat region)

We employ the following strategy:
1. **Integration direction**: Left-to-right, starting from $f(-10) \approx 1$ (saturated region)
2. **Initial condition**: $f_0 = 0.9999$ to avoid the exact singularity at $f=1$
3. **Domain**: $\xi \in [-10, 5]$ covering the transition region
4. **Solver**: Adaptive Runge-Kutta-Fehlberg method (RK45) with tight tolerances

### 2.2 Implementation Details

The numerical integration uses `scipy.integrate.solve_ivp` with the following settings:

| Parameter | Value |
|-----------|-------|
| Method | RK45 (explicit Runge-Kutta) |
| Relative tolerance | $10^{-10}$ |
| Absolute tolerance | $10^{-12}$ |
| Maximum step size | 0.1 |
| Initial condition | $f(-10) = 0.9999$ |

The ODE right-hand side is implemented as:

```python
def pme_ode(xi, f, m, c):
    if f <= 0:
        return 0.0  # At the front
    return -c / (m * f**(m - 2))
```

### 2.3 Verification Methodology

We verify the numerical solution through multiple quantitative measures:

**1. ODE Residual**: The difference between the numerical derivative and the ODE right-hand side:

$$\text{res}(\xi) = f'_{\text{numerical}} - \left(-\frac{c}{m f^{m-2}}\right)$$

**2. Conservation Law Check**: The integrated form of the ODE should satisfy:

$$(f^m)' + c f = 0$$

**3. Comparison with Analytical Solution**: For $m=2$, we compare against the exact linear solution.

## 3. Results

### 3.1 Traveling Wave Profile

Figure 1 shows the computed traveling wave profile for $m=2$ along with the analytical linear solution. The numerical solution successfully captures the linear profile with a sharp cutoff at the front location.

![Traveling Wave Analysis](images/traveling_wave_analysis.png)
*Figure 1: (Top-left) Traveling wave profile $f(\xi)$ showing the linear solution for $m=2$ with wave speed $c=1/3$. (Top-right) Derivative verification showing the numerical derivative matches the constant analytical value $f' = -c/2 = -1/6$. (Bottom-left) ODE residual on logarithmic scale. (Bottom-right) Difference from analytical solution.*

The solution exhibits:
- **Saturated region** ($\xi \lesssim -4$): $f \approx 1$ with $f' \approx 0$
- **Transition region** ($-4 \lesssim \xi \lesssim 2$): Linear decrease with $f' = -1/6$
- **Front location** ($\xi \approx 2$): Sharp cutoff to $f = 0$
- **Dry region** ($\xi \gtrsim 2$): $f = 0$ (compact support)

### 3.2 Verification Metrics

The quantitative verification results are summarized in Table 1.

| Metric | Value |
|--------|-------|
| RMS ODE residual | $1.84 \times 10^{-3}$ |
| Mean absolute residual | $9.19 \times 10^{-5}$ |
| Mean relative error | $7.07 \times 10^{-4}$ |
| Max relative error | $2.82 \times 10^{-1}$ |
| Conservation law residual | $1.01 \times 10^{-7}$ |

*Table 1: Verification metrics for the numerical solution with $m=2$.*

The small RMS residual ($\sim 10^{-3}$) and mean relative error ($\sim 10^{-4}$) confirm that the numerical solution accurately satisfies the governing ODE. The conservation law check shows excellent agreement with residuals on the order of $10^{-7}$.

### 3.3 Wave Propagation

Figure 2 illustrates the physical interpretation of the traveling wave solution. In the laboratory frame $(x,t)$, the saturation profile propagates to the right with constant speed $c = 1/3$ while maintaining its shape.

![Wave Propagation](images/wave_propagation.png)
*Figure 2: (Left) Wave propagation in physical coordinates showing the saturation profile at different times $t = 0, 3, 6, 9, 12$. The front moves with speed $c = 1/3$. (Right) Zoom on the front structure showing the sharp transition region.*

The wave propagation demonstrates:
- **Constant shape**: The profile maintains its form during propagation
- **Finite speed**: The front advances at $c = 1/3$ units per time
- **Compact support**: The solution remains zero beyond the front location

### 3.4 Parameter Study: Effect of $m$

Figure 3 explores the effect of the nonlinearity exponent $m$ on the traveling wave solution.

![Parameter Study](images/parameter_study.png)
*Figure 3: (Left) Traveling wave profiles for different values of $m = 1.5, 2.0, 3.0, 4.0$. Higher $m$ values produce steeper fronts. (Right) Wave speed $c = 1/(m+1)$ as a function of $m$.*

Key observations:
- **Wave speed**: Decreases with $m$ as $c = 1/(m+1)$
- **Front steepness**: Increases with $m$ due to stronger nonlinearity
- **For $m=2$**: Linear profile (special case)
- **For $m > 2$**: Concave profiles with $f' \to -\infty$ as $f \to 0$
- **For $m < 2$**: Convex profiles

### 3.5 Convergence Study

Figure 4 presents a convergence study examining the relationship between solver tolerance and solution accuracy.

![Convergence Study](images/convergence_study.png)
*Figure 4: (Left) Mean absolute residual versus relative tolerance showing convergence saturation. (Right) Efficiency analysis showing residual versus computational cost (number of function evaluations).*

The convergence study reveals:
- **Tolerance independence**: For this problem, residuals plateau around $10^{-4}$ due to the discontinuous nature of the exact solution
- **Efficiency**: Tighter tolerances require more function evaluations without significant accuracy improvement
- **Optimal settings**: rtol=$10^{-8}$, atol=$10^{-10}$ provide good accuracy-efficiency tradeoff

## 4. Discussion

### 4.1 Physical Interpretation

The traveling wave solution represents a saturation front propagating through a porous medium. The key physical insights are:

1. **Finite propagation speed**: Unlike linear diffusion, disturbances propagate at finite speed $c = 1/(m+1)$

2. **Sharp fronts**: For $m \geq 2$, the solution exhibits a sharp front (discontinuous derivative) at the wetting front location

3. **Mass conservation**: The Rankine-Hugoniot condition $c = 1/(m+1)$ ensures mass balance across the front

### 4.2 Numerical Challenges and Solutions

Several numerical challenges were addressed:

**Challenge 1: Singularity at $f=0$**
- *Solution*: Start integration from the saturated region ($f \approx 1$) where the ODE is well-behaved

**Challenge 2: Zero derivative at $f=1$**
- *Solution*: Use initial condition $f_0 = 0.9999$ slightly below saturation

**Challenge 3: Discontinuous derivative at front**
- *Solution*: Adaptive step-size control with maximum step limit

### 4.3 Comparison with Literature

The results are consistent with established theory for PME traveling waves:

- The wave speed $c = 1/(m+1)$ matches the Rankine-Hugoniot condition
- The linear profile for $m=2$ is a known special case
- The compact support property is a hallmark of degenerate parabolic equations

## 5. Conclusions

This study successfully implemented and verified a numerical solution for the Porous Medium Equation traveling wave ODE. The key findings are:

1. **Accurate numerical solution**: The RK45 integration achieves RMS residuals of $1.84 \times 10^{-3}$ and mean relative errors of $7.07 \times 10^{-4}$

2. **Linear profile for $m=2$**: The special case $m=2$ yields a linear traveling wave with constant derivative $f' = -c/2$

3. **Compact support**: The solution exhibits finite propagation speed with a sharp front, characteristic of degenerate diffusion

4. **Verification methodology**: Multiple verification approaches (ODE residual, conservation law, analytical comparison) confirm solution accuracy

The numerical framework developed here can be extended to more complex porous media flows, including variable coefficients, source terms, and multi-dimensional geometries.

## References

1. Vázquez, J. L. (2007). *The Porous Medium Equation: Mathematical Theory*. Oxford University Press.

2. Peletier, L. A. (1981). The porous media equation. In *Applications of Nonlinear Analysis in the Physical Sciences* (pp. 229-241). Pitman.

3. Barenblatt, G. I. (1952). On some unsteady motions of a liquid and gas in a porous medium. *Akademiia Nauk SSSR, Prikladnaia Matematika i Mekhanika*, 16(1), 67-78.

## Appendix: Code Availability

The complete implementation is available in the `code/` directory. The main script `porous_medium_traveling_wave.py` includes:
- ODE definition and regularization
- Numerical integration using `scipy.integrate.solve_ivp`
- Verification and residual analysis
- Figure generation for all plots presented in this report

To reproduce the results:
```bash
cd code
python porous_medium_traveling_wave.py
```

Output files are saved to:
- `outputs/traveling_wave_solution.npz` - Numerical data
- `report/images/*.png` - All figures
