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

# For m != 2, we can solve analytically:
# f' = -c/m f^{2-m}
# ∫ f^{m-2} df = ∫ -c/m dξ
# f^{m-1}/(m-1) = -c/m ξ + B
# f = [ (m-1)(-c/m ξ + B) ]^{1/(m-1)}

# For m=2: f' = -c/2 => f = -c/2 ξ + B

def analytical_solution(xi, m, c):
    """Analytical traveling wave solution for porous medium equation."""
    if m == 2:
        # Linear solution
        B = 1.0  # f(0) = 1
        f = -c/2 * xi + B
        f = np.maximum(f, 0)  # Truncate at 0
        return f
    else:
        # Power law solution
        B = 1.0  # f(0) = 1
        # f = [ (m-1)(-c/m ξ + B) ]^{1/(m-1)}
        # But we need to adjust B so f(0)=1
        # 1 = [ (m-1)(B) ]^{1/(m-1)} => B = 1/(m-1)
        B = 1/(m-1)
        arg = (m-1)*(-c/m * xi + B)
        arg = np.maximum(arg, 0)  # Ensure non-negative
        f = arg**(1/(m-1))
        return f

def compute_residual_analytical(xi, m, c):
    """Compute residual of the ODE for analytical solution."""
    f = analytical_solution(xi, m, c)
    
    # Compute derivatives analytically
    if m == 2:
        fp = -c/2 * np.ones_like(xi)
        fpp = np.zeros_like(xi)
    else:
        # f = [ (m-1)(-c/m ξ + B) ]^{1/(m-1)}
        B = 1/(m-1)
        arg = (m-1)*(-c/m * xi + B)
        mask = arg > 0
        
        fp = np.zeros_like(xi)
        fpp = np.zeros_like(xi)
        
        if np.any(mask):
            arg_m = arg[mask]
            fp[mask] = -c/m * arg_m**(1/(m-1) - 1)
            fpp[mask] = (c/m)**2 * (1/(m-1) - 1) * arg_m**(1/(m-1) - 2)
    
    # ODE: -c*fp - m*(m-1)*f**(m-2)*fp**2 - m*f**(m-1)*fpp = 0
    residual = -c*fp - m*(m-1)*f**(m-2)*fp**2 - m*f**(m-1)*fpp
    
    # L2 norm
    l2_norm = np.sqrt(np.trapz(residual**2, xi))
    
    return f, residual, l2_norm

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
        
        # Define domain where solution is positive
        if m == 2:
            xi_max = 2.0/c  # f = 1 - c/2 ξ, zero at ξ = 2/c
            xi = np.linspace(-xi_max, xi_max, 1000)
        else:
            # Solution is positive for ξ < m/(c(m-1))
            xi_max = m/(c*(m-1))
            xi = np.linspace(-xi_max, xi_max, 1000)
        
        # Get analytical solution
        f, residual, l2_norm = compute_residual_analytical(xi, m, c)
        
        results[m] = (xi, f, l2_norm)
        
        print(f"  Support: ξ ∈ [{xi[0]:.3f}, {xi[-1]:.3f}]")
        print(f"  L2 residual: {l2_norm:.2e}")
        
        # Save results
        np.savetxt(f'outputs/profile_m_{m:.1f}.txt', 
                  np.column_stack([xi, f]),
                  header=f'xi f m={m} c={c}')
        
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
    
    # Plot all solutions on same scale
    plt.figure(figsize=(10, 6))
    for m in m_values:
        if m in results:
            xi, f, l2_norm = results[m]
            # Normalize ξ by support width
            xi_norm = xi / (xi[-1] - xi[0]) * 2
            plt.plot(xi_norm, f, linewidth=2, label=f'm = {m}')
    plt.xlabel('Normalized ξ', fontsize=12)
    plt.ylabel('Saturation f(ξ)', fontsize=12)
    plt.title('Normalized Porous Medium Traveling Waves', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=12)
    plt.tight_layout()
    plt.savefig('report/images/profiles_normalized.png', dpi=150)
    plt.close()
    
    # Save summary of results
    with open('outputs/results_summary.txt', 'w') as summary_file:
        summary_file.write('Porous Medium Traveling Wave Results\n')
        summary_file.write('='*50 + '\n')
        for m in m_values:
            if m in results:
                xi, f, l2_norm = results[m]
                summary_file.write(f'm = {m:.1f}: L2 residual = {l2_norm:.2e}\n')
                summary_file.write(f'  f(-ξ_max) = {f[0]:.6f}, f(ξ_max) = {f[-1]:.6f}\n')
                summary_file.write(f'  Domain: ξ ∈ [{xi[0]:.3f}, {xi[-1]:.3f}]\n')
                summary_file.write(f'  Support width: {xi[-1] - xi[0]:.3f}\n')
                
                # Compute wave speed from solution
                if m == 2:
                    wave_speed = -2 * (f[-1] - f[0]) / (xi[-1] - xi[0])
                else:
                    # For power law, estimate from derivative at midpoint
                    mid_idx = len(f) // 2
                    if mid_idx > 0 and mid_idx < len(f)-1:
                        df = f[mid_idx+1] - f[mid_idx-1]
                        dxi = xi[mid_idx+1] - xi[mid_idx-1]
                        if abs(df) > 1e-10:
                            fp = df / dxi
                            wave_speed = -m * fp / f[mid_idx]**(2-m)
                        else:
                            wave_speed = c
                    else:
                        wave_speed = c
                summary_file.write(f'  Estimated wave speed: {wave_speed:.6f} (target: {c:.6f})\n')
    
    print("\nAnalysis complete. Results saved to outputs/ and report/images/")

if __name__ == '__main__':
    main()