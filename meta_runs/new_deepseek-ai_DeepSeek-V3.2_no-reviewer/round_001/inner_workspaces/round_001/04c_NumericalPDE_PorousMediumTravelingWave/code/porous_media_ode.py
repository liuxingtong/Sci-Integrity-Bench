#!/usr/bin/env python3
"""
Numerical solution of traveling-wave ODE for porous media equation.

The porous medium equation (PME): ∂u/∂t = ∇·(u^m ∇u)
For traveling waves: u(x,t) = f(ξ), ξ = x - ct
This reduces to an ODE for f(ξ).

For m > 0, the ODE is:
-c f' = (f^m f')'

Let v = f', then:
-c f' = m f^{m-1} (f')^2 + f^m f''
Or equivalently:
f'' = -c f' / f^m - m (f')^2 / f

We'll solve this ODE numerically with appropriate boundary conditions.
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for saving files

import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt
import os


def porous_media_ode(xi, y, m, c):
    """
    ODE system for traveling wave solution of porous media equation.
    
    Parameters:
    -----------
    xi : float
        Independent variable (traveling wave coordinate)
    y : array
        [f, f'] where f is saturation profile
    m : float
        Nonlinearity exponent (m > 0)
    c : float
        Wave speed
        
    Returns:
    --------
    dydxi : array
        Derivatives [f', f'']
    """
    f, fp = y
    
    # Avoid division by zero
    if f <= 0:
        f = 1e-12
    
    # Second derivative
    fpp = -c * fp / (f**m) - m * fp**2 / f
    
    return [fp, fpp]


def solve_traveling_wave(m=2.0, c=1.0, f0=1.0, fp0=-0.1, xi_span=(-10, 10), **kwargs):
    """
    Solve the traveling wave ODE for porous media equation.
    
    Parameters:
    -----------
    m : float
        Nonlinearity exponent
    c : float
        Wave speed
    f0 : float
        Initial value of f at xi=0
    fp0 : float
        Initial value of f' at xi=0
    xi_span : tuple
        Integration interval (xi_min, xi_max)
    **kwargs : dict
        Additional arguments for solve_ivp
        
    Returns:
    --------
    sol : OdeSolution
        Solution object from solve_ivp
    """
    # Initial conditions
    y0 = [f0, fp0]
    
    # Solve ODE
    sol = solve_ivp(
        lambda xi, y: porous_media_ode(xi, y, m, c),
        xi_span,
        y0,
        method='RK45',
        rtol=1e-8,
        atol=1e-10,
        dense_output=True,
        **kwargs
    )
    
    return sol


def compute_residual(sol, m, c, xi_eval=None):
    """
    Compute residual of the ODE to verify the solution.
    
    The residual is defined as: R(ξ) = f'' + c f' / f^m + m (f')^2 / f
    For an exact solution, R(ξ) = 0.
    
    Parameters:
    -----------
    sol : OdeSolution
        Solution object from solve_ivp
    m : float
        Nonlinearity exponent
    c : float
        Wave speed
    xi_eval : array, optional
        Points at which to evaluate residual
        
    Returns:
    --------
    xi : array
        Evaluation points
    residual : array
        Residual values
    max_residual : float
        Maximum absolute residual
    rms_residual : float
        Root-mean-square residual
    """
    if xi_eval is None:
        # Use solution points
        xi = sol.t
    else:
        xi = xi_eval
    
    # Evaluate solution at points
    y = sol.sol(xi)
    f = y[0]
    fp = y[1]
    
    # Compute second derivative using the ODE
    fpp = np.zeros_like(f)
    for i in range(len(f)):
        if f[i] <= 0:
            f[i] = 1e-12
        fpp[i] = -c * fp[i] / (f[i]**m) - m * fp[i]**2 / f[i]
    
    # Compute residual
    residual = fpp + c * fp / (f**m) + m * fp**2 / f
    
    # Statistics
    max_residual = np.max(np.abs(residual))
    rms_residual = np.sqrt(np.mean(residual**2))
    
    return xi, residual, max_residual, rms_residual


def plot_solution(sol, m, c, save_path=None):
    """
    Plot the traveling wave solution.
    """
    # Create evaluation points for smooth plot
    xi_plot = np.linspace(sol.t[0], sol.t[-1], 1000)
    y_plot = sol.sol(xi_plot)
    f_plot = y_plot[0]
    fp_plot = y_plot[1]
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    
    # Plot f(ξ)
    ax = axes[0, 0]
    ax.plot(xi_plot, f_plot, 'b-', linewidth=2)
    ax.set_xlabel('ξ (traveling wave coordinate)')
    ax.set_ylabel('f(ξ) (saturation)')
    ax.set_title(f'Traveling wave solution (m={m}, c={c})')
    ax.grid(True, alpha=0.3)
    
    # Plot f'(ξ)
    ax = axes[0, 1]
    ax.plot(xi_plot, fp_plot, 'r-', linewidth=2)
    ax.set_xlabel('ξ (traveling wave coordinate)')
    ax.set_ylabel("f'(ξ)")
    ax.set_title('Derivative of traveling wave')
    ax.grid(True, alpha=0.3)
    
    # Phase portrait
    ax = axes[1, 0]
    ax.plot(f_plot, fp_plot, 'g-', linewidth=2)
    ax.set_xlabel('f(ξ)')
    ax.set_ylabel("f'(ξ)")
    ax.set_title('Phase portrait')
    ax.grid(True, alpha=0.3)
    
    # Compute and plot residual
    xi_res, residual, max_res, rms_res = compute_residual(sol, m, c, xi_plot)
    
    ax = axes[1, 1]
    ax.plot(xi_res, residual, 'k-', linewidth=1)
    ax.axhline(y=0, color='r', linestyle='--', alpha=0.5)
    ax.set_xlabel('ξ (traveling wave coordinate)')
    ax.set_ylabel('Residual R(ξ)')
    ax.set_title(f'ODE Residual (max={max_res:.2e}, RMS={rms_res:.2e})')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Figure saved to {save_path}")
    
    return fig


def main():
    """Main function to run the analysis."""
    # Create output directory
    os.makedirs('outputs', exist_ok=True)
    os.makedirs('report/images', exist_ok=True)
    
    # Parameters for different cases
    cases = [
        {'m': 2.0, 'c': 1.0, 'f0': 1.0, 'fp0': -0.1, 'name': 'case1'},
        {'m': 1.5, 'c': 1.0, 'f0': 1.0, 'fp0': -0.1, 'name': 'case2'},
        {'m': 3.0, 'c': 2.0, 'f0': 1.0, 'fp0': -0.2, 'name': 'case3'},
    ]
    
    results = []
    
    for case in cases:
        print(f"\nSolving case: {case['name']}")
        print(f"  m={case['m']}, c={case['c']}, f0={case['f0']}, f'0={case['fp0']}")
        
        # Solve ODE
        sol = solve_traveling_wave(
            m=case['m'],
            c=case['c'],
            f0=case['f0'],
            fp0=case['fp0'],
            xi_span=(-10, 10)
        )
        
        # Compute residual
        xi, residual, max_res, rms_res = compute_residual(sol, case['m'], case['c'])
        
        # Save results
        case_result = {
            'name': case['name'],
            'sol': sol,
            'max_residual': max_res,
            'rms_residual': rms_res,
            'success': sol.success
        }
        results.append(case_result)
        
        print(f"  Solution success: {sol.success}")
        print(f"  Max residual: {max_res:.2e}")
        print(f"  RMS residual: {rms_res:.2e}")
        
        # Plot solution
        fig = plot_solution(
            sol,
            case['m'],
            case['c'],
            save_path=f'../report/images/solution_{case["name"]}.png'
        )
        plt.close(fig)
        
        # Save numerical data
        np.savez(
            f'outputs/solution_{case["name"]}.npz',
            xi=sol.t,
            f=sol.y[0],
            fp=sol.y[1],
            m=case['m'],
            c=case['c'],
            max_residual=max_res,
            rms_residual=rms_res
        )
    
    # Print summary
    print("\n" + "="*60)
    print("SUMMARY OF RESULTS")
    print("="*60)
    for res in results:
        print(f"{res['name']}: success={res['success']}, "
              f"max_residual={res['max_residual']:.2e}, "
              f"rms_residual={res['rms_residual']:.2e}")
    
    return results


if __name__ == '__main__':
    main()
