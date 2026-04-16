#!/usr/bin/env python3
"""
Final implementation of porous medium traveling wave integration.

We solve: -c f' = (f^m)''
with boundary conditions:
- f → 1 as ξ → -∞
- f = 0 for ξ ≥ ξ* (compact support)
- f'(ξ*) = 0 (smooth front)

We integrate backward from the front ξ* using asymptotic initial conditions.
"""

import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt
import os


def porous_ode(xi, y, m, c):
    """
    ODE system for porous medium traveling wave.
    y = [f, f']
    
    Equation: -c f' = (f^m)''
    which expands to: -c f' = m(m-1) f^{m-2} (f')^2 + m f^{m-1} f''
    """
    f, fp = y
    
    # Avoid division by zero for very small f
    if f < 1e-12:
        f = 1e-12
    
    # Compute f''
    fpp_numer = -c * fp - m * (m-1) * (f ** (m-2)) * (fp ** 2)
    fpp_denom = m * (f ** (m-1))
    fpp = fpp_numer / fpp_denom
    
    return [fp, fpp]


def integrate_traveling_wave(m=2.0, c=1.0, xi_start=0.0, xi_end=-20.0,
                            rtol=1e-8, atol=1e-10, method='DOP853'):
    """
    Integrate traveling wave ODE backward from the front.
    
    At the front ξ=ξ*, we have f(ξ*) = 0 and f'(ξ*) = 0.
    Near the front, asymptotic analysis gives:
    f(ξ) ∼ A (ξ* - ξ)^p for ξ < ξ*
    where p = 1/(m-1) and A = [c(m-1)/m]^{1/(m-1)}
    
    We start at ξ = ξ* - ε with ε small.
    """
    
    # Asymptotic parameters
    p = 1.0 / (m - 1.0)
    A = (c * (m - 1.0) / m) ** (1.0 / (m - 1.0))
    
    # Small offset from front
    epsilon = 1e-6
    
    # Initial conditions at ξ = ξ_start - epsilon
    xi_init = xi_start - epsilon
    f_init = A * (epsilon ** p)
    fp_init = -A * p * (epsilon ** (p - 1.0))
    
    print(f"\nIntegrating for m={m}, c={c}")
    print(f"  Asymptotic: p={p:.4f}, A={A:.4f}")
    print(f"  Starting at ξ={xi_init:.6e} with f={f_init:.6e}, f'={fp_init:.6e}")
    
    # Integrate backward
    sol = solve_ivp(
        lambda t, y: porous_ode(t, y, m, c),
        [xi_init, xi_end],
        [f_init, fp_init],
        method=method,
        rtol=rtol,
        atol=atol,
        dense_output=True,
        max_step=0.1  # Limit step size for accuracy
    )
    
    return sol, A, p


def analyze_and_plot(m_values=[2.0, 3.0, 1.5], c_values=[1.0, 2.0],
                    xi_end=-15.0):
    """Run integration for multiple parameters and create plots."""
    os.makedirs('report/images', exist_ok=True)
    os.makedirs('outputs', exist_ok=True)
    
    all_results = []
    
    for m in m_values:
        for c in c_values:
            try:
                sol, A, p = integrate_traveling_wave(m=m, c=c, xi_end=xi_end)
                
                print(f"  Integration: {sol.t.size} points")
                print(f"  f range: [{sol.y[0].min():.6f}, {sol.y[0].max():.6f}]")
                
                # Check if solution approaches 1
                f_end = sol.y[0, -1]
                print(f"  f at ξ={sol.t[-1]:.2f}: {f_end:.6f}")
                
                # Save results
                result = {
                    'm': m,
                    'c': c,
                    'sol': sol,
                    'A': A,
                    'p': p,
                    'xi': sol.t,
                    'f': sol.y[0],
                    'fp': sol.y[1]
                }
                all_results.append(result)
                
                # Save data
                np.savez(f'outputs/final_m{m}_c{c}.npz',
                        xi=sol.t, f=sol.y[0], fp=sol.y[1],
                        m=m, c=c, A=A, p=p)
                
            except Exception as e:
                print(f"  Failed: {e}")
    
    # Create comprehensive plots
    
    # 1. Profile comparison for different m at fixed c
    plt.figure(figsize=(12, 10))
    
    c_fixed = 1.0
    colors = ['b', 'r', 'g', 'm', 'c']
    
    for i, m in enumerate(m_values):
        # Find result for this m and c_fixed
        result = None
        for r in all_results:
            if abs(r['m'] - m) < 1e-6 and abs(r['c'] - c_fixed) < 1e-6:
                result = r
                break
        
        if result is not None:
            xi = result['xi']
            f = result['f']
            
            # Shift so front is at ξ=0 for comparison
            xi_shifted = xi - xi[0]
            
            plt.plot(xi_shifted, f, color=colors[i], 
                    linewidth=2, label=f'm={m}')
            
            # Plot asymptotic prediction near front
            # f ∼ A (-ξ)^p for ξ < 0
            xi_asym = np.linspace(-2, 0, 100)
            f_asym = result['A'] * (-xi_asym) ** result['p']
            plt.plot(xi_asym, f_asym, color=colors[i], 
                    linestyle='--', alpha=0.5, label=f'asymptotic m={m}')
    
    plt.xlabel(r'$\xi - \xi^*$ (front at 0)', fontsize=12)
    plt.ylabel(r'$f(\xi)$', fontsize=12)
    plt.title(f'Traveling wave profiles (c={c_fixed})', fontsize=14)
    plt.legend(fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.xlim(-15, 5)
    plt.ylim(-0.1, 1.5)
    
    plt.tight_layout()
    plt.savefig('report/images/final_profiles_fixed_c.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    # 2. Effect of wave speed c
    plt.figure(figsize=(12, 10))
    
    m_fixed = 2.0
    
    for i, c in enumerate(c_values):
        # Find result for this m_fixed and c
        result = None
        for r in all_results:
            if abs(r['m'] - m_fixed) < 1e-6 and abs(r['c'] - c) < 1e-6:
                result = r
                break
        
        if result is not None:
            xi = result['xi']
            f = result['f']
            
            # Shift and scale for comparison
            # Theoretical scaling: width ∼ 1/c
            xi_shifted = (xi - xi[0]) * c
            
            plt.plot(xi_shifted, f, color=colors[i], 
                    linewidth=2, label=f'c={c}')
    
    plt.xlabel(r'$c(\xi - \xi^*)$ (scaled)', fontsize=12)
    plt.ylabel(r'$f(\xi)$', fontsize=12)
    plt.title(f'Traveling wave profiles (m={m_fixed}, scaled by c)', fontsize=14)
    plt.legend(fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.xlim(-20, 5)
    plt.ylim(-0.1, 1.5)
    
    plt.tight_layout()
    plt.savefig('report/images/final_profiles_scaled.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    # 3. Phase portraits
    plt.figure(figsize=(12, 10))
    
    for i, m in enumerate(m_values):
        plt.subplot(2, 2, i+1)
        
        for c in c_values:
            # Find result
            result = None
            for r in all_results:
                if abs(r['m'] - m) < 1e-6 and abs(r['c'] - c) < 1e-6:
                    result = r
                    break
            
            if result is not None:
                f = result['f']
                fp = result['fp']
                
                plt.plot(f, fp, linewidth=1.5, label=f'c={c}')
        
        plt.xlabel(r'$f$', fontsize=12)
        plt.ylabel(r"$f'$", fontsize=12)
        plt.title(f'Phase portrait (m={m})', fontsize=12)
        plt.legend(fontsize=10)
        plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('report/images/final_phase_portraits.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    # 4. Convergence test: check asymptotic behavior
    plt.figure(figsize=(12, 10))
    
    for i, m in enumerate(m_values):
        plt.subplot(2, 2, i+1)
        
        c = 1.0  # Fixed c for this plot
        result = None
        for r in all_results:
            if abs(r['m'] - m) < 1e-6 and abs(r['c'] - c) < 1e-6:
                result = r
                break
        
        if result is not None:
            xi = result['xi']
            f = result['f']
            A = result['A']
            p = result['p']
            
            # Distance from front
            dist_from_front = xi[0] - xi  # Positive
            
            # Plot numerical solution
            plt.loglog(dist_from_front, f, 'bo', markersize=3, label='Numerical')
            
            # Plot asymptotic prediction
            dist_fit = np.logspace(-6, 1, 100)
            f_asym = A * dist_fit ** p
            plt.loglog(dist_fit, f_asym, 'r-', linewidth=2, 
                      label=f'Asymptotic: ~dist^{p:.2f}')
            
            plt.xlabel(r'$\xi^* - \xi$ (distance from front)', fontsize=12)
            plt.ylabel(r'$f(\xi)$', fontsize=12)
            plt.title(f'Asymptotic check (m={m}, c={c})', fontsize=12)
            plt.legend(fontsize=10)
            plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('report/images/final_asymptotic_check.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"\nGenerated {len(all_results)} solutions")
    print("Plots saved to report/images/")
    
    return all_results


if __name__ == "__main__":
    results = analyze_and_plot()