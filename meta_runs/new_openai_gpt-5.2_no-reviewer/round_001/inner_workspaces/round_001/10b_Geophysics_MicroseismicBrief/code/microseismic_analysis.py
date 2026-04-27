#!/usr/bin/env python
"""Microseismic location + clustering brief

Reads:
  data/stations.csv
  data/arrival_times.csv
Writes:
  outputs/located_events.csv
  outputs/cluster_summary.csv
  outputs/event_residuals.csv
  outputs/velocity_scan.csv
  report/images/*.png

Assumptions:
  - Constant 1-D P-wave velocity (Vp) for travel times.
  - Straight-ray travel times: t = t0 + ||x-x_sta||/Vp.
  - Station coordinate columns are Cartesian in meters.

The script is designed to be robust to mild schema differences in CSV headers.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from scipy.optimize import least_squares

from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors


OUT_DIR = Path("outputs")
IMG_DIR = Path("report/images")
OUT_DIR.mkdir(parents=True, exist_ok=True)
IMG_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class Schema:
    station_id: str
    x: str
    y: str
    z: str
    event_id: str
    pick_time: str


def _pick_first(cols: List[str], candidates: List[str]) -> Optional[str]:
    lower_map = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand in lower_map:
            return lower_map[cand]
    return None


def infer_schema(stations: pd.DataFrame, arrivals: pd.DataFrame) -> Schema:
    st_cols = list(stations.columns)
    ar_cols = list(arrivals.columns)

    station_id = _pick_first(st_cols, ["station", "station_id", "sta", "name", "id"])
    if station_id is None:
        raise ValueError(f"Could not infer station id column from {st_cols}")

    # coordinate columns
    x = _pick_first(st_cols, ["x", "easting", "east", "x_m", "utm_e", "lon", "longitude"])
    y = _pick_first(st_cols, ["y", "northing", "north", "y_m", "utm_n", "lat", "latitude"])
    z = _pick_first(st_cols, ["z", "elev", "elevation", "height", "z_m"])
    if x is None or y is None or z is None:
        # fall back: first three numeric columns excluding id
        numeric = [c for c in st_cols if c != station_id and pd.api.types.is_numeric_dtype(stations[c])]
        if len(numeric) >= 3:
            x, y, z = numeric[:3]
        else:
            raise ValueError(f"Could not infer coordinate columns from {st_cols}")

    event_id = _pick_first(ar_cols, ["event_id", "event", "eid", "id"])
    if event_id is None:
        raise ValueError(f"Could not infer event id column from {ar_cols}")

    pick_time = _pick_first(ar_cols, ["pick_time", "arrival_time", "p_arrival", "t", "time"])
    if pick_time is None:
        # choose first column containing 'time'
        for c in ar_cols:
            if "time" in c.lower():
                pick_time = c
                break
    if pick_time is None:
        raise ValueError(f"Could not infer pick time column from {ar_cols}")

    return Schema(station_id=station_id, x=x, y=y, z=z, event_id=event_id, pick_time=pick_time)


def parse_pick_times(arrivals: pd.DataFrame, pick_col: str) -> np.ndarray:
    """Return pick times as float seconds (arbitrary epoch)."""
    s = arrivals[pick_col]
    if pd.api.types.is_numeric_dtype(s):
        return s.astype(float).to_numpy()

    # Try datetime parsing
    dt = pd.to_datetime(s, errors="coerce", utc=True)
    if dt.notna().mean() > 0.9:
        # seconds since UNIX epoch
        return (dt.view("int64") / 1e9).to_numpy()

    # Try parsing as float in strings
    vals = pd.to_numeric(s, errors="coerce")
    if vals.notna().mean() > 0.9:
        return vals.astype(float).to_numpy()

    raise ValueError(f"Could not parse pick times in column {pick_col}")


def locate_event(
    df_evt: pd.DataFrame,
    st: pd.DataFrame,
    schema: Schema,
    vp: float,
    bounds_pad_xy: float = 500.0,
    bounds_pad_z_up: float = 200.0,
    bounds_pad_z_down: float = 5000.0,
    huber_fscale: float = 0.02,
) -> Optional[Dict]:
    """Locate one event using robust least squares; return dict with solution + diagnostics."""
    # Merge station coords
    merged = df_evt.merge(
        st[[schema.station_id, schema.x, schema.y, schema.z]],
        left_on=schema.station_id,
        right_on=schema.station_id,
        how="inner",
    ).copy()

    if merged.shape[0] < 4:
        return None

    t_obs = merged["_pick_seconds"].to_numpy(dtype=float)
    t_ref = float(np.nanmin(t_obs))
    t_obs_rel = t_obs - t_ref

    xs = merged[schema.x].to_numpy(dtype=float)
    ys = merged[schema.y].to_numpy(dtype=float)
    zs = merged[schema.z].to_numpy(dtype=float)

    # Initial guess
    x0 = float(np.nanmean(xs))
    y0 = float(np.nanmean(ys))
    # Put initial source beneath array
    z0 = float(np.nanmin(zs) - 500.0)
    t00 = float(np.nanmin(t_obs_rel) - 0.05)  # slightly before earliest pick

    # Bounds based on station extents
    xmin, xmax = float(np.nanmin(xs) - bounds_pad_xy), float(np.nanmax(xs) + bounds_pad_xy)
    ymin, ymax = float(np.nanmin(ys) - bounds_pad_xy), float(np.nanmax(ys) + bounds_pad_xy)

    zmax = float(np.nanmax(zs) + bounds_pad_z_up)
    zmin = float(np.nanmin(zs) - bounds_pad_z_down)

    # origin time bounds: allow negative and positive relative times
    tmin, tmax = -10.0, float(np.nanmax(t_obs_rel) + 1.0)

    def residuals(p: np.ndarray) -> np.ndarray:
        x, y, z, t0 = p
        d = np.sqrt((xs - x) ** 2 + (ys - y) ** 2 + (zs - z) ** 2)
        t_pred = t0 + d / vp
        return (t_pred - t_obs_rel)

    p_init = np.array([x0, y0, z0, t00], dtype=float)
    lb = np.array([xmin, ymin, zmin, tmin], dtype=float)
    ub = np.array([xmax, ymax, zmax, tmax], dtype=float)

    try:
        res = least_squares(
            residuals,
            p_init,
            bounds=(lb, ub),
            loss="huber",
            f_scale=huber_fscale,
            max_nfev=2000,
        )
    except Exception:
        return None

    x_hat, y_hat, z_hat, t0_hat = res.x
    r = residuals(res.x)
    rms = float(np.sqrt(np.mean(r**2)))
    mad = float(np.median(np.abs(r - np.median(r))))

    # Covariance estimate (linearized)
    cov_x = cov_y = cov_z = cov_t0 = np.nan
    if res.jac is not None and res.jac.shape[0] >= res.jac.shape[1]:
        J = res.jac
        dof = max(1, J.shape[0] - J.shape[1])
        s2 = float(np.sum(r**2) / dof)
        try:
            JTJ_inv = np.linalg.inv(J.T @ J)
            cov = s2 * JTJ_inv
            cov_x, cov_y, cov_z, cov_t0 = [float(math.sqrt(max(cov[i, i], 0.0))) for i in range(4)]
        except np.linalg.LinAlgError:
            pass

    # Per-pick residuals for diagnostics
    resid_df = merged[[schema.event_id, schema.station_id]].copy()
    resid_df["residual_s"] = r

    out = {
        "event_id": merged[schema.event_id].iloc[0],
        "n_picks": int(merged.shape[0]),
        "x": float(x_hat),
        "y": float(y_hat),
        "z": float(z_hat),
        "t0_seconds": float(t0_hat + t_ref),
        "t_ref_seconds": float(t_ref),
        "rms_s": rms,
        "mad_s": mad,
        "success": bool(res.success),
        "cost": float(res.cost),
        "nfev": int(res.nfev),
        "sigma_x_m": cov_x,
        "sigma_y_m": cov_y,
        "sigma_z_m": cov_z,
        "sigma_t0_s": cov_t0,
        "residuals": resid_df,
    }
    return out


def velocity_scan(
    arrivals: pd.DataFrame,
    stations: pd.DataFrame,
    schema: Schema,
    vp_grid: np.ndarray,
    max_events: int = 25,
) -> pd.DataFrame:
    """Coarse global Vp scan by locating a subset of events and minimizing median RMS."""
    # Choose events with most picks
    g = arrivals.groupby(schema.event_id).size().sort_values(ascending=False)
    evt_ids = g.head(max_events).index.to_list()

    rows = []
    for vp in vp_grid:
        rms_list = []
        n_loc = 0
        for eid in evt_ids:
            df_evt = arrivals[arrivals[schema.event_id] == eid]
            sol = locate_event(df_evt, stations, schema, vp=float(vp))
            if sol is None:
                continue
            if not sol["success"]:
                continue
            n_loc += 1
            rms_list.append(sol["rms_s"])
        if len(rms_list) == 0:
            med_rms = np.nan
        else:
            med_rms = float(np.nanmedian(rms_list))
        rows.append({"vp_mps": float(vp), "median_rms_s": med_rms, "n_events": int(n_loc)})
    return pd.DataFrame(rows)


def choose_dbscan_eps(Xs: np.ndarray, k: int = 5, q: float = 0.9) -> Tuple[float, np.ndarray]:
    """Estimate eps from k-NN distances in standardized space."""
    nbrs = NearestNeighbors(n_neighbors=min(k, len(Xs))).fit(Xs)
    dists, _ = nbrs.kneighbors(Xs)
    # distance to kth neighbor
    kdist = np.sort(dists[:, -1])
    eps = float(np.quantile(kdist, q))
    return eps, kdist


def pca_trend_azimuth(points_xyz: np.ndarray) -> float:
    """Return azimuth (degrees from +x axis towards +y) of first principal component horizontal projection."""
    X = points_xyz - points_xyz.mean(axis=0, keepdims=True)
    C = np.cov(X.T)
    w, v = np.linalg.eigh(C)
    pc1 = v[:, np.argmax(w)]
    hx, hy = pc1[0], pc1[1]
    az = (np.degrees(np.arctan2(hy, hx)) + 360.0) % 180.0  # 0-180 for bidirectional
    return float(az)


def fit_plane_strike_dip(points_xyz: np.ndarray) -> Tuple[float, float]:
    """Fit plane by SVD; return strike (deg, 0-360) and dip (deg, 0-90).

    Coordinates assumed x East, y North, z Up (or any right-handed with z vertical).
    Strike defined as azimuth of horizontal line in plane (right-hand rule not enforced).
    """
    X = points_xyz - points_xyz.mean(axis=0, keepdims=True)
    _, _, vh = np.linalg.svd(X, full_matrices=False)
    normal = vh[-1, :]
    # Ensure normal points upward (positive z) for consistency
    if normal[2] < 0:
        normal = -normal

    nx, ny, nz = normal
    # Dip: angle from horizontal of plane; equivalently 90 - angle between normal and vertical
    dip = np.degrees(np.arctan2(np.sqrt(nx**2 + ny**2), nz))

    # Strike: azimuth of horizontal vector perpendicular to normal's horizontal projection
    # normal horizontal azimuth:
    az_n = (np.degrees(np.arctan2(ny, nx)) + 360.0) % 360.0
    strike = (az_n + 90.0) % 360.0

    return float(strike), float(dip)


def main():
    sns.set_context("talk")
    sns.set_style("whitegrid")

    stations = pd.read_csv("data/stations.csv")
    arrivals = pd.read_csv("data/arrival_times.csv")

    schema = infer_schema(stations, arrivals)

    # Standardize station id to string for join stability
    stations[schema.station_id] = stations[schema.station_id].astype(str)
    arrivals[schema.station_id] = arrivals[schema.station_id].astype(str)

    arrivals = arrivals.copy()
    arrivals["_pick_seconds"] = parse_pick_times(arrivals, schema.pick_time)

    # Velocity scan
    vp_grid = np.arange(2500.0, 6500.1, 250.0)
    scan = velocity_scan(arrivals, stations, schema, vp_grid=vp_grid, max_events=25)
    scan.to_csv(OUT_DIR / "velocity_scan.csv", index=False)

    # Choose Vp as argmin median RMS
    scan_valid = scan.dropna().sort_values("median_rms_s")
    if scan_valid.shape[0] > 0:
        vp0 = float(scan_valid.iloc[0]["vp_mps"])
    else:
        vp0 = 5000.0

    # Plot scan
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(scan["vp_mps"], scan["median_rms_s"], marker="o")
    ax.set_xlabel("Assumed Vp (m/s)")
    ax.set_ylabel("Median event RMS (s)")
    ax.set_title(f"Velocity scan (subset); chosen Vp={vp0:.0f} m/s")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(IMG_DIR / "fig_velocity_scan.png", dpi=200)
    plt.close(fig)

    # Locate all events
    located_rows = []
    resid_rows = []

    for eid, df_evt in arrivals.groupby(schema.event_id):
        sol = locate_event(df_evt, stations, schema, vp=vp0)
        if sol is None:
            continue
        resid_df = sol.pop("residuals")
        located_rows.append(sol)
        resid_rows.append(resid_df)

    located = pd.DataFrame(located_rows)
    if len(resid_rows) > 0:
        residuals = pd.concat(resid_rows, ignore_index=True)
    else:
        residuals = pd.DataFrame(columns=[schema.event_id, schema.station_id, "residual_s"])

    located.to_csv(OUT_DIR / "located_events.csv", index=False)
    residuals.to_csv(OUT_DIR / "event_residuals.csv", index=False)

    # Add derived quantities
    if located.shape[0] == 0:
        raise RuntimeError("No events could be located. Check schema and data.")

    # Determine whether station z is elevation (positive up). Assume so; define depth below mean station elevation.
    z_ref = float(stations[schema.z].mean())
    located["depth_m"] = z_ref - located["z"]

    # Quality filters
    good = located[(located["success"] == True) & (located["n_picks"] >= 5)]
    # Keep also by misfit threshold based on distribution
    rms_thr = float(np.nanquantile(good["rms_s"], 0.9)) if good.shape[0] > 10 else float(good["rms_s"].max())
    good = good[good["rms_s"] <= rms_thr]

    # Clustering in (x,y,depth)
    X = good[["x", "y", "depth_m"]].to_numpy()
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)
    eps, kdist = choose_dbscan_eps(Xs, k=5, q=0.9)

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(kdist)
    ax.axhline(eps, color="r", linestyle="--", label=f"eps (q90)={eps:.2f}")
    ax.set_xlabel("Points sorted")
    ax.set_ylabel("5-NN distance (standardized)")
    ax.set_title("DBSCAN eps selection via k-distance")
    ax.legend()
    fig.tight_layout()
    fig.savefig(IMG_DIR / "fig_kdistance.png", dpi=200)
    plt.close(fig)

    # DBSCAN
    # min_samples: require small cluster support
    db = DBSCAN(eps=eps, min_samples=8)
    labels = db.fit_predict(Xs)
    good = good.copy()
    good["cluster"] = labels

    # Cluster summary + structural metrics
    summaries = []
    for cl, dfc in good.groupby("cluster"):
        pts = dfc[["x", "y", "z"]].to_numpy()
        if cl == -1:
            summaries.append({
                "cluster": int(cl),
                "n_events": int(dfc.shape[0]),
                "trend_az_deg": np.nan,
                "strike_deg": np.nan,
                "dip_deg": np.nan,
                "x_mean": float(dfc["x"].mean()),
                "y_mean": float(dfc["y"].mean()),
                "depth_mean_m": float(dfc["depth_m"].mean()),
            })
            continue

        trend = pca_trend_azimuth(pts)
        strike, dip = fit_plane_strike_dip(pts)
        summaries.append({
            "cluster": int(cl),
            "n_events": int(dfc.shape[0]),
            "trend_az_deg": float(trend),
            "strike_deg": float(strike),
            "dip_deg": float(dip),
            "x_mean": float(dfc["x"].mean()),
            "y_mean": float(dfc["y"].mean()),
            "depth_mean_m": float(dfc["depth_m"].mean()),
        })

    cluster_summary = pd.DataFrame(summaries).sort_values(["cluster"])
    cluster_summary.to_csv(OUT_DIR / "cluster_summary.csv", index=False)

    # --- Figures ---
    # Station & events map
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.scatter(stations[schema.x], stations[schema.y], s=60, c="k", marker="^", label="Stations")
    sc = ax.scatter(good["x"], good["y"], s=18, c=good["cluster"], cmap="tab20", alpha=0.9)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel(f"{schema.x} (m)")
    ax.set_ylabel(f"{schema.y} (m)")
    ax.set_title("Located microseismicity (plan view), colored by DBSCAN cluster")
    cb = fig.colorbar(sc, ax=ax, shrink=0.8)
    cb.set_label("cluster label")
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(IMG_DIR / "fig_planview_clusters.png", dpi=200)
    plt.close(fig)

    # Cross-section: depth vs x and depth vs y
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    axes[0].scatter(good["x"], good["depth_m"], c=good["cluster"], cmap="tab20", s=14)
    axes[0].set_xlabel(f"{schema.x} (m)")
    axes[0].set_ylabel("Depth below mean station elevation (m)")
    axes[0].set_title("X-section")
    axes[0].invert_yaxis()

    axes[1].scatter(good["y"], good["depth_m"], c=good["cluster"], cmap="tab20", s=14)
    axes[1].set_xlabel(f"{schema.y} (m)")
    axes[1].set_title("Y-section")
    axes[1].invert_yaxis()

    fig.suptitle("Depth sections (colored by cluster)")
    fig.tight_layout()
    fig.savefig(IMG_DIR / "fig_depth_sections.png", dpi=200)
    plt.close(fig)

    # Time evolution (if interpretable)
    t0 = good["t0_seconds"].to_numpy(dtype=float)
    fig, ax = plt.subplots(figsize=(10, 4))
    if np.nanmedian(t0) > 1e8:
        # likely UNIX seconds
        tt = pd.to_datetime(t0, unit='s', utc=True)
        ax.scatter(tt, good["depth_m"], c=good["cluster"], cmap='tab20', s=10, alpha=0.8)
        ax.set_xlabel('Origin time (UTC)')
    else:
        # relative seconds
        tt = t0 - np.nanmin(t0)
        ax.scatter(tt, good["depth_m"], c=good["cluster"], cmap='tab20', s=10, alpha=0.8)
        ax.set_xlabel('Origin time (s since first event)')
    ax.set_ylabel('Depth (m)')
    ax.invert_yaxis()
    ax.set_title('Temporal evolution: depth vs origin time (colored by cluster)')
    fig.tight_layout()
    fig.savefig(IMG_DIR / 'fig_time_depth.png', dpi=200)
    plt.close(fig)

    # Residual diagnostics
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    sns.histplot(good["rms_s"], bins=25, ax=axes[0], color="#4C72B0")
    axes[0].set_xlabel("Event RMS (s)")
    axes[0].set_title("Location misfit distribution")

    axes[1].scatter(good["n_picks"], good["rms_s"], s=18, alpha=0.7)
    axes[1].set_xlabel("Number of P picks")
    axes[1].set_ylabel("Event RMS (s)")
    axes[1].set_title("Misfit vs pick count")

    fig.tight_layout()
    fig.savefig(IMG_DIR / "fig_misfit_qc.png", dpi=200)
    plt.close(fig)

    # Rose diagram of trends for non-noise clusters
    az = cluster_summary.loc[cluster_summary["cluster"] != -1, "trend_az_deg"].dropna().to_numpy()
    weights = cluster_summary.loc[cluster_summary["cluster"] != -1, "n_events"].to_numpy()
    if len(az) > 0:
        # Expand by weights for simple rose
        az_exp = np.concatenate([np.repeat(a, int(w)) for a, w in zip(az, weights)])
        theta = np.deg2rad(az_exp)
        bins = np.deg2rad(np.linspace(0, 180, 19))
        hist, edges = np.histogram(theta, bins=bins)
        centers = 0.5 * (edges[:-1] + edges[1:])

        fig = plt.figure(figsize=(6, 6))
        ax = fig.add_subplot(111, polar=True)
        ax.bar(centers, hist, width=(edges[1] - edges[0]) * 0.9, bottom=0.0, color="#55A868", alpha=0.85)
        ax.set_theta_zero_location("E")
        ax.set_theta_direction(-1)
        ax.set_thetamin(0)
        ax.set_thetamax(180)
        ax.set_title("Cluster trend azimuths (PCA PC1; 0–180°)")
        fig.tight_layout()
        fig.savefig(IMG_DIR / "fig_rose_trends.png", dpi=200)
        plt.close(fig)

    # Along-strike projection for dominant cluster (largest non-noise)
    non_noise = cluster_summary[cluster_summary["cluster"] != -1].copy()
    if non_noise.shape[0] > 0:
        dominant = int(non_noise.sort_values("n_events", ascending=False).iloc[0]["cluster"])
        df_dom = good[good["cluster"] == dominant].copy()
        # use trend azimuth for projection
        trend = float(non_noise.set_index("cluster").loc[dominant, "trend_az_deg"])
        # unit vectors in horizontal plane
        ang = np.deg2rad(trend)
        u = np.array([np.cos(ang), np.sin(ang)])
        v = np.array([-np.sin(ang), np.cos(ang)])
        XY = df_dom[["x", "y"]].to_numpy()
        XY0 = XY - XY.mean(axis=0, keepdims=True)
        s_along = XY0 @ u
        s_across = XY0 @ v

        fig, ax = plt.subplots(figsize=(7, 5))
        sc = ax.scatter(s_along, df_dom["depth_m"], c=s_across, cmap="coolwarm", s=18)
        ax.invert_yaxis()
        ax.set_xlabel("Along-trend distance (m)")
        ax.set_ylabel("Depth (m)")
        ax.set_title(f"Dominant cluster cross-section (cluster {dominant}); color=across-trend")
        cb = fig.colorbar(sc, ax=ax, shrink=0.8)
        cb.set_label("Across-trend (m)")
        fig.tight_layout()
        fig.savefig(IMG_DIR / "fig_dominant_cluster_section.png", dpi=200)
        plt.close(fig)

    # Save metadata JSON for report
    meta = {
        "schema": schema.__dict__,
        "vp_chosen_mps": vp0,
        "n_events_total": int(arrivals[schema.event_id].nunique()),
        "n_events_located": int(located.shape[0]),
        "n_events_good": int(good.shape[0]),
        "rms_threshold_s": rms_thr,
        "z_ref_mean_station": z_ref,
        "dbscan_eps_std": float(eps),
        "dbscan_min_samples": 8,
    }
    (OUT_DIR / "run_metadata.json").write_text(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
