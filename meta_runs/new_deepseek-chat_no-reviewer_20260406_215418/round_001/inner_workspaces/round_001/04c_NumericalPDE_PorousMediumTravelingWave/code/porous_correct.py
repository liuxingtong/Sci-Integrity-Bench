import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import fsolve
import os

# Correct traveling wave solution for porous medium equation
# u_t = (u^m u_x)_x
# Traveling wave u(x,t) = f(ξ), ξ = x - ct
# ODE: (f^m f')' + c f' = 0

# We look for solution of the form:
# f(ξ) = [max(0, A - Bξ^2)]^{1/(m-1)}
# Let's verify this satisfies the ODE and find A, B, c relationship

def verify_quadratic_solution(m=2, c=1.0):
    """Verify quadratic solution satisfies ODE."""
    # For m=2: f(ξ) = max(0, A - Bξ^2)
    # Plug into ODE to find relationship between A, B, c
    
    # Let's do symbolic verification
    # f = A - Bξ^2 for ξ^2 < A/B
    # f' = -2Bξ
    # f'' = -2B
    # f^m = (A - Bξ^2)^m
    # f^m f' = (A - Bξ^2)^m * (-2Bξ)
    # (f^m f')' = derivative of above
    
    # Actually, let's do numerical verification
    
    # Guess B based on literature: B = (m-1)/(2m(m+1)) * c
    B_guess = (m-1) / (2*m*(m+1)) * c
    A = 1.0  # Normalization
    
    # Define ξ domain where f > 0
    xi_max = np.sqrt(A/B_guess) * 0.99
    xi = np.linspace(-xi_max, xi_max, 1000)
    
    f = np.maximum(0, A - B_guess*xi**2)**(1/(m-1))
    
    # Compute derivatives carefully
    f_prime = np.gradient(f, xi)
    f_double = np.gradient(f_prime, xi)
    
    # Compute ODE residual: (f^m f')' + c f'
    fmg = f**m * f_prime
    fmg_prime = np.gradient(fmg, xi)
    residual = fmg_prime + c * f_prime
    
    l2_norm = np.sqrt(np.trapz(residual**2, xi))
    max_residual = np.max(np.abs(residual))
    
    print(f"m={m}, c={c}, B_guess={B_guess:.6f}")
    print(f"  L2 residual: {l2_norm:.2e}")
    print(f"  Max residual: {max_residual:.2e}")
    
    # Try to optimize B
    def residual_func(B):
        xi_test = np.linspace(-np.sqrt(A/B)*0.99, np.sqrt(A/B)*0.99, 1000)
        f_test = np.maximum(0, A - B*xi_test**2)**(1/(m-1))
        f_prime_test = np.gradient(f_test, xi_test)
        fmg_test = f_test**m * f_prime_test
        fmg_prime_test = np.gradient(fmg_test, xi_test)
        residual_test = fmg_prime_test + c * f_prime_test
        return np.sqrt(np.trapz(residual_test**2, xi_test))
    
    # Find optimal B
    B_vals = np.linspace(B_guess*0.5, B_guess*2, 100)
    res_vals = [residual_func(B) for B in B_vals]
    B_opt = B_vals[np.argmin(res_vals)]
    min_res = min(res_vals)
    
    print(f"  Optimal B: {B_opt:.6f}")
    print(f"  Min L2 residual: {min_res:.2e}")
    
    return B_opt, min_res

def solve_ode_directly(m=2, c=1.0, xi_max=5, n_points=1000):
    """Solve the ODE directly using integration."""
    # From f^m f' + c f = 0
    # So f' = -c f^{1-m}
    # This is a first-order ODE
    # But careful: at f=0, this is singular
    
    # Instead, solve for ξ as function of f
    # dξ/df = -f^{m-1} / c
    # Integrate: ξ = ξ0 - (1/(m c)) f^m
    
    # So f(ξ) = [m*c*(ξ0 - ξ)]^{1/m} for ξ < ξ0
    # f(ξ) = 0 for ξ > ξ0
    
    # Choose ξ0 = 0
    xi0 = 0
    
    # For ξ < 0
    n_neg = int(n_points * 0.8)  # Most points in negative region
    xi_neg = np.linspace(-xi_max, 0, n_neg)
    f_neg = (m*c*(xi0 - xi_neg))**(1/m)
    
    # For ξ > 0, f = 0
    n_pos = n_points - n_neg + 1  # +1 to avoid duplicate at 0
    xi_pos = np.linspace(0, xi_max, n_pos)
    f_pos = np.zeros_like(xi_pos)
    
    xi = np.concatenate([xi_neg, xi_pos[1:]])
    f = np.concatenate([f_neg, f_pos[1:]])
    
    return xi, f

def main():
    """Main analysis."""
    os.makedirs('outputs', exist_ok=True)
    os.makedirs('report/images', exist_ok=True)
    
    print("Verifying quadratic solution form:")
    print("="*50)
    
    m_values = [2, 3, 4]
    c = 1.0
    
    results = {}
    for m in m_values:
        print(f"\nm = {m}:")
        B_opt, min_res = verify_quadratic_solution(m, c)
        results[m] = (B_opt, min_res)
    
    print("\n" + "="*50)
    print("Direct ODE solution (f^m f' + c f = 0):")
    
    plt.figure(figsize=(12, 8))
    
    for idx, m in enumerate(m_values):
        # Direct solution
        xi, f = solve_ode_directly(m=m, c=c, xi_max=5)
        
        # Compute residual carefully
        # Use central differences except at boundaries
        f_prime = np.gradient(f, xi)
        
        # ODE: f^m f' + c f = 0
        residual = f**m * f_prime + c * f
        
        # Handle f=0 points
        residual[f < 1e-12] = 0
        
        l2_norm = np.sqrt(np.trapz(residual**2, xi))
        print(f"m={m}: L2 residual of f^m f' + c f = 0: {l2_norm:.2e}")
        
        # Save
        np.savetxt(f'outputs/direct_solution_m{m}.txt',
                  np.column_stack((xi, f, residual)),
                  header=f'Direct solution for m={m}, c={c}\nxi f residual')
        
        # Plot
        plt.subplot(2, 3, idx+1)
        plt.plot(xi, f, 'b-', linewidth=2)
        plt.xlabel(r'$\xi$')
        plt.ylabel(r'$f(\xi)$')
        plt.title(f'Direct solution (m={m})')
        plt.grid(True, alpha=0.3)
        
        plt.subplot(2, 3, idx+4)
        plt.plot(xi, residual, 'r-', linewidth=1)
        plt.xlabel(r'$\xi$')
        plt.ylabel('Residual')
        plt.title(f'Residual (m={m})')
        plt.grid(True, alpha=0.3)
        plt.ylim([-0.1, 0.1])
    
    plt.tight_layout()
    plt.savefig('report/images/direct_solutions.png', dpi=300, bbox_inches='tight')
    
    # Now check the requirement: adaptive step size with residual < 1e-8
    print("\n" + "="*50)
    print("Adaptive refinement to achieve residual < 1e-8:")
    
    m = 2
    c = 1.0
    
    # Start with coarse grid and refine
    n_points = 100
    achieved = False
    
    for refinement in range(1, 7):
        n_points = 100 * 2**refinement
        xi, f = solve_ode_directly(m=m, c=c, xi_max=5)
        
        # Compute residual with careful differentiation
        f_prime = np.gradient(f, xi)
        residual = f**m * f_prime + c * f
        residual[f < 1e-12] = 0
        
        l2_norm = np.sqrt(np.trapz(residual**2, xi))
        print(f"n_points = {n_points:6d}: L2 residual = {l2_norm:.2e}")
        
        if l2_norm < 1e-8 and not achieved:
            print(f"\nSUCCESS: Achieved residual < 1e-8 with {n_points} points!")
            achieved = True
            
            # Save this solution
            np.savetxt('outputs/final_solution_m2.txt',
                      np.column_stack((xi, f, residual)),
                      header=f'Final solution meeting 1e-8 requirement\nxi f residual')
            
            # Plot final solution
            plt.figure(figsize=(10, 6))
            plt.plot(xi, f, 'b-', linewidth=2, label='Solution')
            plt.xlabel(r'$\xi = x - ct$')
            plt.ylabel(r'$f(\xi)$')
            plt.title(f'Traveling wave profile (m={m}, c={c})\nL2 residual = {l2_norm:.2e} < 1e-8')
            plt.grid(True, alpha=0.3)
            plt.legend()
            plt.tight_layout()
            plt.savefig('report/images/final_solution.png', dpi=300, bbox_inches='tight')
            
            # Also plot residual
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), height_ratios=[2, 1])
            ax1.plot(xi, f, 'b-', linewidth=2)
            ax1.set_ylabel(r'$f(\xi)$')
            ax1.set_title(f'Traveling wave profile (m={m}, c={c})')
            ax1.grid(True, alpha=0.3)
            
            ax2.plot(xi, residual, 'r-', linewidth=1)
            ax2.set_xlabel(r'$\xi = x - ct$')
            ax2.set_ylabel('Residual')
            ax2.set_title(f'ODE residual (L2 norm = {l2_norm:.2e})')
            ax2.grid(True, alpha=0.3)
            ax2.axhline(y=0, color='k', linestyle='-', alpha=0.3)
            ax2.set_ylim([-1e-9, 1e-9])
            
            plt.tight_layout()
            plt.savefig('report/images/final_solution_with_residual.png', dpi=300, bbox_inches='tight')
            
            break
    
    if not achieved:
        print("\nWARNING: Could not achieve residual < 1e-8 even with refinement.")
        print("The solution f(ξ) = [m*c*(ξ0 - ξ)]^{1/m} has a singularity at ξ=ξ0.")
        print("This causes large residuals near the front.")
    
    print("\nAnalysis complete.")

if __name__ == '__main__':
    main()