import numpy as np
from scipy.integrate import solve_bvp
import matplotlib.pyplot as plt
import os

# Porous medium equation: u_t = (u^m u_x)_x
# Traveling wave: u(x,t) = f(ξ), ξ = x - ct
# ODE: (f^m f')' + c f' = 0
# Integrate once: f^m f' + c f = A
# For boundary conditions: f → 0, f' → 0 as ξ → ∞ gives A = 0
# So: f^m f' + c f = 0
# This is a first-order ODE: f' = -c f^{1-m}

# We can solve this ODE directly:
# df/dξ = -c f^{1-m}
# f^{m-1} df = -c dξ
# Integrate: (1/m) f^m = -c ξ + constant
# f(ξ) = [max(0, C - m*c*ξ)]^{1/m}

# But wait, this gives linear decay, not quadratic.
# Let me re-derive carefully.

# Actually, the standard traveling wave for porous medium equation
# is known to be: f(ξ) = [max(0, A - B*ξ^2)]^{1/(m-1)}
# Let's verify this satisfies the ODE.

def verify_solution():
    """Verify the analytical solution satisfies the ODE."""
    m = 2
    c = 1.0
    
    # Proposed solution: f(ξ) = [max(0, 1 - k*ξ^2)]^{1/(m-1)}
    # For m=2: f(ξ) = max(0, 1 - k*ξ^2)
    k = 1.0/12.0  # Guess
    
    xi = np.linspace(-2, 2, 1000)
    f = np.maximum(0, 1 - k*xi**2)
    
    # Compute derivatives
    f_prime = np.gradient(f, xi)
    f_double_prime = np.gradient(f_prime, xi)
    
    # ODE: (f^m f')' + c f' = 0
    # Compute left side
    lhs = np.gradient(f**m * f_prime, xi) + c * f_prime
    
    print(f"Max residual: {np.max(np.abs(lhs)):.2e}")
    
    # Try to find k that minimizes residual
    from scipy.optimize import minimize
    
    def residual_norm(k_val):
        f_test = np.maximum(0, 1 - k_val*xi**2)
        f_prime_test = np.gradient(f_test, xi)
        lhs_test = np.gradient(f_test**m * f_prime_test, xi) + c * f_prime_test
        return np.sqrt(np.trapz(lhs_test**2, xi))
    
    res = minimize(residual_norm, 0.1, bounds=[(0.001, 1.0)])
    print(f"Optimal k: {res.x[0]:.6f}")
    print(f"Min residual norm: {res.fun:.2e}")
    
    return res.x[0]

# Let me implement a proper numerical solution using the first-order ODE
# f' = -c f^{1-m} for f > 0

def solve_traveling_wave_numerical(m=2, c=1.0, xi_max=10, n_points=1000):
    """Solve traveling wave using the first-order ODE."""
    # We need to solve f' = -c f^{1-m}
    # This is separable
    # f^{m-1} df = -c dξ
    # Integrate from ξ0 to ξ: (1/m) f^m = -c (ξ - ξ0) + constant
    
    # At the front ξ = ξ0, f = 0
    # Let ξ0 be where f = 0
    # Then for ξ < ξ0: f(ξ) = [m*c*(ξ0 - ξ)]^{1/m}
    
    # Choose ξ0 = 0 for simplicity
    xi0 = 0
    
    # For ξ < xi0
    xi_neg = np.linspace(-xi_max, xi0, n_points//2)
    f_neg = (m*c*(xi0 - xi_neg))**(1/m)
    
    # For ξ > xi0, f = 0
    xi_pos = np.linspace(xi0, xi_max, n_points//2)
    f_pos = np.zeros_like(xi_pos)
    
    # Combine
    xi = np.concatenate([xi_neg, xi_pos[1:]])
    f = np.concatenate([f_neg, f_pos[1:]])
    
    return xi, f

def main():
    """Main analysis function."""
    # Create directories
    os.makedirs('outputs', exist_ok=True)
    os.makedirs('report/images', exist_ok=True)
    
    print("Verifying solution...")
    k_opt = verify_solution()
    
    # Parameters
    m_values = [2, 3, 4]
    c = 1.0
    
    # Plot numerical solutions
    plt.figure(figsize=(12, 8))
    
    for i, m in enumerate(m_values):
        print(f"\nAnalyzing m = {m}")
        
        # Numerical solution from first-order ODE
        xi_num, f_num = solve_traveling_wave_numerical(m=m, c=c, xi_max=10)
        
        # Compute residual of first-order ODE: f' + c f^{1-m} = 0
        f_prime = np.gradient(f_num, xi_num)
        residual_fo = f_prime + c * f_num**(1-m)
        # Handle f=0 points
        residual_fo[f_num < 1e-12] = 0
        l2_fo = np.sqrt(np.trapz(residual_fo**2, xi_num))
        print(f"  First-order ODE L2 residual: {l2_fo:.2e}")
        
        # Compute residual of original second-order ODE
        # (f^m f')' + c f' = 0
        fmg = f_num**m * f_prime
        fmg_prime = np.gradient(fmg, xi_num)
        residual_so = fmg_prime + c * f_prime
        residual_so[f_num < 1e-12] = 0
        l2_so = np.sqrt(np.trapz(residual_so**2, xi_num))
        print(f"  Second-order ODE L2 residual: {l2_so:.2e}")
        
        # Save data
        np.savetxt(f'outputs/profile_m{m}_c{c}_numerical.txt',
                  np.column_stack((xi_num, f_num, residual_fo, residual_so)),
                  header=f'Traveling wave profile for m={m}, c={c}\nxi f residual_fo residual_so')
        
        # Plot
        plt.subplot(2, 3, i+1)
        plt.plot(xi_num, f_num, 'b-', linewidth=2)
        plt.xlabel(r'$\xi = x - ct$')
        plt.ylabel(r'$f(\xi)$')
        plt.title(f'Traveling wave (m={m}, c={c})')
        plt.grid(True, alpha=0.3)
        
        # Plot derivative
        plt.subplot(2, 3, i+4)
        plt.plot(xi_num, f_prime, 'r-', linewidth=2)
        plt.xlabel(r'$\xi = x - ct$')
        plt.ylabel(r"$f'(\xi)$")
        plt.title(f'Derivative (m={m})')
        plt.grid(True, alpha=0.3)
        
        # Also try the quadratic solution for comparison
        # f(ξ) = [max(0, 1 - k*ξ^2)]^{1/(m-1)}
        k = (m-1) / (2*m*(m+1)) * c
        xi_quad = np.linspace(-1.5/np.sqrt(k), 1.5/np.sqrt(k), 1000)
        f_quad = np.maximum(0, 1 - k*xi_quad**2)**(1/(m-1))
        
        # Overlay for comparison
        plt.subplot(2, 3, i+1)
        plt.plot(xi_quad, f_quad, 'g--', linewidth=1.5, alpha=0.7, label='Quadratic')
        if i == 0:
            plt.legend()
    
    plt.tight_layout()
    plt.savefig('report/images/numerical_solutions.png', dpi=300, bbox_inches='tight')
    
    # Plot residuals
    plt.figure(figsize=(12, 5))
    
    for i, m in enumerate(m_values):
        # Load data
        data = np.loadtxt(f'outputs/profile_m{m}_c{c}_numerical.txt')
        xi = data[:, 0]
        residual_so = data[:, 3]
        
        plt.subplot(1, 3, i+1)
        plt.plot(xi, residual_so, 'b-', linewidth=1)
        plt.xlabel(r'$\xi$')
        plt.ylabel('Residual')
        plt.title(f'Second-order ODE residual (m={m})')
        plt.grid(True, alpha=0.3)
        plt.ylim([-0.1, 0.1])
    
    plt.tight_layout()
    plt.savefig('report/images/residuals.png', dpi=300, bbox_inches='tight')
    
    # Adaptive step size verification
    print("\n\nAdaptive step size verification:")
    print("="*50)
    
    m = 2
    c = 1.0
    
    # Try different numbers of points
    n_points_list = [100, 200, 500, 1000, 2000]
    
    residuals = []
    
    for n_points in n_points_list:
        xi, f = solve_traveling_wave_numerical(m=m, c=c, xi_max=10, n_points=n_points)
        f_prime = np.gradient(f, xi)
        fmg = f**m * f_prime
        fmg_prime = np.gradient(fmg, xi)
        residual = fmg_prime + c * f_prime
        residual[f < 1e-12] = 0
        
        l2_norm = np.sqrt(np.trapz(residual**2, xi))
        residuals.append(l2_norm)
        
        print(f"n_points = {n_points:4d}: L2 residual = {l2_norm:.2e}")
    
    # Check if we meet the requirement of 1e-8
    min_residual = min(residuals)
    print(f"\nMinimum L2 residual achieved: {min_residual:.2e}")
    if min_residual < 1e-8:
        print("SUCCESS: Requirement of 1e-8 L2 residual is met!")
    else:
        print(f"WARNING: Requirement of 1e-8 L2 residual is NOT met.")
        print(f"Best achieved: {min_residual:.2e}")
    
    # Plot convergence
    plt.figure(figsize=(8, 5))
    plt.loglog(n_points_list, residuals, 'bo-', linewidth=2, markersize=8)
    plt.xlabel('Number of grid points')
    plt.ylabel('L2 residual norm')
    plt.title('Convergence of numerical solution')
    plt.grid(True, alpha=0.3, which='both')
    plt.axhline(y=1e-8, color='r', linestyle='--', label='Target: 1e-8')
    plt.legend()
    plt.tight_layout()
    plt.savefig('report/images/convergence.png', dpi=300, bbox_inches='tight')
    
    print("\nAnalysis complete. All figures saved to report/images/")

if __name__ == '__main__':
    main()