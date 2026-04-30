# PorousMediumTravelingWave
# Numerical integration of traveling-wave ODE arising from the porous medium equation.
#
# PDE model: u_t = (u^m)_{xx}, m>1.
# Traveling wave: u(x,t)=f(\xi), \xi = x - c t.
# ODE: (f^m)'' + c f' = 0.
# Expanded second-order form:
#   m f^{m-1} f'' + m(m-1) f^{m-2} (f')^2 + c f' = 0.
#
# We integrate the second-order ODE as a first-order system and validate via a discrete residual.

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp


@dataclass
class TWParams:
    m: float = 3.0
    c: float = 1.0
    f0: float = 1.0
    xi0: float = 0.0
    eps_stop: float = 1e-6
    xi_max: float = 2.0
    rtol: float = 1e-10
    atol: float = 1e-12
    method: str = "Radau"
    max_step: float = 1e-2
    n_grid: int = 2000


def rhs_second_order(xi: float, y: np.ndarray, m: float, c: float) -> np.ndarray:
    """y = [f, fp]."""
    f, fp = y
    # Avoid division by zero in the RHS when f becomes extremely small.
    f_safe = max(f, 1e-300)

    # From: m f^{m-1} f'' + m(m-1) f^{m-2} (f')^2 + c f' = 0
    # => f'' = -(m-1)*(f')^2/f - (c/m)*f' / f^{m-1}
    fpp = -(m - 1.0) * (fp * fp) / f_safe - (c / m) * fp / (f_safe ** (m - 1.0))
    return np.array([fp, fpp], dtype=float)


def analytic_profile(xi: np.ndarray, m: float, c: float, f0: float = 1.0, xi0: float = 0.0) -> np.ndarray:
    """Analytic compactly-supported traveling wave associated with integration constant K=0.

    From integrated ODE: (f^m)' + c f = 0 => m f^{m-1} f' + c f = 0.
    Solution with f(xi0)=f0:
      f(xi)^{m-1} = f0^{m-1} - (c (m-1)/m) (xi-xi0)
    and f=0 beyond the front.
    """
    s = f0 ** (m - 1.0) - (c * (m - 1.0) / m) * (xi - xi0)
    s_pos = np.maximum(s, 0.0)
    return s_pos ** (1.0 / (m - 1.0))


def compute_residual_uniform_grid(xi: np.ndarray, f: np.ndarray, c: float, m: float) -> dict:
    """Compute discrete residual R = (f^m)'' + c f' on a uniform grid."""
    # Ensure uniform spacing for stable gradient-based second derivatives
    dx = float(xi[1] - xi[0])
    q = f ** m
    fp = np.gradient(f, dx, edge_order=2)
    q_x = np.gradient(q, dx, edge_order=2)
    q_xx = np.gradient(q_x, dx, edge_order=2)
    R = q_xx + c * fp

    # Metrics
    l2 = float(np.sqrt(np.mean(R * R)))
    linf = float(np.max(np.abs(R)))
    denom = float(np.max(np.abs(q_xx) + np.abs(c * fp)) + 1e-300)
    rel_l2 = float(l2 / denom)
    rel_linf = float(linf / denom)

    return {
        "dx": dx,
        "fp": fp,
        "q_xx": q_xx,
        "residual": R,
        "l2": l2,
        "linf": linf,
        "rel_l2": rel_l2,
        "rel_linf": rel_linf,
    }


def integrate_tw(params: TWParams) -> dict:
    m, c = params.m, params.c

    # Initial slope from integrated condition (f^m)' + c f = 0 at xi0.
    fp0 = -c / (m * (params.f0 ** (m - 1.0)))
    y0 = np.array([params.f0, fp0], dtype=float)

    def event_f_hits_eps(xi, y):
        return y[0] - params.eps_stop

    event_f_hits_eps.terminal = True
    event_f_hits_eps.direction = -1

    sol = solve_ivp(
        fun=lambda xi, y: rhs_second_order(xi, y, m=m, c=c),
        t_span=(params.xi0, params.xi_max),
        y0=y0,
        method=params.method,
        rtol=params.rtol,
        atol=params.atol,
        max_step=params.max_step,
        events=event_f_hits_eps,
        dense_output=True,
    )

    xi_end = sol.t_events[0][0] if len(sol.t_events[0]) else sol.t[-1]
    xi_grid = np.linspace(params.xi0, xi_end, params.n_grid)
    y_grid = sol.sol(xi_grid)
    f_grid = y_grid[0]
    fp_grid = y_grid[1]

    # Analytic reference for K=0 compact front
    f_ref = analytic_profile(xi_grid, m=m, c=c, f0=params.f0, xi0=params.xi0)

    # Error against analytic (over computed domain)
    err = f_grid - f_ref
    err_l2 = float(np.sqrt(np.mean(err * err)))
    err_linf = float(np.max(np.abs(err)))

    # ODE residual on uniform grid
    res = compute_residual_uniform_grid(xi_grid, f_grid, c=c, m=m)

    # Additional check: first-order integrated relation G = (f^m)' + c f should be ~0
    dx = res["dx"]
    q = f_grid ** m
    q_x = np.gradient(q, dx, edge_order=2)
    G = q_x + c * f_grid
    G_l2 = float(np.sqrt(np.mean(G * G)))
    G_linf = float(np.max(np.abs(G)))

    # Theoretical front position for analytic solution
    xi_front = params.xi0 + (m / (c * (m - 1.0))) * (params.f0 ** (m - 1.0))

    out = {
        "params": asdict(params),
        "solver": {
            "success": bool(sol.success),
            "status": int(sol.status),
            "message": sol.message,
            "nfev": int(sol.nfev),
            "njev": int(getattr(sol, "njev", 0) or 0),
            "nlu": int(getattr(sol, "nlu", 0) or 0),
            "t_start": float(sol.t[0]),
            "t_end": float(sol.t[-1]),
            "xi_end_event": float(xi_end),
        },
        "xi_front_theory": float(xi_front),
        "grid": {
            "xi": xi_grid,
            "f": f_grid,
            "fp_from_ivp": fp_grid,
            "f_ref": f_ref,
            "error": err,
        },
        "residual": {
            "l2": res["l2"],
            "linf": res["linf"],
            "rel_l2": res["rel_l2"],
            "rel_linf": res["rel_linf"],
            "dx": res["dx"],
            "R": res["residual"],
            "fp_fd": res["fp"],
        },
        "integrated_check": {
            "G_l2": G_l2,
            "G_linf": G_linf,
            "G": G,
        },
        "analytic_error": {
            "err_l2": err_l2,
            "err_linf": err_linf,
        },
    }
    return out


def save_outputs(out: dict, out_dir: str | Path) -> None:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Save arrays to npz
    xi = out["grid"]["xi"]
    f = out["grid"]["f"]
    fp_ivp = out["grid"]["fp_from_ivp"]
    f_ref = out["grid"]["f_ref"]
    err = out["grid"]["error"]
    R = out["residual"]["R"]
    fp_fd = out["residual"]["fp_fd"]
    G = out["integrated_check"]["G"]

    np.savez_compressed(
        out_dir / "tw_solution.npz",
        xi=xi,
        f=f,
        fp_ivp=fp_ivp,
        fp_fd=fp_fd,
        f_ref=f_ref,
        err=err,
        residual=R,
        integrated_G=G,
        params=json.dumps(out["params"]),
    )

    # Save summary json (no huge arrays)
    summary = {
        "params": out["params"],
        "solver": out["solver"],
        "xi_front_theory": out["xi_front_theory"],
        "residual": {k: out["residual"][k] for k in ["l2", "linf", "rel_l2", "rel_linf", "dx"]},
        "integrated_check": {k: out["integrated_check"][k] for k in ["G_l2", "G_linf"]},
        "analytic_error": out["analytic_error"],
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))


if __name__ == "__main__":
    params = TWParams()
    out = integrate_tw(params)
    save_outputs(out, "outputs")
    print(json.dumps({
        "solver": out["solver"],
        "residual": {k: out["residual"][k] for k in ["l2", "linf", "rel_l2", "rel_linf"]},
        "integrated_check": out["integrated_check"],
        "analytic_error": out["analytic_error"],
        "xi_front_theory": out["xi_front_theory"],
    }, indent=2))
