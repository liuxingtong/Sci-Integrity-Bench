import numpy as np
from scipy.integrate import solve_bvp, solve_ivp
import matplotlib.pyplot as plt
import os

# Porous medium equation traveling wave ODE
# ∂u/∂t = ∂²(u^m)/∂x²
# Traveling wave: u(x,t) = f(ξ), ξ = x - ct
# ODE: -c f' = m(m-1)f^{m-2}(f')² + m f^{m-1} f''
# Rewrite as system of first-order ODEs:
# Let y1 = f, y2 = f'
# Then: y1' = y2
#       y2' = [-c*y2 - m*(m-1)*y1^{m-2}*y2²] / (m*y1^{m-1})
# For y1 > 0

def porous_medium_ode(xi, y, m, c):
    """ODE system for porous medium traveling wave."""
    f, fp = y
    
    # Avoid division by zero - handle array case
    f_safe = np.maximum(f, 1e-12)
    
    # Compute fpp
    fpp = (-c*fp - m*(m-1)*f_safe**(m-2)*fp**2) / (m*f_safe**(m-1))
    
    return [fp, fpp]


def bc(ya, yb):
    """Boundary conditions for traveling wave.
    Typically: f(-∞) = 1, f(∞) = 0
    We approximate on finite domain [-L, L]"""
    # Left boundary: f ≈ 1
    # Right boundary: f ≈ 0
    return [ya[0] - 1, yb[0]]


def solve_traveling_wave(m=2, c=1, L=10, n_points=100):
    """Solve traveling wave ODE for porous medium equation."""
    # Initial mesh
    xi_mesh = np.linspace(-L, L, n_points)
    
    # Initial guess: tanh profile
    f_init = 0.5 * (1 - np.tanh(xi_mesh))
    fp_init = -0.5 / np.cosh(xi_mesh)**2
    y_init = np.vstack([f_init, fp_init])
    
    # Solve BVP
    sol = solve_bvp(
        lambda xi, y: porous_medium_ode(xi, y, m, c),
        bc,
        xi_mesh,
        y_init,
        max_nodes=10000,
        tol=1e-8
    )
    
    if not sol.success:
        print(f"BVP solver failed: {sol.message}")
        return None
    
    # Refine solution on dense grid
    xi_dense = np.linspace(-L, L, 1000)
    f_dense = sol.sol(xi_dense)[0]
    
    return xi_dense, f_dense, sol


def compute_residual(xi, f, m, c):
    """Compute residual of the ODE."""
    # Compute derivatives using finite differences
    dx = xi[1] - xi[0]
    fp = np.gradient(f, dx)
    fpp = np.gradient(fp, dx)
    
    # ODE residual: -c*fp - m*(m-1)*f**(m-2)*fp**2 - m*f**(m-1)*fpp
    # Should be zero
    residual = -c*fp - m*(m-1)*f**(m-2)*fp**2 - m*f**(m-1)*fpp
    
    # L2 norm
    l2_norm = np.sqrt(np.trapz(residual**2, xi))
    
    return residual, l2_norm


def adaptive_step_solver(m=2, c=1, L=10, tol=1e-8, max_iter=10):
    """Solve with adaptive step size to achieve residual < tol."""
    n_points = 100
    
    for iter in range(max_iter):
        print(f"Iteration {iter+1}: n_points = {n_points}")
        
        result = solve_traveling_wave(m, c, L, n_points)
        if result is None:
            return None
        
        xi, f, sol = result
        
        # Compute residual
        residual, l2_norm = compute_residual(xi, f, m, c)
        print(f"  Residual L2 norm: {l2_norm:.2e}")
        
        if l2_norm < tol:
            print(f"Converged after {iter+1} iterations")
            return xi, f, sol, l2_norm
        
        # Increase resolution
        n_points = int(n_points * 1.5)
    
    print(f"Failed to converge after {max_iter} iterations")
    return xi, f, sol, l2_norm


def main():
    """Main analysis function."""
    # Create outputs directory
    os.makedirs('outputs', exist_ok=True)
    os.makedirs('report/images', exist_ok=True)
    
    # Test different m values
    m_values = [1.5, 2, 3, 4]
    c = 1.0  # wave speed
    
    results = {}
    
    for m in m_values:
        print(f"\nSolving for m = {m}")
        print("="*40)
        
        # Solve with adaptive step size
        result = adaptive_step_solver(m=m, c=c, L=15, tol=1e-8)
        
        if result is not None:
            xi, f, sol, l2_norm = result
            results[m] = (xi, f, l2_norm)
            
            # Save results
            np.savetxt(f'outputs/profile_m_{m:.1f}.txt', 
                      np.column_stack([xi, f]),
                      header=f'xi f m={m} c={c}')
            
            # Plot
            plt.figure(figsize=(10, 6))
            plt.plot(xi, f, 'b-', linewidth=2, label=f'm = {m}')
            plt.xlabel('Traveling wave coordinate ξ = x - ct', fontsize=12)
            plt.ylabel('Saturation f(ξ)', fontsize=12)
            plt.title(f'Porous Medium Traveling Wave (m={m}, c={c})', fontsize=14)
            plt.grid(True, alpha=0.3)
            plt.legend(fontsize=12)
            plt.tight_layout()
            plt.savefig(f'report/images/profile_m_{m:.1f}.png', dpi=150)
            plt.close()
            
            # Plot residual
            residual, _ = compute_residual(xi, f, m, c)
            plt.figure(figsize=(10, 6))
            plt.plot(xi, residual, 'r-', linewidth=1)
            plt.xlabel('ξ', fontsize=12)
            plt.ylabel('ODE residual', fontsize=12)
            plt.title(f'Residual of Traveling Wave ODE (m={m}, L2 norm={l2_norm:.2e})', fontsize=14)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(f'report/images/residual_m_{m:.1f}.png', dpi=150)
            plt.close()
    
    # Compare profiles for different m
    plt.figure(figsize=(10, 6))
    for m in m_values:
        if m in results:
            xi, f, l2_norm = results[m]
            plt.plot(xi, f, linewidth=2, label=f'm = {m}')
    plt.xlabel('Traveling wave coordinate ξ = x - ct', fontsize=12)
    plt.ylabel('Saturation f(ξ)', fontsize=12)
    plt.title('Porous Medium Traveling Waves for Different m Values', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=12)
    plt.tight_layout()
    plt.savefig('report/images/profiles_comparison.png', dpi=150)
    plt.close()
    
    # Save summary of results
    with open('outputs/results_summary.txt', 'w') as f:
        f.write('Porous Medium Traveling Wave Results\n')
        f.write('='*50 + '\n')
        for m in m_values:
            if m in results:
                xi, f, l2_norm = results[m]
                f.write(f'm = {m:.1f}: L2 residual = {l2_norm:.2e}\n')
                f.write(f'  f(-L) = {f[0]:.6f}, f(L) = {f[-1]:.6f}\n')
                f.write(f'  Domain: ξ ∈ [{xi[0]:.1f}, {xi[-1]:.1f}]\n')
    
    print("\nAnalysis complete. Results saved to outputs/ and report/images/")

if __name__ == '__main__':
    main()