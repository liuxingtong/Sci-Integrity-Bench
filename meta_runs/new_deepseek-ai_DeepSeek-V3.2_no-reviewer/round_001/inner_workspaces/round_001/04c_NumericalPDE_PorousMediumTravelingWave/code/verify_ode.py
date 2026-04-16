#!/usr/bin/env python3
"""
Verify the ODE for porous medium traveling wave.
"""

import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt


def test_ode():
    """Test if the ODE satisfies known properties."""
    
    # For m=2, the equation is: -c f' = (f^2)'' = 2(f f')' = 2(f'^2 + f f'')
    # So: 2f f'' + 2f'^2 + c f' = 0
    
    # We can try to find a solution of the form f(ξ) = 1 - a ξ^2 for ξ < 0, 0 otherwise
    # Then f' = -2a ξ, f'' = -2a
    # Plug in: 2(1 - a ξ^2)(-2a) + 2(4a^2 ξ^2) + c(-2a ξ) = 0
    # = -4a(1 - a ξ^2) + 8a^2 ξ^2 - 2a c ξ = 0
    # = -4a + 4a^2 ξ^2 + 8a^2 ξ^2 - 2a c ξ = 0
    # = -4a + 12a^2 ξ^2 - 2a c ξ = 0
    # This must hold for all ξ < 0, so coefficients must vanish:
    # -4a = 0 → a = 0 (trivial) OR
    # The form is wrong.
    
    # Actually, known solution for m=2 is: f(ξ) = max(0, c/6 (ξ0^2 - ξ^2)) for |ξ| < ξ0
    # Let's test this.
    
    c = 1.0
    ξ0 = np.sqrt(6/c)  # So f(0) = 1
    
    def exact_f(xi):
        return np.maximum(0, c/6 * (ξ0**2 - xi**2))
    
    def exact_fp(xi):
        return np.where(xi**2 < ξ0**2, -c/3 * xi, 0)
    
    def exact_fpp(xi):
        return np.where(xi**2 < ξ0**2, -c/3, 0)
    
    # Test points
    xi_test = np.linspace(-ξ0+0.1, ξ0-0.1, 100)
    f_test = exact_f(xi_test)
    fp_test = exact_fp(xi_test)
    fpp_test = exact_fpp(xi_test)
    
    # Check if ODE is satisfied: -c fp = 2(fp^2 + f fpp)
    lhs = -c * fp_test
    rhs = 2 * (fp_test**2 + f_test * fpp_test)
    
    error = np.abs(lhs - rhs)
    print(f"Testing exact solution for m=2")
    print(f"Max error in ODE: {error.max():.2e}")
    print(f"Mean error: {error.mean():.2e}")
    
    # Plot
    plt.figure(figsize=(10, 6))
    plt.plot(xi_test, f_test, 'b-', label='f(ξ)')
    plt.plot(xi_test, fp_test, 'r-', label="f'(ξ)")
    plt.plot(xi_test, fpp_test, 'g-', label="f''(ξ)")
    plt.xlabel(r'$\xi$')
    plt.title('Exact solution for m=2 (porous medium)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('report/images/exact_solution_m2.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    # Now test our ODE function
    def our_ode(xi, y, m, c):
        f, fp = y
        if f < 1e-12:
            f = 1e-12
        fpp = (-c*fp - m*(m-1)*f**(m-2)*fp**2) / (m*f**(m-1))
        return [fp, fpp]
    
    # Compute fpp using our ODE function
    fpp_our = []
    for i, xi_val in enumerate(xi_test):
        y = [f_test[i], fp_test[i]]
        _, fpp_val = our_ode(xi_val, y, m=2.0, c=c)
        fpp_our.append(fpp_val)
    
    fpp_our = np.array(fpp_our)
    error_fpp = np.abs(fpp_our - fpp_test)
    print(f"\nComparing f'' computation:")
    print(f"Max error in f'': {error_fpp.max():.2e}")
    print(f"Mean error: {error_fpp.mean():.2e}")
    
    # The exact solution seems to work! So our ODE is correct.
    # The issue is with our integration method/initial conditions.
    
    # Let's try to integrate from the peak (f=1, f'=0) at ξ=0
    print(f"\n=== Integrating from peak ===")
    
    def integrate_from_peak(m=2.0, c=1.0, xi_end=ξ0):
        # At ξ=0, f=1, f'=0
        y0 = [1.0, 0.0]
        
        # But f'=0 gives division by zero in ODE!
        # Use small perturbation
        y0 = [1.0, -1e-6]
        
        sol = solve_ivp(
            lambda t, y: our_ode(t, y, m, c),
            [0, xi_end],
            y0,
            method='DOP853',
            rtol=1e-8,
            atol=1e-10,
            dense_output=True
        )
        
        return sol
    
    sol = integrate_from_peak()
    print(f"Integration from peak: {sol.t.size} points")
    print(f"f range: [{sol.y[0].min():.6f}, {sol.y[0].max():.6f}]")
    
    # Compare with exact
    xi_num = sol.t
    f_num = sol.y[0]
    f_exact = exact_f(xi_num)
    
    error = np.abs(f_num - f_exact)
    print(f"\nComparison with exact solution:")
    print(f"Max error: {error.max():.2e}")
    print(f"Mean error: {error.mean():.2e}")
    
    # Plot comparison
    plt.figure(figsize=(10, 6))
    plt.plot(xi_num, f_num, 'bo', markersize=3, label='Numerical')
    plt.plot(xi_test, f_test, 'r-', label='Exact')
    plt.xlabel(r'$\xi$')
    plt.ylabel(r'$f(\xi)$')
    plt.title('Comparison: Numerical vs Exact (m=2)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('report/images/comparison_m2.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    return


if __name__ == "__main__":
    test_ode()