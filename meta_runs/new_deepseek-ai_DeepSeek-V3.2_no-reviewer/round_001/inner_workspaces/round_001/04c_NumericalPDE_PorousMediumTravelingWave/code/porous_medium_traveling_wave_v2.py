import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt
import os

# Porous medium equation traveling wave ODE
# ∂u/∂t = ∂²(u^m)/∂x²
# Traveling wave: u(x,t) = f(ξ), ξ = x - ct
# After integration: (f^m)' = -c f
# So: m f^{m-1} f' = -c f
# For f > 0: f' = -c/(m) f^{2-m}

def porous_medium_ode_first_order(xi, f, m, c):
    """First-order ODE for porous medium traveling wave."""
    return -c/(m) * f**(2-m)


def solve_traveling_wave_shooting(m=2, c=1, xi_max=20, f0=1.0, tol=1e-8):
    """Solve traveling wave ODE using forward integration from left boundary."""
    # For m > 1, the solution has compact support
    # We integrate forward until f reaches 0
    
    # Define event for when f reaches near 0
    def event(xi, f):
        return f[0] - 1e-12
    event.terminal = True
    event.direction = -1
    
    # Solve ODE
    sol = solve_ivp(
        lambda xi, f: porous_medium_ode_first_order(xi, f, m, c),
        [0, xi_max],
        [f0],
        events=[event],
        max_step=0.01,
        rtol=1e-10,
        atol=1e-12
    )
    
    if sol.success:
        xi = sol.t
        f = sol.y[0]
        
        # Check if we reached f=0
        if len(sol.t_events[0]) > 0:
            # Truncate at the event
            idx = np.argmin(np.abs(sol.t - sol.t_events[0][0]))
            xi = sol.t[:idx]
            f = sol.y[0, :idx]
        
        # Create symmetric solution for negative xi
        # Since ODE is autonomous, solution for ξ < 0 is symmetric
        xi_full = np.concatenate([-xi[::-1], xi])
        f_full = np.concatenate([f[::-1], f])
        
        return xi_full, f_full, sol
    else:
        print(f"IVP solver failed: {sol.message}")
        return None


def compute_residual(xi, f, m, c):
    """Compute residual of the original second-order ODE."""
    # Compute derivatives using finite differences
    dx = xi[1] - xi[0]
    fp = np.gradient(f, dx)
    fpp = np.gradient(fp, dx)
    
    # Original ODE: -c*fp - m*(m-1)*f**(m-2)*fp**2 - m*f**(m-1)*fpp = 0
    residual = -c*fp - m*(m-1)*f**(m-2)*fp**2 - m*f**(m-1)*fpp
    
    # L2 norm
    l2_norm = np.sqrt(np.trapz(residual**2, xi))
    
    return residual, l2_norm


def adaptive_step_solver(m=2, c=1, max_iter=10):
    """Solve with adaptive step size to achieve residual < tol."""
    xi_max = 10
    
    for iter in range(max_iter):
        print(f"Iteration {iter+1}: xi_max = {xi_max}")
        
        result = solve_traveling_wave_shooting(m, c, xi_max)
        if result is None:
            return None
        
        xi, f, sol = result
        
        # Compute residual of original second-order ODE
        residual, l2_norm = compute_residual(xi, f, m, c)
        print(f"  Residual L2 norm: {l2_norm:.2e}")
        
        if l2_norm < 1e-8:
            print(f"Converged after {iter+1} iterations")
            return xi, f, sol, l2_norm
        
        # Increase domain size
        xi_max *= 2
    
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
        result = adaptive_step_solver(m=m, c=c)
        
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
    with open('outputs/results_summary.txt', 'w') as summary_file:
        summary_file.write('Porous Medium Traveling Wave Results\n')
        summary_file.write('='*50 + '\n')
        for m in m_values:
            if m in results:
                xi, f_vals, l2_norm = results[m]
                summary_file.write(f'm = {m:.1f}: L2 residual = {l2_norm:.2e}\n')
                summary_file.write(f'  f(min) = {f_vals[0]:.6f}, f(max) = {f_vals[-1]:.6f}\n')
                summary_file.write(f'  Domain: ξ ∈ [{xi[0]:.1f}, {xi[-1]:.1f}]\n')
                summary_file.write(f'  Support width: {xi[-1] - xi[0]:.2f}\n')
    
    print("\nAnalysis complete. Results saved to outputs/ and report/images/")

if __name__ == '__main__':
    main()