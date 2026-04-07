import numpy as np
import matplotlib.pyplot as plt
import os

# Porous medium equation traveling wave solution
# The equation: ∂u/∂t = ∂/∂x (u^m ∂u/∂x)
# Traveling wave: u(x,t) = f(ξ), ξ = x - ct
# Reduces to: (f^m f')' + c f' = 0
# Integrate once: f^m f' + c f = A
# For boundary conditions f → 0 as ξ → ∞, f' → 0, so A = 0
# Thus: f^m f' + c f = 0 => f' = -c f^{1-m}

# This first-order ODE can be solved analytically:
# ∫ f^{m-1} df = -c ∫ dξ
# (1/m) f^m = -c ξ + constant
# f(ξ) = [max(0, C - m*c*ξ)]^{1/m}

# But the standard Barenblatt solution (self-similar) is different.
# Actually, the traveling wave for porous medium equation with m>1
# has compact support and is given by:
# f(ξ) = [max(0, A - B*ξ^2)]^{1/(m-1)}

def analytical_solution(xi, m, c=1):
    """Analytical traveling wave solution for porous medium equation.
    
    Parameters:
    xi : array-like, traveling wave coordinate ξ = x - ct
    m : exponent in porous medium equation (m > 1)
    c : wave speed
    
    Returns:
    f : solution profile
    """
    # The solution has compact support
    # f(ξ) = [max(0, 1 - k*ξ^2)]^{1/(m-1)} where k = (m-1)/(2m(m+1)) * c
    k = (m-1) / (2*m*(m+1)) * c
    inside = 1 - k * xi**2
    inside = np.maximum(inside, 0)
    return inside**(1/(m-1))

def compute_residual(xi, f, m, c):
    """Compute residual of the ODE: f^m f' + c f = 0."""
    f_prime = np.gradient(f, xi)
    residual = f**m * f_prime + c * f
    # Handle points where f ≈ 0
    mask = f < 1e-12
    residual[mask] = 0
    return residual

def main():
    """Main function to compute and analyze traveling wave profiles."""
    # Parameters
    m_values = [2, 3, 4, 5]
    c_values = [0.5, 1.0, 2.0]
    
    # Create directories
    os.makedirs('outputs', exist_ok=True)
    os.makedirs('report/images', exist_ok=True)
    
    # Plot 1: Profiles for different m values (c=1)
    plt.figure(figsize=(12, 8))
    
    for i, m in enumerate(m_values):
        # Determine domain based on compact support
        # Support ends where 1 - k*ξ^2 = 0 => ξ = ±1/√k
        k = (m-1) / (2*m*(m+1))
        xi_max = 1.5 / np.sqrt(k) if k > 0 else 10
        xi = np.linspace(-xi_max, xi_max, 1000)
        
        f = analytical_solution(xi, m, c=1.0)
        
        # Compute residual
        residual = compute_residual(xi, f, m, 1.0)
        l2_norm = np.sqrt(np.trapz(residual**2, xi))
        print(f"m={m}, c=1.0: L2 residual = {l2_norm:.2e}")
        
        # Save data
        np.savetxt(f'outputs/profile_m{m}_c1.0.txt',
                  np.column_stack((xi, f, residual)),
                  header=f'Traveling wave profile for m={m}, c=1.0\nxi f residual')
        
        # Plot
        plt.subplot(2, 3, i+1)
        plt.plot(xi, f, 'b-', linewidth=2)
        plt.xlabel(r'$\xi = x - ct$')
        plt.ylabel(r'$f(\xi)$')
        plt.title(f'm = {m}, c = 1.0')
        plt.grid(True, alpha=0.3)
        
        # Mark compact support
        support_edge = 1 / np.sqrt(k)
        plt.axvline(x=support_edge, color='r', linestyle='--', alpha=0.5, linewidth=1)
        plt.axvline(x=-support_edge, color='r', linestyle='--', alpha=0.5, linewidth=1)
        
        # Plot residual in subplot
        plt.subplot(2, 3, 5)
        plt.plot(xi, residual, '-', label=f'm={m}')
    
    plt.subplot(2, 3, 5)
    plt.xlabel(r'$\xi$')
    plt.ylabel('Residual')
    plt.title('ODE residuals (c=1.0)')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Plot 6: Wave speed dependence for m=2
    m = 2
    plt.subplot(2, 3, 6)
    for c in c_values:
        k = (m-1) / (2*m*(m+1)) * c
        xi_max = 1.5 / np.sqrt(k) if k > 0 else 10
        xi = np.linspace(-xi_max, xi_max, 1000)
        f = analytical_solution(xi, m, c)
        plt.plot(xi, f, '-', linewidth=2, label=f'c={c}')
    
    plt.xlabel(r'$\xi = x - ct$')
    plt.ylabel(r'$f(\xi)$')
    plt.title(f'Wave speed variation (m={m})')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    plt.tight_layout()
    plt.savefig('report/images/traveling_wave_analysis.png', dpi=300, bbox_inches='tight')
    
    # Plot 2: 3D surface of profiles
    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111, projection='3d')
    
    xi_global = np.linspace(-5, 5, 200)
    for m in m_values:
        f = analytical_solution(xi_global, m, 1.0)
        ax.plot(xi_global, m * np.ones_like(xi_global), f, linewidth=2, label=f'm={m}')
    
    ax.set_xlabel(r'$\xi$')
    ax.set_ylabel('m')
    ax.set_zlabel(r'$f(\xi)$')
    ax.set_title('Traveling wave profiles for different m values')
    ax.legend()
    plt.savefig('report/images/3d_profiles.png', dpi=300, bbox_inches='tight')
    
    # Plot 3: Compact support visualization
    plt.figure(figsize=(10, 6))
    colors = plt.cm.viridis(np.linspace(0, 1, len(m_values)))
    
    for idx, m in enumerate(m_values):
        k = (m-1) / (2*m*(m+1))
        support_edge = 1 / np.sqrt(k)
        xi = np.linspace(-support_edge, support_edge, 400)
        f = analytical_solution(xi, m, 1.0)
        
        plt.plot(xi, f, color=colors[idx], linewidth=2, label=f'm={m}')
        plt.fill_between(xi, 0, f, color=colors[idx], alpha=0.2)
        
        # Mark support edge
        plt.axvline(x=support_edge, color=colors[idx], linestyle=':', alpha=0.5)
        plt.axvline(x=-support_edge, color=colors[idx], linestyle=':', alpha=0.5)
    
    plt.xlabel(r'$\xi = x - ct$')
    plt.ylabel(r'$f(\xi)$')
    plt.title('Compact support of traveling waves (c=1.0)')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig('report/images/compact_support.png', dpi=300, bbox_inches='tight')
    
    print("\nAnalysis complete. Figures saved to report/images/")

if __name__ == '__main__':
    main()