#!/usr/bin/env python3
"""
Improved integration for porous medium traveling waves.

For the porous medium equation ∂u/∂t = Δ(u^m), the traveling wave
solution u(x,t) = f(ξ) with ξ = x - ct satisfies:

-c f' = (f^m)''

We can integrate this once:
-c f = (f^m)' + A
where A is integration constant.

For a proper traveling wave with f → 0 as ξ → ∞ and f → 1 as ξ → -∞,
we typically have A = 0. Then:
(f^m)' = -c f
or m f^{m-1} f' = -c f

For f > 0, this gives:
f' = -c/(m f^{m-2})

But wait, this is only valid if we neglect the integration constant.
Let's derive properly.
"""

import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt
import os


def porous_ode_system(xi, y, m, c):
    """
    ODE system for porous medium traveling wave.
    y = [f, g] where g = (f^m)'
    
    From: -c f' = (f^m)''
    Let g = (f^m)', then:
    f' = ?
    g' = -c f'
    
    But we need f' in terms of f and g.
    Since g = (f^m)' = m f^{m-1} f', we have:
    f' = g / (m f^{m-1})
    
    Then system is:
    f' = g / (m f^{m-1})
    g' = -c f' = -c g / (m f^{m-1})
    """
    f, g = y
    
    # Avoid division by zero
    if f < 1e-12:
        f = 1e-12
    
    fp = g / (m * f**(m-1))
    gp = -c * fp
    
    return [fp, gp]


def integrate_from_peak(m=2.0, c=1.0, f_peak=1.0, xi_range=20.0, 
                       rtol=1e-8, atol=1e-10, method='DOP853'):
    """
    Integrate from the peak of the wave (f=1) in both directions.
    
    At the peak, we expect f' = 0. But from the ODE, if f=1 and f'=0,
    we need to determine g.
    
    Actually, for a proper traveling wave, we want f → 0 as ξ → ∞.
    Let's integrate backward from where f is small.
    """
    
    # Alternative approach: use phase plane analysis
    # The equation can be written as:
    # d/dξ (f^m)' = -c f'
    # Integrating once: (f^m)' = -c f + K
    # For f → 0 and f' → 0 as ξ → ∞, we need K = 0
    # So (f^m)' = -c f
    # or m f^{m-1} f' = -c f
    # For f > 0: f' = -c/(m f^{m-2})
    
    # This suggests we can solve:
    # f' = -c/(m) f^{2-m} for f > 0
    # But this blows up as f → 0 for m > 2
    
    # Let's try a different formulation
    # Write as second order ODE directly
    def ode2(xi, y):
        f, fp = y
        if f < 1e-12:
            f = 1e-12
        
        # f'' = [-c fp - m(m-1) f^{m-2} fp^2] / (m f^{m-1})
        fpp = (-c*fp - m*(m-1)*f**(m-2)*fp**2) / (m*f**(m-1))
        return [fp, fpp]
    
    # We need to find the right initial conditions
    # For a traveling wave with compact support, f(ξ*) = 0 at some ξ*
    # and f'(ξ*) = 0 (smooth cutoff)
    
    # Actually, at the front ξ* where f=0, we typically have f'=0 too
    # So we can integrate backward from the front
    
    # Start very close to 0
    f0 = 1e-6
    # For small f, the ODE simplifies. Let's derive asymptotic behavior
    # For f → 0, assume f ~ a (ξ* - ξ)^p
    # Then f' ~ -a p (ξ* - ξ)^{p-1}
    # f'' ~ a p (p-1) (ξ* - ξ)^{p-2}
    # Plug into ODE and balance leading terms
    # For m > 1, we find p = 1/(m-1)
    
    p = 1/(m-1)
    a = (c * (m-1) / m)**(1/(m-1))  # From literature
    
    # At small ε = ξ* - ξ, f ≈ a ε^p
    # f' ≈ -a p ε^{p-1}
    
    # Choose ε small
    epsilon = 1e-4
    f0 = a * epsilon**p
    fp0 = -a * p * epsilon**(p-1)
    
    print(f"Asymptotic analysis: p = {p:.4f}, a = {a:.4f}")
    print(f"Starting with f0 = {f0:.6e}, fp0 = {fp0:.6e}")
    
    # Integrate backward (ξ decreasing)
    xi_start = 0.0  # This is ξ*, the front position
    xi_end = -xi_range  # Go backward
    
    sol = solve_ivp(
        lambda t, y: ode2(t, y),
        [xi_start, xi_end],
        [f0, fp0],
        method=method,
        rtol=rtol,
        atol=atol,
        dense_output=True
    )
    
    return sol


def test_improved():
    """Test the improved integration."""
    os.makedirs('report/images', exist_ok=True)
    os.makedirs('outputs', exist_ok=True)
    
    m_test = 2.0
    c_test = 1.0
    
    print(f"Testing improved integration for m={m_test}, c={c_test}")
    
    sol = integrate_from_peak(m=m_test, c=c_test, xi_range=15.0)
    
    print(f"Integration successful: {sol.t.size} points")
    print(f"ξ range: [{sol.t.min():.4f}, {sol.t.max():.4f}]")
    print(f"f range: [{sol.y[0].min():.6f}, {sol.y[0].max():.6f}]")
    
    # Plot
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    xi = sol.t
    f = sol.y[0]
    fp = sol.y[1]
    
    # Profile
    ax = axes[0, 0]
    ax.plot(xi, f, 'b-', linewidth=2)
    ax.set_xlabel(r'$\xi$')
    ax.set_ylabel(r'$f(\xi)$')
    ax.set_title(f'Traveling wave profile (m={m_test}, c={c_test})')
    ax.grid(True, alpha=0.3)
    
    # Derivative
    ax = axes[0, 1]
    ax.plot(xi, fp, 'r-', linewidth=2)
    ax.set_xlabel(r'$\xi$')
    ax.set_ylabel(r"$f'(\xi)$")
    ax.set_title('Derivative')
    ax.grid(True, alpha=0.3)
    
    # Phase portrait
    ax = axes[1, 0]
    ax.plot(f, fp, 'g-', linewidth=2)
    ax.set_xlabel(r'$f$')
    ax.set_ylabel(r"$f'$")
    ax.set_title('Phase portrait')
    ax.grid(True, alpha=0.3)
    
    # Log-log plot to check power law
    ax = axes[1, 1]
    # Plot f vs (ξ* - ξ) on log-log
    # ξ* is where we started (0)
    xi_star_minus_xi = -xi  # Since we integrated backward
    mask = xi_star_minus_xi > 0
    ax.loglog(xi_star_minus_xi[mask], f[mask], 'mo-', markersize=3)
    
    # Expected power law: f ~ a (ξ* - ξ)^p
    p = 1/(m_test - 1)
    a = (c_test * (m_test - 1) / m_test)**(1/(m_test - 1))
    
    # Overlay expected power law
    xi_fit = np.logspace(-4, 1, 100)
    f_fit = a * xi_fit**p
    ax.loglog(xi_fit, f_fit, 'k--', label=f'Expected: ~ξ^{p:.2f}')
    
    ax.set_xlabel(r'$\xi^* - \xi$')
    ax.set_ylabel(r'$f(\xi)$')
    ax.set_title('Power law check (log-log)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('report/images/improved_integration.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    # Save data
    np.savez(f'outputs/improved_m{m_test}_c{c_test}.npz',
             xi=xi, f=f, fp=fp, m=m_test, c=c_test)
    
    print(f"\nFigure saved to report/images/improved_integration.png")
    print(f"Data saved to outputs/improved_m{m_test}_c{c_test}.npz")
    
    return sol


if __name__ == "__main__":
    test_improved()