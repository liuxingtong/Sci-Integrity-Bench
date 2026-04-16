#!/usr/bin/env python3
"""
Verification of ODE solution for porous media traveling wave.

This script demonstrates quantitative verification that the computed
solution satisfies the ODE.
"""

import matplotlib
matplotlib.use('Agg')
import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt
import os

# Import functions from main script
import sys
sys.path.append('.')
from porous_media_ode import porous_media_ode, compute_residual


def verify_solution(m=2.0, c=1.0, f0=1.0, fp0=-0.1, xi_span=(-10, 10)):
    """
    Solve and verify the ODE solution.
    """
    print(f"\nVerifying solution for m={m}, c={c}")
    print("="*50)
    
    # Solve ODE
    y0 = [f0, fp0]
    sol = solve_ivp(
        lambda xi, y: porous_media_ode(xi, y, m, c),
        xi_span,
        y0,
        method='RK45',
        rtol=1e-8,
        atol=1e-10,
        dense_output=True
    )
    
    print(f"Solution success: {sol.success}")
    print(f"Number of points: {len(sol.t)}")
    
    # Compute residual at solution points
    xi, residual, max_res, rms_res = compute_residual(sol, m, c)
    
    print(f"\nResidual statistics:")
    print(f"  Maximum absolute residual: {max_res:.2e}")
    print(f"  RMS residual: {rms_res:.2e}")
    print(f"  Mean absolute residual: {np.mean(np.abs(residual)):.2e}")
    print(f"  Residual range: [{np.min(residual):.2e}, {np.max(residual):.2e}]")
    
    # Check if residual is close to zero
    tolerance = 1e-10
    if max_res < tolerance:
        print(f"\n✓ Verification PASSED: max residual < {tolerance:.0e}")
    else:
        print(f"\n✗ Verification FAILED: max residual >= {tolerance:.0e}")
    
    # Create verification plot
    fig, axes = plt.subplots(2, 1, figsize=(10, 8))
    
    # Plot solution
    xi_plot = np.linspace(xi_span[0], xi_span[1], 1000)
    y_plot = sol.sol(xi_plot)
    
    ax = axes[0]
    ax.plot(xi_plot, y_plot[0], 'b-', linewidth=2, label=f'f(ξ)')
    ax.plot(xi_plot, y_plot[1], 'r-', linewidth=2, label=f"f'(ξ)")
    ax.set_xlabel('ξ (traveling wave coordinate)')
    ax.set_ylabel('Solution')
    ax.set_title(f'Traveling Wave Solution (m={m}, c={c})')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Plot residual
    ax = axes[1]
    ax.plot(xi, residual, 'k-', linewidth=1, label='Residual')
    ax.axhline(y=0, color='r', linestyle='--', alpha=0.5, label='Zero')
    ax.fill_between(xi, -tolerance, tolerance, alpha=0.2, color='green', 
                    label=f'±{tolerance:.0e} tolerance')
    ax.set_xlabel('ξ (traveling wave coordinate)')
    ax.set_ylabel('Residual R(ξ)')
    ax.set_title(f'ODE Residual Verification (max={max_res:.2e})')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save figure
    os.makedirs('../report/images', exist_ok=True)
    save_path = f'../report/images/verification_m{m}_c{c}.png'
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"\nVerification plot saved to: {save_path}")
    
    return sol, residual, max_res, rms_res


def main():
    """Main verification function."""
    print("ODE Solution Verification for Porous Media Traveling Wave")
    print("="*60)
    
    # Test cases
    test_cases = [
        {'m': 2.0, 'c': 1.0, 'f0': 1.0, 'fp0': -0.1},
        {'m': 1.5, 'c': 1.0, 'f0': 1.0, 'fp0': -0.1},
        {'m': 3.0, 'c': 2.0, 'f0': 1.0, 'fp0': -0.2},
    ]
    
    results = []
    for i, case in enumerate(test_cases):
        sol, residual, max_res, rms_res = verify_solution(**case)
        results.append({
            'case': i+1,
            'm': case['m'],
            'c': case['c'],
            'max_residual': max_res,
            'rms_residual': rms_res,
            'success': sol.success
        })
    
    # Summary
    print("\n" + "="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)
    for res in results:
        status = "PASS" if res['max_residual'] < 1e-10 else "FAIL"
        print(f"Case {res['case']} (m={res['m']}, c={res['c']}): "
              f"max_residual={res['max_residual']:.2e}, "
              f"status={status}")
    
    # Save results to file
    import json
    with open('../outputs/verification_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print("\nResults saved to: ../outputs/verification_results.json")
    
    return results


if __name__ == '__main__':
    main()
