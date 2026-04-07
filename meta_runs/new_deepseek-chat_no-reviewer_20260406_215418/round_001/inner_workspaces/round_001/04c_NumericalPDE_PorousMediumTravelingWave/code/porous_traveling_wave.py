import numpy as np
from scipy.integrate import solve_bvp
import matplotlib.pyplot as plt
import os

# Porous medium traveling wave ODE
# u(x,t) = f(ξ), ξ = x - ct
# Equation: -c f' = (f^m f')'
# Rewrite as system:
# f' = g
# g' = (-c*g - m*f^(m-1)*g^2) / f^m  for f > 0

# For numerical stability, we can rewrite as:
# (f^m f')' + c f' = 0
# Integrate once: f^m f' + c f = A (constant)
# At boundaries: f → 0, f' → 0 as ξ → ∞ gives A = 0
# So: f^m f' + c f = 0 => f' = -c f^{1-m}
# This first-order ODE holds where f > 0
# But we need to solve the full second-order BVP

def porous_ode(x, y, m, c):
    """ODE system for porous medium traveling wave.
    y[0] = f, y[1] = f'
    """
    f, g = y
    
    # Handle small f to avoid division by zero
    eps = 1e-12
    f_safe = np.maximum(f, eps)
    
    dydx = np.zeros_like(y)
    dydx[0] = g
    
    # For f ≈ 0, use asymptotic form to avoid division by zero
    mask = f_safe <= eps
    dydx[1, ~mask] = (-c*g[~mask] - m * f_safe[~mask]**(m-1) * g[~mask]**2) / f_safe[~mask]**m
    dydx[1, mask] = 0
    
    return dydx

def bc(ya, yb, m, c):
    """Boundary conditions.
    f(-L) = 1, f(L) = 0, where L is large.
    """
    return np.array([ya[0] - 1, yb[0]])

def solve_traveling_wave(m=2, c=1, L=10, n_points=100):
    """Solve traveling wave BVP for porous medium equation."""
    # Initial mesh
    x = np.linspace(-L, L, n_points)
    
    # Initial guess: tanh profile
    f_init = 0.5 * (1 - np.tanh(x/2))
    g_init = -0.5 / (np.cosh(x/2)**2) / 2  # derivative of tanh
    y_init = np.vstack((f_init, g_init))
    
    # Solve BVP
    sol = solve_bvp(
        lambda x, y: porous_ode(x, y, m, c),
        lambda ya, yb: bc(ya, yb, m, c),
        x, y_init,
        max_nodes=10000,
        tol=1e-8
    )
    
    if not sol.success:
        print(f"Warning: BVP solver did not converge for m={m}, c={c}")
        print(f"Message: {sol.message}")
    
    return sol

def compute_residual(sol, m, c):
    """Compute L2 residual of the ODE."""
    x = sol.x
    f = sol.y[0]
    g = sol.y[1]
    
    # Compute residual of the ODE: -c g - (f^m g)' = 0
    # Actually compute (f^m g)' + c g
    fmg = f**m * g
    # Numerical derivative
    fmg_prime = np.gradient(fmg, x)
    residual = fmg_prime + c * g
    
    # L2 norm
    l2_norm = np.sqrt(np.trapz(residual**2, x))
    return l2_norm, residual

def main():
    """Main function to compute and plot traveling wave profiles."""
    # Parameters
    m_values = [2, 3, 4]
    c = 1.0
    L = 20  # Larger domain for better boundary conditions
    
    # Create output directory
    os.makedirs('outputs', exist_ok=True)
    os.makedirs('report/images', exist_ok=True)
    
    plt.figure(figsize=(12, 8))
    
    for i, m in enumerate(m_values):
        print(f"\nSolving for m = {m}, c = {c}")
        
        # Solve BVP
        sol = solve_traveling_wave(m=m, c=c, L=L, n_points=200)
        
        if sol.success:
            # Evaluate on fine grid
            x_fine = np.linspace(-L, L, 1000)
            f_fine = sol.sol(x_fine)[0]
            
            # Compute residual
            l2_norm, residual = compute_residual(sol, m, c)
            print(f"  L2 residual: {l2_norm:.2e}")
            print(f"  Max |f|: {np.max(np.abs(f_fine)):.4f}")
            print(f"  Number of mesh points: {len(sol.x)}")
            
            # Save solution
            np.savetxt(f'outputs/profile_m{m}_c{c}.txt', 
                      np.column_stack((x_fine, f_fine)),
                      header=f'Traveling wave profile for m={m}, c={c}\nxi f')
            
            # Plot
            plt.subplot(2, 2, i+1)
            plt.plot(x_fine, f_fine, 'b-', linewidth=2, label=f'm={m}')
            plt.xlabel(r'$\xi = x - ct$')
            plt.ylabel(r'$f(\xi)$')
            plt.title(f'Traveling wave profile (m={m}, c={c})')
            plt.grid(True, alpha=0.3)
            plt.legend()
            
            # Plot residual
            plt.subplot(2, 2, 4)
            plt.plot(sol.x, residual, '-', label=f'm={m}')
        else:
            print(f"  Failed: {sol.message}")
    
    plt.subplot(2, 2, 4)
    plt.xlabel(r'$\xi$')
    plt.ylabel('Residual')
    plt.title('ODE residuals')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    
    # Save figure
    plt.savefig('report/images/traveling_wave_profiles.png', dpi=300, bbox_inches='tight')
    plt.savefig('outputs/traveling_wave_profiles.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Also plot derivative profiles
    plt.figure(figsize=(10, 6))
    for m in m_values:
        try:
            data = np.loadtxt(f'outputs/profile_m{m}_c{c}.txt')
            x_fine = data[:, 0]
            f_fine = data[:, 1]
            f_prime = np.gradient(f_fine, x_fine)
            plt.plot(x_fine, f_prime, '-', linewidth=2, label=f'm={m}')
        except:
            pass
    
    plt.xlabel(r'$\xi = x - ct$')
    plt.ylabel(r"$f'(\xi)$")
    plt.title('Derivative of traveling wave profiles')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig('report/images/traveling_wave_derivatives.png', dpi=300, bbox_inches='tight')
    plt.savefig('outputs/traveling_wave_derivatives.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print("\nAnalysis complete. Results saved to outputs/ and report/images/")

if __name__ == '__main__':
    main()