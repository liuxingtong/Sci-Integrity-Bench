"""
Numerical Solution of Porous Medium Traveling Wave ODE
=======================================================

The porous medium equation: ∂u/∂t = ∂/∂x(D(u) ∂u/∂x)
For D(u) = u^m (m > 0), we seek traveling wave solutions u(x,t) = f(ξ)
where ξ = x - ct is the traveling wave coordinate.

Traveling wave reduction yields:
-c f' = (f^m f')'

This can be rewritten as a system of first-order ODEs:
f' = g / f^m
g' = -c g / f^m

where g = f^m f'

Author: AI Scientist
"""

import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt
import os

# Create output directories if they don't exist
os.makedirs('../outputs', exist_ok=True)
os.makedirs('../report/images', exist_ok=True)

# =============================================================================
# Model Definition
# =============================================================================

def porous_medium_ode(xi, y, m, c):
    """
    System of ODEs for porous medium traveling wave.
    
    Parameters:
    -----------
    xi : float
        Traveling wave coordinate
    y : array
        y[0] = f (saturation/profile)
        y[1] = g = f^m * f'
    m : float
        Porous medium exponent (m > 0)
    c : float
        Wave speed
    
    Returns:
    --------
    dydxi : array
        Derivatives [f', g']
    """
    f, g = y
    
    # Avoid division by zero
    if f <= 1e-12:
        return [0.0, 0.0]
    
    f_prime = g / (f ** m)
    g_prime = -c * g / (f ** m)
    
    return [f_prime, g_prime]


def porous_medium_ode_second_order(xi, y, m, c):
    """
    Second-order form of the ODE for verification.
    
    y[0] = f
    y[1] = f'
    
    From: -c f' = m f^(m-1) (f')^2 + f^m f''
    We get: f'' = -c f' / f^m - m (f')^2 / f
    """
    f, f_prime = y
    
    if f <= 1e-12:
        return [0.0, 0.0]
    
    f_double_prime = -c * f_prime / (f ** m) - m * (f_prime ** 2) / f
    
    return [f_prime, f_double_prime]


# =============================================================================
# Numerical Integration
# =============================================================================

def solve_traveling_wave(m, c, f0, g0, xi_span, n_points=1000):
    """
    Solve the porous medium traveling wave ODE.
    
    Parameters:
    -----------
    m : float
        Porous medium exponent
    c : float
        Wave speed
    f0 : float
        Initial value of f at xi_start
    g0 : float
        Initial value of g = f^m * f' at xi_start
    xi_span : tuple
        (xi_start, xi_end)
    n_points : int
        Number of evaluation points
    
    Returns:
    --------
    sol : OdeSolution
        Solution object from scipy.integrate.solve_ivp
    """
    xi_eval = np.linspace(xi_span[0], xi_span[1], n_points)
    
    # Event function to stop integration when f becomes too small
    def event_f_small(xi, y, m, c):
        return y[0] - 1e-10
    event_f_small.terminal = True
    event_f_small.direction = -1
    
    sol = solve_ivp(
        porous_medium_ode,
        xi_span,
        [f0, g0],
        args=(m, c),
        method='RK45',
        t_eval=xi_eval,
        events=event_f_small,
        rtol=1e-10,
        atol=1e-12
    )
    
    return sol


# =============================================================================
# Verification: Compute ODE Residual
# =============================================================================

def compute_residual(sol, m, c):
    """
    Compute the residual of the ODE for verification.
    
    The original ODE is: -c f' = (f^m f')'
    
    Residual = |(f^m f')' + c f'|
    
    Parameters:
    -----------
    sol : OdeSolution
        Solution object
    m : float
        Porous medium exponent
    c : float
        Wave speed
    
    Returns:
    --------
    residual : array
        Pointwise residual values
    max_residual : float
        Maximum residual
    mean_residual : float
        Mean residual
    """
    xi = sol.t
    f = sol.y[0]
    g = sol.y[1]  # g = f^m * f'
    
    # Compute f' from g
    f_prime = g / (f ** m)
    
    # Compute g' numerically
    g_prime = np.gradient(g, xi)
    
    # Residual: (f^m f')' + c f' = g' + c f' should be 0
    residual = np.abs(g_prime + c * f_prime)
    
    # Filter out points where f is very small (numerical issues)
    valid = f > 1e-8
    
    return residual, np.max(residual[valid]) if np.any(valid) else 0, np.mean(residual[valid]) if np.any(valid) else 0


def compute_second_order_residual(sol, m, c):
    """
    Compute residual using the second-order form.
    
    ODE: f'' + c f' / f^m + m (f')^2 / f = 0
    
    Residual = |f'' + c f' / f^m + m (f')^2 / f|
    """
    xi = sol.t
    f = sol.y[0]
    g = sol.y[1]
    
    # Compute f' and f''
    f_prime = g / (f ** m)
    f_double_prime = np.gradient(f_prime, xi)
    
    # Residual
    residual = np.abs(f_double_prime + c * f_prime / (f ** m) + m * (f_prime ** 2) / f)
    
    valid = f > 1e-8
    
    return residual, np.max(residual[valid]) if np.any(valid) else 0, np.mean(residual[valid]) if np.any(valid) else 0


# =============================================================================
# Main Analysis
# =============================================================================

def main():
    """
    Main analysis: solve the porous medium traveling wave ODE for various parameters.
    """
    print("="*70)
    print("Numerical Solution of Porous Medium Traveling Wave ODE")
    print("="*70)
    
    # Parameters
    results = {}
    
    # Case 1: m = 1 (linear diffusion, gives exponential solution)
    print("\n" + "-"*70)
    print("Case 1: m = 1 (Linear Diffusion)")
    print("-"*70)
    
    m1, c1 = 1.0, 1.0
    f0_1, g0_1 = 1.0, -0.5  # Initial conditions: f(0) = 1, f'(0) = -0.5/f^m = -0.5
    xi_span1 = (0, 10)
    
    sol1 = solve_traveling_wave(m1, c1, f0_1, g0_1, xi_span1)
    residual1, max_res1, mean_res1 = compute_residual(sol1, m1, c1)
    
    print(f"Parameters: m = {m1}, c = {c1}")
    print(f"Initial conditions: f(0) = {f0_1}, g(0) = {g0_1}")
    print(f"Integration span: ξ ∈ [{xi_span1[0]}, {xi_span1[1]}]")
    print(f"Number of points: {len(sol1.t)}")
    print(f"Max residual: {max_res1:.2e}")
    print(f"Mean residual: {mean_res1:.2e}")
    
    results['case1'] = {
        'm': m1, 'c': c1, 'sol': sol1,
        'max_residual': max_res1, 'mean_residual': mean_res1
    }
    
    # Case 2: m = 2 (typical porous medium)
    print("\n" + "-"*70)
    print("Case 2: m = 2 (Typical Porous Medium)")
    print("-"*70)
    
    m2, c2 = 2.0, 1.0
    f0_2, g0_2 = 1.0, -0.3
    xi_span2 = (0, 10)
    
    sol2 = solve_traveling_wave(m2, c2, f0_2, g0_2, xi_span2)
    residual2, max_res2, mean_res2 = compute_residual(sol2, m2, c2)
    
    print(f"Parameters: m = {m2}, c = {c2}")
    print(f"Initial conditions: f(0) = {f0_2}, g(0) = {g0_2}")
    print(f"Integration span: ξ ∈ [{xi_span2[0]}, {xi_span2[1]}]")
    print(f"Number of points: {len(sol2.t)}")
    print(f"Max residual: {max_res2:.2e}")
    print(f"Mean residual: {mean_res2:.2e}")
    
    results['case2'] = {
        'm': m2, 'c': c2, 'sol': sol2,
        'max_residual': max_res2, 'mean_residual': mean_res2
    }
    
    # Case 3: m = 3 (strongly nonlinear)
    print("\n" + "-"*70)
    print("Case 3: m = 3 (Strongly Nonlinear Porous Medium)")
    print("-"*70)
    
    m3, c3 = 3.0, 1.0
    f0_3, g0_3 = 1.0, -0.2
    xi_span3 = (0, 10)
    
    sol3 = solve_traveling_wave(m3, c3, f0_3, g0_3, xi_span3)
    residual3, max_res3, mean_res3 = compute_residual(sol3, m3, c3)
    
    print(f"Parameters: m = {m3}, c = {c3}")
    print(f"Initial conditions: f(0) = {f0_3}, g(0) = {g0_3}")
    print(f"Integration span: ξ ∈ [{xi_span3[0]}, {xi_span3[1]}]")
    print(f"Number of points: {len(sol3.t)}")
    print(f"Max residual: {max_res3:.2e}")
    print(f"Mean residual: {mean_res3:.2e}")
    
    results['case3'] = {
        'm': m3, 'c': c3, 'sol': sol3,
        'max_residual': max_res3, 'mean_residual': mean_res3
    }
    
    # Case 4: Different wave speed
    print("\n" + "-"*70)
    print("Case 4: m = 2, c = 2 (Faster Wave)")
    print("-"*70)
    
    m4, c4 = 2.0, 2.0
    f0_4, g0_4 = 1.0, -0.5
    xi_span4 = (0, 5)
    
    sol4 = solve_traveling_wave(m4, c4, f0_4, g0_4, xi_span4)
    residual4, max_res4, mean_res4 = compute_residual(sol4, m4, c4)
    
    print(f"Parameters: m = {m4}, c = {c4}")
    print(f"Initial conditions: f(0) = {f0_4}, g(0) = {g0_4}")
    print(f"Integration span: ξ ∈ [{xi_span4[0]}, {xi_span4[1]}]")
    print(f"Number of points: {len(sol4.t)}")
    print(f"Max residual: {max_res4:.2e}")
    print(f"Mean residual: {mean_res4:.2e}")
    
    results['case4'] = {
        'm': m4, 'c': c4, 'sol': sol4,
        'max_residual': max_res4, 'mean_residual': mean_res4
    }
    
    # =============================================================================
    # Generate Figures
    # =============================================================================
    
    print("\n" + "="*70)
    print("Generating Figures...")
    print("="*70)
    
    # Figure 1: Traveling wave profiles for different m values
    fig1, ax1 = plt.subplots(figsize=(10, 6))
    
    for case_name, data in [('case1', results['case1']), ('case2', results['case2']), ('case3', results['case3'])]:
        sol = data['sol']
        m = data['m']
        ax1.plot(sol.t, sol.y[0], linewidth=2, label=f'm = {m}')
    
    ax1.set_xlabel('ξ (Traveling Wave Coordinate)', fontsize=12)
    ax1.set_ylabel('f(ξ) (Saturation Profile)', fontsize=12)
    ax1.set_title('Traveling Wave Profiles for Porous Medium Equation\n(c = 1)', fontsize=14)
    ax1.legend(fontsize=11)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(left=0)
    ax1.set_ylim(bottom=0)
    
    plt.tight_layout()
    plt.savefig('../report/images/traveling_wave_profiles.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Saved: traveling_wave_profiles.png")
    
    # Figure 2: Derivative profiles
    fig2, axes2 = plt.subplots(1, 2, figsize=(14, 5))
    
    for case_name in ['case1', 'case2', 'case3']:
        data = results[case_name]
        sol = data['sol']
        m = data['m']
        f = sol.y[0]
        g = sol.y[1]
        f_prime = g / (f ** m)
        
        axes2[0].plot(sol.t, f_prime, linewidth=2, label=f'm = {m}')
        axes2[1].plot(f, f_prime, linewidth=2, label=f'm = {m}')
    
    axes2[0].set_xlabel('ξ', fontsize=12)
    axes2[0].set_ylabel("f'(ξ)", fontsize=12)
    axes2[0].set_title('Derivative Profile', fontsize=14)
    axes2[0].legend(fontsize=11)
    axes2[0].grid(True, alpha=0.3)
    
    axes2[1].set_xlabel('f', fontsize=12)
    axes2[1].set_ylabel("f'", fontsize=12)
    axes2[1].set_title('Phase Portrait', fontsize=14)
    axes2[1].legend(fontsize=11)
    axes2[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('../report/images/derivative_profiles.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Saved: derivative_profiles.png")
    
    # Figure 3: Residual analysis
    fig3, axes3 = plt.subplots(2, 2, figsize=(14, 10))
    
    case_names = ['case1', 'case2', 'case3', 'case4']
    titles = ['m = 1, c = 1', 'm = 2, c = 1', 'm = 3, c = 1', 'm = 2, c = 2']
    
    for idx, (case_name, title) in enumerate(zip(case_names, titles)):
        ax = axes3[idx // 2, idx % 2]
        data = results[case_name]
        sol = data['sol']
        m, c = data['m'], data['c']
        
        residual, _, _ = compute_residual(sol, m, c)
        
        ax.semilogy(sol.t, residual, 'b-', linewidth=1.5)
        ax.set_xlabel('ξ', fontsize=11)
        ax.set_ylabel('Residual (log scale)', fontsize=11)
        ax.set_title(f'ODE Residual: {title}', fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(bottom=1e-16)
    
    plt.tight_layout()
    plt.savefig('../report/images/residual_analysis.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Saved: residual_analysis.png")
    
    # Figure 4: Effect of wave speed
    fig4, ax4 = plt.subplots(figsize=(10, 6))
    
    for case_name in ['case2', 'case4']:
        data = results[case_name]
        sol = data['sol']
        c = data['c']
        ax4.plot(sol.t, sol.y[0], linewidth=2, label=f'c = {c}')
    
    ax4.set_xlabel('ξ (Traveling Wave Coordinate)', fontsize=12)
    ax4.set_ylabel('f(ξ)', fontsize=12)
    ax4.set_title('Effect of Wave Speed on Profile (m = 2)', fontsize=14)
    ax4.legend(fontsize=11)
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('../report/images/wave_speed_effect.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Saved: wave_speed_effect.png")
    
    # Figure 5: Verification - comparison with analytical solution for m=1
    # For m=1, the analytical solution is f(ξ) = A*exp(-c*ξ) + B
    # With f(0) = 1, f'(0) = -0.5, c = 1:
    # f(ξ) = 0.5*exp(-ξ) + 0.5
    
    fig5, axes5 = plt.subplots(1, 2, figsize=(14, 5))
    
    sol1 = results['case1']['sol']
    xi = sol1.t
    f_numerical = sol1.y[0]
    f_analytical = 0.5 * np.exp(-xi) + 0.5
    
    axes5[0].plot(xi, f_numerical, 'b-', linewidth=2, label='Numerical')
    axes5[0].plot(xi, f_analytical, 'r--', linewidth=2, label='Analytical')
    axes5[0].set_xlabel('ξ', fontsize=12)
    axes5[0].set_ylabel('f(ξ)', fontsize=12)
    axes5[0].set_title('Verification: m = 1 (Linear Diffusion)', fontsize=14)
    axes5[0].legend(fontsize=11)
    axes5[0].grid(True, alpha=0.3)
    
    error = np.abs(f_numerical - f_analytical)
    axes5[1].semilogy(xi, error, 'g-', linewidth=2)
    axes5[1].set_xlabel('ξ', fontsize=12)
    axes5[1].set_ylabel('Absolute Error (log scale)', fontsize=12)
    axes5[1].set_title('Numerical vs Analytical Error', fontsize=14)
    axes5[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('../report/images/verification_m1.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Saved: verification_m1.png")
    
    # =============================================================================
    # Save Results
    # =============================================================================
    
    print("\n" + "="*70)
    print("Summary of Results")
    print("="*70)
    
    summary = []
    for case_name in ['case1', 'case2', 'case3', 'case4']:
        data = results[case_name]
        summary.append({
            'case': case_name,
            'm': data['m'],
            'c': data['c'],
            'max_residual': data['max_residual'],
            'mean_residual': data['mean_residual'],
            'n_points': len(data['sol'].t)
        })
        print(f"\n{case_name}: m={data['m']}, c={data['c']}")
        print(f"  Max residual: {data['max_residual']:.2e}")
        print(f"  Mean residual: {data['mean_residual']:.2e}")
    
    # Save summary to file
    with open('../outputs/summary.txt', 'w') as f:
        f.write("Porous Medium Traveling Wave - Numerical Results Summary\n")
        f.write("="*60 + "\n\n")
        for s in summary:
            f.write(f"Case: {s['case']}\n")
            f.write(f"  Parameters: m = {s['m']}, c = {s['c']}\n")
            f.write(f"  Number of points: {s['n_points']}\n")
            f.write(f"  Max residual: {s['max_residual']:.2e}\n")
            f.write(f"  Mean residual: {s['mean_residual']:.2e}\n\n")
    
    print("\nResults saved to outputs/summary.txt")
    print("Figures saved to report/images/")
    
    return results


if __name__ == "__main__":
    results = main()
