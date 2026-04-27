#!/usr/bin/env python3
"""Numerical integration of porous-medium traveling-wave ODE.

Model PDE (porous medium equation, PME):
    u_t = (u^m)_{xx},   m>1.

Traveling wave u(x,t)=f(\xi), \xi=x-c t gives ODE:
    (f^m)'' + c f' = 0.
Integrating once yields
    (f^m)' + c f = A.
For a right state f(\infty)=u_R with (f^m)'->0, A=c u_R.
Here we focus on a saturation front from u_L=1 to u_R=0, so A=0:
    (f^m)' = -c f.
Equivalently, first-order ODE:
    f' = -(c/m) f^{2-m}.

We integrate this first-order ODE until f reaches ~0, then verify the
second-order ODE residual on the smooth region where f is away from 0.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass
class Solution:
    xi: np.ndarray
    f: np.ndarray
    c: float
    m: float
    xi0: float
    f0: float
    eps_stop: float


def rhs_first_order(xi: float, y: np.ndarray, c: float, m: float) -> np.ndarray:
    f = float(y[0])
    # Guard against negative due to numerical noise.
    f = max(f, 0.0)
    return np.array([-(c / m) * (f ** (2.0 - m))])


def analytic_front(xi: np.ndarray, c: float, m: float, xi0: float, f0: float) -> np.ndarray:
    """Analytic solution to (f^m)' = -c f with initial f(xi0)=f0.

    For m != 1:
        f^{m-1} = f0^{m-1} - (m-1)c/m (xi-xi0)
    and f is clipped at 0.
    """
    if abs(m - 1.0) < 1e-14:
        raise ValueError("m must be >1 for porous medium; analytic formula here assumes m!=1")
    z = (f0 ** (m - 1.0)) - ((m - 1.0) * c / m) * (xi - xi0)
    f = np.where(z > 0.0, z ** (1.0 / (m - 1.0)), 0.0)
    return f


def integrate_front(c: float, m: float, xi0: float, f0: float, xi_max: float, eps_stop: float,
                    rtol: float, atol: float, max_step: float | None) -> Solution:
    from scipy.integrate import solve_ivp

    def event_reach_eps(xi, y):
        return y[0] - eps_stop

    event_reach_eps.terminal = True
    event_reach_eps.direction = -1

    sol = solve_ivp(
        fun=lambda xi, y: rhs_first_order(xi, y, c=c, m=m),
        t_span=(xi0, xi_max),
        y0=np.array([f0], dtype=float),
        method="RK45",
        rtol=rtol,
        atol=atol,
        max_step=max_step,
        events=event_reach_eps,
        dense_output=False,
    )
    xi = sol.t
    f = sol.y[0]

    # If event did not trigger, append xi_max.
    return Solution(xi=xi, f=f, c=c, m=m, xi0=xi0, f0=f0, eps_stop=eps_stop)


def compute_residuals(sol: Solution, n_grid: int = 2000, f_min_resid: float = 1e-4) -> dict:
    """Compute residuals of both integrated and original ODE.

    Residual definitions (using spline differentiation on a uniform grid):
        r1(\xi) = (f^m)' + c f  (should be 0)
        r2(\xi) = (f^m)'' + c f' (should be 0)

    Residual norms are reported over {\xi: f(\xi) >= f_min_resid}.
    """
    from scipy.interpolate import CubicSpline

    xi = sol.xi
    f = sol.f

    # Build uniform grid for diagnostics.
    xi_u = np.linspace(xi.min(), xi.max(), n_grid)

    # Cubic spline fit of f on the computed nodes.
    # We expect a smooth profile for m=2; for m>2 it becomes sharp near the front.
    cs_f = CubicSpline(xi, f, bc_type="natural")
    f_u = cs_f(xi_u)
    fp_u = cs_f(xi_u, 1)

    g_u = f_u ** sol.m
    # Spline g for derivatives of f^m.
    cs_g = CubicSpline(xi_u, g_u, bc_type="natural")
    gp_u = cs_g(xi_u, 1)
    gpp_u = cs_g(xi_u, 2)

    r1 = gp_u + sol.c * f_u
    r2 = gpp_u + sol.c * fp_u

    mask = f_u >= f_min_resid
    if not np.any(mask):
        raise RuntimeError("No points satisfy f>=f_min_resid; adjust f_min_resid or integration range")

    def norms(r):
        r_m = r[mask]
        # L2 over xi via trapezoid normalization by interval length.
        L = xi_u[mask][-1] - xi_u[mask][0]
        l2 = np.sqrt(np.trapz(r_m**2, xi_u[mask]) / max(L, 1e-300))
        linf = np.max(np.abs(r_m))
        return float(l2), float(linf)

    r1_l2, r1_linf = norms(r1)
    r2_l2, r2_linf = norms(r2)

    return {
        "xi_u": xi_u,
        "f_u": f_u,
        "fp_u": fp_u,
        "g_u": g_u,
        "r1": r1,
        "r2": r2,
        "mask": mask,
        "norms": {
            "r1_L2": r1_l2,
            "r1_Linf": r1_linf,
            "r2_L2": r2_l2,
            "r2_Linf": r2_linf,
            "f_min_resid": float(f_min_resid),
        },
    }


def save_figures(sol: Solution, diag: dict, outdir: Path, prefix: str = "") -> dict:
    import matplotlib.pyplot as plt

    outdir.mkdir(parents=True, exist_ok=True)

    xi_u = diag["xi_u"]
    f_u = diag["f_u"]
    mask = diag["mask"]

    # Analytic reference
    f_an = analytic_front(xi_u, c=sol.c, m=sol.m, xi0=sol.xi0, f0=sol.f0)

    figs = {}

    # Profile
    plt.figure(figsize=(6.2, 3.8))
    plt.plot(sol.xi, sol.f, "o", ms=3, label="solve_ivp nodes")
    plt.plot(xi_u, f_u, "-", lw=2, label="spline interpolant")
    plt.plot(xi_u, f_an, "--", lw=2, label="analytic")
    plt.xlabel(r"$\\xi$")
    plt.ylabel(r"$f(\\xi)$")
    plt.title(f"PME traveling-wave front: m={sol.m:g}, c={sol.c:g}")
    plt.ylim(-0.05, 1.05 * max(sol.f0, 1.0))
    plt.grid(True, alpha=0.3)
    plt.legend(frameon=False)
    fn = outdir / f"{prefix}profile.png"
    plt.tight_layout()
    plt.savefig(fn, dpi=200)
    plt.close()
    figs["profile"] = str(fn)

    # Residuals
    r1 = diag["r1"]
    r2 = diag["r2"]
    plt.figure(figsize=(6.2, 3.8))
    plt.semilogy(xi_u[mask], np.abs(r1[mask]) + 1e-300, label=r"$|r_1|=|(f^m)'+cf|$")
    plt.semilogy(xi_u[mask], np.abs(r2[mask]) + 1e-300, label=r"$|r_2|=|(f^m)''+cf'|$")
    plt.xlabel(r"$\\xi$")
    plt.ylabel("absolute residual (masked region)")
    plt.title("ODE residual diagnostics (excluding near-front region)")
    plt.grid(True, which="both", alpha=0.3)
    plt.legend(frameon=False)
    fn = outdir / f"{prefix}residuals.png"
    plt.tight_layout()
    plt.savefig(fn, dpi=200)
    plt.close()
    figs["residuals"] = str(fn)

    # Error vs analytic
    err = f_u - f_an
    plt.figure(figsize=(6.2, 3.8))
    plt.plot(xi_u, err, lw=2)
    plt.axhline(0.0, color="k", lw=1)
    plt.xlabel(r"$\\xi$")
    plt.ylabel(r"$f_{num}-f_{analytic}$")
    plt.title("Numerical error vs analytic traveling-wave profile")
    plt.grid(True, alpha=0.3)
    fn = outdir / f"{prefix}error_vs_analytic.png"
    plt.tight_layout()
    plt.savefig(fn, dpi=200)
    plt.close()
    figs["error_vs_analytic"] = str(fn)

    return figs


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--m", type=float, default=2.0, help="porous medium exponent m>1")
    p.add_argument("--c", type=float, default=1.0, help="traveling wave speed c")
    p.add_argument("--xi0", type=float, default=-5.0, help="starting xi")
    p.add_argument("--xi_max", type=float, default=20.0, help="max xi to integrate to")
    p.add_argument("--f0", type=float, default=1.0, help="initial f(xi0)")
    p.add_argument("--eps_stop", type=float, default=1e-10, help="stop integration when f hits eps_stop")
    p.add_argument("--rtol", type=float, default=1e-10)
    p.add_argument("--atol", type=float, default=1e-12)
    p.add_argument("--max_step", type=float, default=0.05)
    p.add_argument("--n_grid", type=int, default=3000)
    p.add_argument("--f_min_resid", type=float, default=1e-6)
    p.add_argument("--out_npz", type=str, default="outputs/solution.npz")
    p.add_argument("--out_metrics", type=str, default="outputs/metrics.json")
    p.add_argument("--fig_dir", type=str, default="report/images")
    args = p.parse_args()

    sol = integrate_front(
        c=args.c,
        m=args.m,
        xi0=args.xi0,
        f0=args.f0,
        xi_max=args.xi_max,
        eps_stop=args.eps_stop,
        rtol=args.rtol,
        atol=args.atol,
        max_step=args.max_step,
    )

    diag = compute_residuals(sol, n_grid=args.n_grid, f_min_resid=args.f_min_resid)

    # Save arrays
    out_npz = Path(args.out_npz)
    out_npz.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        out_npz,
        xi=sol.xi,
        f=sol.f,
        xi_u=diag["xi_u"],
        f_u=diag["f_u"],
        r1=diag["r1"],
        r2=diag["r2"],
        mask=diag["mask"].astype(np.uint8),
        m=sol.m,
        c=sol.c,
        xi0=sol.xi0,
        f0=sol.f0,
        eps_stop=sol.eps_stop,
    )

    figs = save_figures(sol, diag, outdir=Path(args.fig_dir))

    metrics = {
        "model": {
            "PDE": "u_t = (u^m)_{xx}",
            "traveling_wave": "u(x,t)=f(x-ct)",
            "ODE_second_order": "(f^m)'' + c f' = 0",
            "ODE_first_order_A0": "(f^m)' + c f = 0",
            "first_order_explicit": "f' = -(c/m) f^{2-m}",
        },
        "params": {
            "m": sol.m,
            "c": sol.c,
            "xi0": sol.xi0,
            "f0": sol.f0,
            "xi_max": float(sol.xi.max()),
            "eps_stop": sol.eps_stop,
            "rtol": args.rtol,
            "atol": args.atol,
            "max_step": args.max_step,
            "n_grid": args.n_grid,
            "f_min_resid": args.f_min_resid,
        },
        "diagnostics": {
            **diag["norms"],
            "n_ivp_points": int(sol.xi.size),
        },
        "figures": figs,
    }

    out_metrics = Path(args.out_metrics)
    out_metrics.parent.mkdir(parents=True, exist_ok=True)
    out_metrics.write_text(json.dumps(metrics, indent=2))

    print(json.dumps(metrics["diagnostics"], indent=2))


if __name__ == "__main__":
    main()
