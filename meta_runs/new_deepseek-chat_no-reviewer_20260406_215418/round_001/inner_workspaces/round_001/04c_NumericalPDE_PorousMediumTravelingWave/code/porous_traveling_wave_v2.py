import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import fsolve
import matplotlib.pyplot as plt
import os

# Porous medium traveling wave
# From integration: f^m f' + c f = 0 (assuming boundary conditions)
# So f' = -c f^{1-m}
# This is valid for f > 0
# We need to solve with boundary conditions f(-∞) = 1, f(∞) = 0

# Actually, the traveling wave solution for porous medium equation
# has compact support: f(ξ) = 0 for ξ > ξ0
# The solution is known analytically:
# f(ξ) = [max(0, 1 - (m-1)/(2m(m+1)) * ξ^2)]^{1/(m-1)}
# But let's solve numerically

def porous_ode_first_order(xi, f, m, c):
    """First-order ODE: f' = -c f^{1-m}"""
    eps = 1e-12
    f_safe = max(f, eps)
    if f_safe <= eps:
        return 0.0
    return -c * f_safe**(1-m)

def solve_shooting(m=2, c=1, xi_max=10, tol=1e-8):
    """Solve using shooting method."""
    # We know f(0) should be around some value
    # Let's find f(0) such that f(xi_max) ≈ 0
    
    def objective(f0):
        """Solve IVP from 0 to xi_max with initial condition f(0)=f0."""
        sol = solve_ivp(
            lambda xi, f: porous_ode_first_order(xi, f[0], m, c),
            [0, xi_max],
            [f0],
            method='RK45',
            rtol=1e-10,
            atol=1e-12
        )
        return sol.y[0, -1]  # f(xi_max)
    
    # Find f0 such that f(xi_max) = 0
    # f0 should be between 0 and 1
    f0_guess = 0.5
    f0_solution = fsolve(objective, f0_guess, xtol=tol)[0]
    
    # Now solve forward and backward
    # Forward (0 to xi_max)
    sol_forward = solve_ivp(
        lambda xi, f: porous_ode_first_order(xi, f[0], m, c),
        [0, xi_max],
        [f0_solution],
        method='RK45',
        rtol=1e-10,
        atol=1e-12,
        dense_output=True
    )
    
    # Backward (0 to -xi_max)
    sol_backward = solve_ivp(
        lambda xi, f: porous_ode_first_order(xi, f[0], m, c),
        [0, -xi_max],
        [f0_solution],
        method='RK45',
        rtol=1e-10,
        atol=1e-12,
        dense_output=True
    )
    
    return f0_solution, sol_forward, sol_backward

def analytical_solution(xi, m, c=1):
    """Analytical solution for porous medium traveling wave."""
    # Known solution: f(ξ) = [max(0, A - B*ξ^2)]^{1/(m-1)}
    # where A and B are constants
    # For c=1, the solution is:
    # f(ξ) = [max(0, 1 - (m-1)/(2m(m+1)) * ξ^2)]^{1/(m-1)}
    B = (m-1) / (2*m*(m+1))
    inside = 1 - B * xi**2
    inside = np.maximum(inside, 0)
    return inside**(1/(m-1))

def main():
    """Main function."""
    # Parameters
    m_values = [2, 3, 4]
    c = 1.0
    xi_max = 20
    
    # Create directories
    os.makedirs('outputs', exist_ok=True)
    os.makedirs('report/images', exist_ok=True)
    
    plt.figure(figsize=(12, 8))
    
    for i, m in enumerate(m_values):
        print(f"\nSolving for m = {m}, c = {c}")
        
        # Numerical solution
        f0, sol_forward, sol_backward = solve_shooting(m=m, c=c, xi_max=xi_max)
        print(f"  f(0) = {f0:.6f}")
        
        # Create combined solution
        xi_backward = np.linspace(-xi_max, 0, 200)
        xi_forward = np.linspace(0, xi_max, 200)
        
        f_backward = sol_backward.sol(xi_backward)[0]
        f_forward = sol_forward.sol(xi_forward)[0]
        
        xi_combined = np.concatenate([xi_backward, xi_forward[1:]])
        f_combined = np.concatenate([f_backward, f_forward[1:]])
        
        # Analytical solution
        f_analytical = analytical_solution(xi_combined, m, c)
        
        # Compute residual of first-order ODE
        # f' + c f^{1-m} = 0
        f_prime = np.gradient(f_combined, xi_combined)
        residual = f_prime + c * f_combined**(1-m)
        # Handle points where f ≈ 0
        residual[f_combined < 1e-12] = 0
        
        l2_norm = np.sqrt(np.trapz(residual**2, xi_combined))
        print(f"  L2 residual: {l2_norm:.2e}")
        
        # Save solution
        np.savetxt(f'outputs/profile_m{m}_c{c}_numerical.txt',
                  np.column_stack((xi_combined, f_combined, residual)),
                  header=f'Traveling wave profile for m={m}, c={c}\nxi f residual')
        
        np.savetxt(f'outputs/profile_m{m}_c{c}_analytical.txt',
                  np.column_stack((xi_combined, f_analytical)),
                  header=f'Analytical traveling wave profile for m={m}, c={c}\nxi f')
        
        # Plot numerical vs analytical
        plt.subplot(2, 2, i+1)
        plt.plot(xi_combined, f_combined, 'b-', linewidth=2, label='Numerical')
        plt.plot(xi_combined, f_analytical, 'r--', linewidth=1.5, label='Analytical')
        plt.xlabel(r'$\xi = x - ct$')
        plt.ylabel(r'$f(\xi)$')
        plt.title(f'Traveling wave profile (m={m}, c={c})')
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        # Plot residual
        plt.subplot(2, 2, 4)
        plt.plot(xi_combined, residual, '-', label=f'm={m}')
    
    plt.subplot(2, 2, 4)
    plt.xlabel(r'$\xi$')
    plt.ylabel('Residual')
    plt.title('ODE residuals (first-order)')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    
    plt.savefig('report/images/traveling_wave_profiles_v2.png', dpi=300, bbox_inches='tight')
    plt.savefig('outputs/traveling_wave_profiles_v2.png', dpi=300, bbox_inches='tight')
    
    # Plot compact support
    plt.figure(figsize=(10, 6))
    for m in m_values:
        xi = np.linspace(-10, 10, 1000)
        f_anal = analytical_solution(xi, m, c)
        plt.plot(xi, f_anal, '-', linewidth=2, label=f'm={m}')
    
    plt.xlabel(r'$\xi = x - ct$')
    plt.ylabel(r'$f(\xi)$')
    plt.title('Analytical traveling wave profiles (compact support)')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig('report/images/analytical_profiles.png', dpi=300, bbox_inches='tight')
    plt.savefig('outputs/analytical_profiles.png', dpi=300, bbox_inches='tight')
    
    print("\nAnalysis complete.")

if __name__ == '__main__':
    main()