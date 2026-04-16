#!/usr/bin/env python3
"""
Check analytical solutions for porous medium traveling waves.

For m=2, there's a known exact solution.
For general m, we can compare with known asymptotic behavior.
"""

import numpy as np
import matplotlib.pyplot as plt
import os


def exact_solution_m2(xi, c=1.0):
    """
    Exact traveling wave solution for m=2.
    For ∂u/∂t = Δ(u^2), the traveling wave solution is:
    f(ξ) = max(0, 1 - c/6 ξ^2) for ξ ≤ 0? Actually need to check.
    
    Wait, the Barenblatt solution is a similarity solution, not traveling wave.
    Let me derive properly.
    
    For m=2: ∂u/∂t = ∂²(u²)/∂x²
    Traveling wave: u(x,t) = f(ξ), ξ = x - ct
    Then: -c f' = (f²)'' = 2(f f')' = 2(f'² + f f'')
    So: 2f f'' + 2(f')² + c f' = 0
    
    Multiply by f: 2f² f'' + 2f (f')² + c f f' = 0
    This is (f²)'' + c/2 (f²)' = 0
    Let g = f², then: g'' + c/2 g' = 0
    Solution: g' = A exp(-c/2 ξ)
    g = B - (2A/c) exp(-c/2 ξ)
    
    For bounded solution as ξ → ∞, need A = 0, so g' = 0, g = constant.
    That gives trivial solution.
    
    Actually, traveling waves for porous medium equation typically have
    compact support. Let me look for solution with f(ξ) = 0 for ξ > ξ*.
    """
    
    # Known solution form: f(ξ) = [c/(2m) (ξ0 - ξ)]^{1/(m-1)} for ξ < ξ0, 0 otherwise
    # For m=2: f(ξ) = max(0, c/4 (ξ0 - ξ))
    
    ξ0 = 0  # Front position
    return np.maximum(0, c/4 * (ξ0 - xi))


def asymptotic_behavior(xi, m, c, xi0=0):
    """
    Asymptotic behavior near the front.
    f(ξ) ∼ [c(m-1)/(m) (ξ0 - ξ)]^{1/(m-1)} for ξ < ξ0
    f(ξ) = 0 for ξ ≥ ξ0
    """
    return np.where(xi < xi0, 
                   (c*(m-1)/m * (xi0 - xi))**(1/(m-1)), 
                   0)


def main():
    """Main function."""
    os.makedirs('report/images', exist_ok=True)
    
    # Test m=2 case
    xi = np.linspace(-5, 5, 1000)
    c = 1.0
    
    # Analytical solution
    f_analytical = asymptotic_behavior(xi, m=2.0, c=c)
    
    plt.figure(figsize=(10, 6))
    plt.plot(xi, f_analytical, 'b-', linewidth=2, label='Analytical (m=2)')
    
    # Test m=3
    f_analytical_m3 = asymptotic_behavior(xi, m=3.0, c=c)
    plt.plot(xi, f_analytical_m3, 'r-', linewidth=2, label='Analytical (m=3)')
    
    # Test m=1.5
    f_analytical_m15 = asymptotic_behavior(xi, m=1.5, c=c)
    plt.plot(xi, f_analytical_m15, 'g-', linewidth=2, label='Analytical (m=1.5)')
    
    plt.xlabel(r'$\xi = x - ct$', fontsize=12)
    plt.ylabel(r'$f(\xi)$', fontsize=12)
    plt.title('Analytical traveling wave solutions (compact support)', fontsize=14)
    plt.legend(fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.ylim(-0.1, 1.1)
    
    plt.tight_layout()
    plt.savefig('report/images/analytical_solutions.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print("Analytical solutions plotted.")
    print("Note: These are asymptotic forms valid near the front ξ=ξ0.")
    
    # Now let's try to numerically integrate matching this asymptotic behavior
    # The ODE is: -c f' = (f^m)''
    # Near the front ξ=ξ0, with f(ξ) ∼ A (ξ0 - ξ)^p, we get p = 1/(m-1)
    # and A = [c(m-1)/m]^{1/(m-1)}
    
    # We can use this as initial condition at ξ just below ξ0
    
    return


if __name__ == "__main__":
    main()