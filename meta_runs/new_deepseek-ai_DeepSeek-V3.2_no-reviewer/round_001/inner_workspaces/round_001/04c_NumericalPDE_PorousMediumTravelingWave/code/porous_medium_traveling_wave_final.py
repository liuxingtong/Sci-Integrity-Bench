import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt
import os

# Porous medium equation traveling wave ODE
# ∂u/∂t = ∂²(u^m)/∂x²
# Traveling wave: u(x,t) = f(ξ), ξ = x - ct
# ODE: -c f' = (f^m)''
# Integrate once: (f^m)' = -c f + A
# With boundary conditions f→0, f'→0 as ξ→∞, we get A=0
# So: (f^m)' = -c f
# Or: m f^{m-1} f' = -c f
# For f > 0: f' = -c/m f^{2-m}

def porous_ode(xi, f, m, c):
    """First-order ODE for porous medium traveling wave."""
    # Handle f near 0 carefully
    f_safe = max(f[0], 1e-12)
    return [-c/m * f_safe**(2-m)]


def solve_wave_numerical(m=2, c=1, f0=1.0, xi_end=10, atol=1e-12, rtol=1e-10):
    """Solve traveling wave ODE numerically."""
    # Event for when f reaches 0
    def event(xi, f):
        return f[0]
    event.terminal = True
    event.direction = -1
    
    try:
        sol = solve_ivp(
            lambda xi, f: porous_ode(xi, f, m, c),
            [0, xi_end],
            [f0],
            events=[event],
            max_step=0.01,
            atol=atol,
            rtol=rtol,
            method='RK45'
        )
        
        if sol.success:
            xi_positive = sol.t
            f_positive = sol.y[0]
            
            # If we hit the event, truncate
            if len(sol.t_events[0]) > 0:
                event_idx = np.argmin(np.abs(xi_positive - sol.t_events[0][0]))
                xi_positive = xi_positive[:event_idx]
                f_positive = f_positive[:event_idx]
            
            # Create symmetric solution (wave is even function)
            xi_negative = -xi_positive[::-1]
            f_negative = f_positive[::-1]
            
            xi_full = np.concatenate([xi_negative, xi_positive])
            f_full = np.concatenate([f_negative, f_positive])
            
            return xi_full, f_full, sol
        else:
            print(f"  IVP solver failed: {sol.message}")
            return None
            
    except Exception as e:
        print(f"  Error in solver: {e}")
        return None


def compute_residual(xi, f, m, c):
    """Compute residual of the original second-order ODE."""
    # Use central differences for better accuracy
    dx = xi[1] - xi[0]
    
    # First derivative
    fp = np.gradient(f, dx, edge_order=2)
    
    # Second derivative  
    fpp = np.gradient(fp, dx, edge_order=2)
    
    # Avoid division by zero in residual calculation
    f_safe = np.maximum(f, 1e-12)
    
    # Original ODE: -c*fp - m*(m-1)*f**(m-2)*fp**2 - m*f**(m-1)*fpp = 0
    residual = -c*fp - m*(m-1)*f_safe**(m-2)*fp**2 - m*f_safe**(m-1)*fpp
    
    # L2 norm (skip boundaries where derivatives are less accurate)
    if len(residual) > 10:
        l2_norm = np.sqrt(np.trapz(residual[5:-5]**2, xi[5:-5]))
    else:
        l2_norm = np.sqrt(np.trapz(residual**2, xi))
    
    return residual, l2_norm


def adaptive_solver(m=2, c=1, tol=1e-8, max_refinements=6):
    """Solve with adaptive tolerance to achieve residual < tol."""
    f0 = 1.0
    xi_end = 20
    
    # Try different tolerances
    for ref in range(max_refinements):
        atol = 10**(-12 - ref)
        rtol = 10**(-10 - ref)
        
        print(f"  Refinement {ref+1}: atol={atol:.1e}, rtol={rtol:.1e}")
        
        result = solve_wave_numerical(m, c, f0, xi_end, atol, rtol)
        
        if result is None:
            continue
            
        xi, f, sol = result
        
        # Compute residual
        if len(xi) > 10:
            residual, l2_norm = compute_residual(xi, f, m, c)
            print(f"    L2 residual: {l2_norm:.2e}")
            
            if l2_norm < tol:
                print(f"    Converged with L2 residual < {tol:.1e}")
                return xi, f, sol, l2_norm
        
        # Increase domain if needed
        xi_end *= 1.5
    
    # Return best result
    if result is not None:
        xi, f, sol = result
        residual, l2_norm = compute_residual(xi, f, m, c)
        return xi, f, sol, l2_norm
    else:
        return None


def main():
    """Main analysis function."""
    # Create directories in workspace root
    os.makedirs('outputs', exist_ok=True)
    os.makedirs('report/images', exist_ok=True)
    
    # Test different m values
    m_values = [1.5, 2, 3, 4]
    c = 1.0  # wave speed
    
    results = {}
    
    for m in m_values:
        print(f"\nSolving for m = {m}")
        print("="*40)
        
        # Solve with adaptive tolerance
        result = adaptive_solver(m=m, c=c, tol=1e-8)
        
        if result is not None:
            xi, f, sol, l2_norm = result
            results[m] = (xi, f, l2_norm)
            
            print(f"  Final L2 residual: {l2_norm:.2e}")
            print(f"  Solution points: {len(xi)}")
            print(f"  Domain: [{xi[0]:.3f}, {xi[-1]:.3f}]")
            print(f"  f({xi[0]:.3f}) = {f[0]:.6f}, f({xi[-1]:.3f}) = {f[-1]:.6f}")
            
            # Save results
            np.savetxt(f'outputs/profile_m_{m:.1f}.txt', 
                      np.column_stack([xi, f]),
                      header=f'xi f m={m} c={c} L2_residual={l2_norm:.2e}')
            
            # Plot solution
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
            plt.plot(xi, residual, 'r-', linewidth=1, alpha=0.7)
            plt.axhline(y=0, color='k', linestyle='--', alpha=0.5)
            plt.xlabel('ξ', fontsize=12)
            plt.ylabel('ODE residual', fontsize=12)
            plt.title(f'Residual (m={m}, L2 norm={l2_norm:.2e})', fontsize=14)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(f'report/images/residual_m_{m:.1f}.png', dpi=150)
            plt.close()
        else:
            print(f"  Failed to obtain solution for m={m}")
    
    # Compare profiles for different m
    if results:
        plt.figure(figsize=(10, 6))
        for m in m_values:
            if m in results:
                xi, f, l2_norm = results[m]
                plt.plot(xi, f, linewidth=2, label=f'm = {m} (L2={l2_norm:.1e})')
        plt.xlabel('Traveling wave coordinate ξ = x - ct', fontsize=12)
        plt.ylabel('Saturation f(ξ)', fontsize=12)
        plt.title(f'Porous Medium Traveling Waves (c={c})', fontsize=14)
        plt.grid(True, alpha=0.3)
        plt.legend(fontsize=10)
        plt.tight_layout()
        plt.savefig('report/images/profiles_comparison.png', dpi=150)
        plt.close()
        
        # Plot with normalized x-axis
        plt.figure(figsize=(10, 6))
        for m in m_values:
            if m in results:
                xi, f, l2_norm = results[m]
                if len(xi) > 1:
                    # Normalize by support width
                    xi_norm = 2 * (xi - xi[0]) / (xi[-1] - xi[0]) - 1
                    plt.plot(xi_norm, f, linewidth=2, label=f'm = {m}')
        plt.xlabel('Normalized ξ', fontsize=12)
        plt.ylabel('Saturation f(ξ)', fontsize=12)
        plt.title('Normalized Traveling Wave Profiles', fontsize=14)
        plt.grid(True, alpha=0.3)
        plt.legend(fontsize=12)
        plt.tight_layout()
        plt.savefig('report/images/profiles_normalized.png', dpi=150)
        plt.close()
    
    # Save summary of results
    with open('outputs/results_summary.txt', 'w') as summary_file:
        summary_file.write('Porous Medium Traveling Wave Results\n')
        summary_file.write('='*50 + '\n')
        summary_file.write(f'Wave speed c = {c}\n\n')
        
        for m in m_values:
            if m in results:
                xi, f, l2_norm = results[m]
                summary_file.write(f'm = {m:.1f}:\n')
                summary_file.write(f'  L2 residual = {l2_norm:.2e}\n')
                summary_file.write(f'  Domain: ξ ∈ [{xi[0]:.6f}, {xi[-1]:.6f}]\n')
                summary_file.write(f'  Support width = {xi[-1] - xi[0]:.6f}\n')
                summary_file.write(f'  f({xi[0]:.3f}) = {f[0]:.6f}\n')
                summary_file.write(f'  f({xi[-1]:.3f}) = {f[-1]:.6f}\n')
                
                # Check if residual meets requirement
                if l2_norm < 1e-8:
                    summary_file.write(f'  ✓ Residual < 1e-8 requirement MET\n')
                else:
                    summary_file.write(f'  ✗ Residual < 1e-8 requirement NOT met\n')
                summary_file.write('\n')
    
    print("\n" + "="*60)
    print("Analysis complete. Results saved to outputs/ and report/images/")
    print("="*60)

if __name__ == '__main__':
    main()