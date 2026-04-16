#!/usr/bin/env python3
"""
Find correct traveling wave solution for porous medium equation.

We solve: (f^m)'' + c f' = 0
Integrate once: (f^m)' + c f = A (constant)

Boundary conditions:
1. f → 1 as ξ → -∞
2. f = 0 for ξ ≥ ξ* (compact support)
3. f'(ξ*) = 0 (smooth front)

At ξ=ξ*, f=0, so (f^m)' = m f^{m-1} f' = 0
Thus A = c f(ξ*) = 0

So: (f^m)' + c f = 0
or: m f^{m-1} f' + c f = 0

For f > 0: m f^{m-2} f' + c = 0
=> f' = -c/(m) f^{2-m}

This is what we had before. But now we need to incorporate compact support.

The solution f' = -c/m f^{2-m} blows up as f→0 for m>2.
The resolution is that the solution has a free boundary at ξ=ξ* where f=0.

We can solve: df/f^{2-m} = -c/m dξ
Integrate from ξ to ξ*:
∫_{f(ξ)}^{0} f^{m-2} df = -c/m ∫_{ξ}^{ξ*} dξ

But ∫_{f}^{0} f^{m-2} df = -f^{m-1}/(m-1) for m≠1
So: -f^{m-1}/(m-1) = -c/m (ξ* - ξ)
=> f^{m-1} = c(m-1)/m (ξ* - ξ)
=> f(ξ) = [c(m-1)/m (ξ* - ξ)]^{1/(m-1)} for ξ < ξ*

This is the correct solution! It has compact support: f=0 for ξ ≥ ξ*.
"""

import numpy as np
import matplotlib.pyplot as plt
import os


def exact_traveling_wave(xi, m, c, xi_star=0):
    """
    Exact traveling wave solution for porous medium equation.
    f(ξ) = [c(m-1)/m (ξ* - ξ)]^{1/(m-1)} for ξ < ξ*
    f(ξ) = 0 for ξ ≥ ξ*
    """
    # Avoid negative base for fractional power
    arg = c * (m-1) / m * (xi_star - xi)
    arg = np.maximum(arg, 0)  # Set to 0 where negative
    
    return arg ** (1.0/(m-1))


def test_exact():
    """Test the exact solution."""
    os.makedirs('report/images', exist_ok=True)
    
    xi = np.linspace(-5, 5, 1000)
    xi_star = 0  # Front position
    
    plt.figure(figsize=(12, 10))
    
    # Test different m values
    m_values = [1.5, 2.0, 3.0, 4.0]
    c = 1.0
    
    colors = ['b', 'r', 'g', 'm']
    
    for i, m in enumerate(m_values):
        f = exact_traveling_wave(xi, m, c, xi_star)
        
        plt.plot(xi, f, color=colors[i], linewidth=2, label=f'm={m}')
        
        # Check derivative at front
        # For ξ just below ξ*, f ∼ A (ξ* - ξ)^p with p=1/(m-1)
        p = 1.0/(m-1)
        A = (c*(m-1)/m) ** p
        
        print(f"m={m}: p={p:.3f}, A={A:.3f}")
        
        # Plot asymptotic form for comparison
        xi_asym = np.linspace(-2, 0, 100)
        f_asym = A * (xi_star - xi_asym) ** p
        plt.plot(xi_asym, f_asym, color=colors[i], linestyle='--', alpha=0.5)
    
    plt.xlabel(r'$\xi = x - ct$', fontsize=12)
    plt.ylabel(r'$f(\xi)$', fontsize=12)
    plt.title('Exact traveling wave solutions for porous medium equation', fontsize=14)
    plt.legend(fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.ylim(-0.1, 1.5)
    
    plt.tight_layout()
    plt.savefig('report/images/exact_solutions_all_m.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    # Now verify that this satisfies the ODE
    print("\n=== Verifying ODE satisfaction ===")
    
    for m in [2.0, 3.0]:
        print(f"\nFor m={m}:")
        
        # Choose points away from front where f > 0
        xi_test = np.linspace(-3, -0.1, 100)
        f_test = exact_traveling_wave(xi_test, m, c, xi_star)
        
        # Compute derivatives analytically
        # f = [c(m-1)/m (ξ* - ξ)]^{1/(m-1)}
        # Let a = c(m-1)/m
        # f = [a (ξ* - ξ)]^{1/(m-1)} = a^{1/(m-1)} (ξ* - ξ)^{1/(m-1)}
        
        a = c * (m-1) / m
        p = 1.0/(m-1)
        
        f_exact = a**p * (xi_star - xi_test)**p
        fp_exact = -a**p * p * (xi_star - xi_test)**(p-1)
        fpp_exact = a**p * p * (p-1) * (xi_star - xi_test)**(p-2)
        
        # Check ODE: -c f' = m(m-1) f^{m-2} (f')^2 + m f^{m-1} f''
        lhs = -c * fp_exact
        rhs = m*(m-1) * f_exact**(m-2) * fp_exact**2 + m * f_exact**(m-1) * fpp_exact
        
        error = np.abs(lhs - rhs)
        print(f"  Max ODE error: {error.max():.2e}")
        print(f"  Mean ODE error: {error.mean():.2e}")
        
        # Also check integrated form: (f^m)' + c f = 0
        # (f^m)' = m f^{m-1} f'
        lhs2 = m * f_exact**(m-1) * fp_exact + c * f_exact
        error2 = np.abs(lhs2)
        print(f"  Max integrated form error: {error2.max():.2e}")
    
    # Now implement numerical integration to recover this solution
    print("\n=== Numerical integration ===")
    
    def porous_ode(xi, y, m, c):
        """ODE: (f^m)'' + c f' = 0"""
        f, fp = y
        if f < 1e-12:
            f = 1e-12
        
        # f'' = [-c fp - m(m-1) f^{m-2} fp^2] / (m f^{m-1})
        fpp = (-c*fp - m*(m-1)*f**(m-2)*fp**2) / (m*f**(m-1))
        return [fp, fpp]
    
    # Integrate from near the front backward
    m_test = 2.0
    p_test = 1.0/(m_test-1)
    a_test = c * (m_test-1) / m_test
    A_test = a_test ** p_test
    
    epsilon = 1e-4
    xi_start = xi_star - epsilon
    f_start = A_test * epsilon**p_test
    fp_start = -A_test * p_test * epsilon**(p_test-1)
    
    print(f"Starting integration at ξ={xi_start:.6e}")
    print(f"  f={f_start:.6e}, f'={fp_start:.6e}")
    
    from scipy.integrate import solve_ivp
    
    sol = solve_ivp(
        lambda t, y: porous_ode(t, y, m_test, c),
        [xi_start, -10.0],  # Integrate backward
        [f_start, fp_start],
        method='DOP853',
        rtol=1e-8,
        atol=1e-10,
        dense_output=True
    )
    
    print(f"Integration: {sol.t.size} points")
    print(f"f range: [{sol.y[0].min():.6f}, {sol.y[0].max():.6f}]")
    
    # Compare with exact
    xi_num = sol.t
    f_num = sol.y[0]
    f_exact_compare = exact_traveling_wave(xi_num, m_test, c, xi_star)
    
    error = np.abs(f_num - f_exact_compare)
    print(f"\nComparison with exact solution:")
    print(f"Max error: {error.max():.2e}")
    print(f"Mean error: {error.mean():.2e}")
    
    # Plot comparison
    plt.figure(figsize=(10, 6))
    plt.plot(xi_num, f_num, 'bo', markersize=3, label='Numerical')
    
    xi_exact_plot = np.linspace(-10, 0, 1000)
    f_exact_plot = exact_traveling_wave(xi_exact_plot, m_test, c, xi_star)
    plt.plot(xi_exact_plot, f_exact_plot, 'r-', label='Exact')
    
    plt.xlabel(r'$\xi$')
    plt.ylabel(r'$f(\xi)$')
    plt.title(f'Numerical vs Exact (m={m_test}, c={c})')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('report/images/numerical_vs_exact.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    return


if __name__ == "__main__":
    test_exact()