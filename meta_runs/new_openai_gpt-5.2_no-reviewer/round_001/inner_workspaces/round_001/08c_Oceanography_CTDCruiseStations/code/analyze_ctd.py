"""CTD Cruise Stations: vertical profile + thermohaline analysis.

Reads data/cruise_ctd.csv, performs light QC, computes TEOS-10 derived
properties (SA, CT, sigma0, depth), extracts profile metrics (MLD, max N2),
creates figures, and saves processed tables to outputs/.

Run:
  python code/analyze_ctd.py
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns


def _first_match(cols: List[str], patterns: List[str]) -> Optional[str]:
    """Return first column name matching any regex pattern (case-insensitive)."""
    for pat in patterns:
        r = re.compile(pat, flags=re.IGNORECASE)
        for c in cols:
            if r.search(c):
                return c
    return None


@dataclass
class ColMap:
    station: Optional[str]
    cast: Optional[str]
    profile: Optional[str]
    time: Optional[str]
    date: Optional[str]
    latitude: Optional[str]
    longitude: Optional[str]
    pressure: Optional[str]
    depth: Optional[str]
    temperature: Optional[str]
    salinity: Optional[str]


def infer_columns(df: pd.DataFrame) -> ColMap:
    cols = list(df.columns)
    station = _first_match(cols, [r"^station$", r"station[_ ]?id", r"\bstn\b", r"\bevent\b"])
    cast = _first_match(cols, [r"^cast$", r"cast[_ ]?no", r"\bcastid\b", r"\bbottle\b"])
    profile = _first_match(cols, [r"profile[_ ]?id", r"^profile$"])

    # time columns
    time = _first_match(cols, [r"datetime", r"timestamp", r"time(_utc)?$", r"\btime\b"])
    date = _first_match(cols, [r"\bdate\b"])

    latitude = _first_match(cols, [r"^lat$", r"latitude"])
    longitude = _first_match(cols, [r"^lon$", r"longitude", r"long"])

    pressure = _first_match(cols, [r"press", r"\bp\b.*dbar", r"dbar"])
    depth = _first_match(cols, [r"depth", r"\bz\b.*m", r"meters"])

    temperature = _first_match(cols, [r"temp", r"temperature", r"\bt\b.*c"])
    salinity = _first_match(cols, [r"sal", r"salinity", r"\bsp\b"])

    return ColMap(
        station=station,
        cast=cast,
        profile=profile,
        time=time,
        date=date,
        latitude=latitude,
        longitude=longitude,
        pressure=pressure,
        depth=depth,
        temperature=temperature,
        salinity=salinity,
    )


def parse_time(df: pd.DataFrame, cmap: ColMap) -> pd.Series:
    """Parse datetime from available fields; returns pandas datetime64[ns]."""
    if cmap.time and cmap.date and cmap.time != cmap.date:
        # attempt combine if separate
        dt = pd.to_datetime(
            df[cmap.date].astype(str).str.strip() + " " + df[cmap.time].astype(str).str.strip(),
            errors="coerce",
            utc=True,
        )
        if dt.notna().any():
            return dt

    if cmap.time:
        dt = pd.to_datetime(df[cmap.time], errors="coerce", utc=True)
        if dt.notna().any():
            return dt

    if cmap.date:
        dt = pd.to_datetime(df[cmap.date], errors="coerce", utc=True)
        if dt.notna().any():
            return dt

    return pd.to_datetime(pd.Series([pd.NaT] * len(df)), utc=True)


def build_profile_id(df: pd.DataFrame, cmap: ColMap) -> pd.Series:
    if cmap.profile:
        pid = df[cmap.profile].astype(str)
        return pid

    parts = []
    if cmap.station:
        parts.append(df[cmap.station].astype(str))
    if cmap.cast:
        parts.append(df[cmap.cast].astype(str))

    if parts:
        pid = parts[0]
        for p in parts[1:]:
            pid = pid + "_" + p
        return pid

    # fallback: use lat/lon rounded + time
    lat = df[cmap.latitude] if cmap.latitude else pd.Series(np.nan, index=df.index)
    lon = df[cmap.longitude] if cmap.longitude else pd.Series(np.nan, index=df.index)
    return (
        lat.round(3).astype(str)
        + "_"
        + lon.round(3).astype(str)
        + "_"
        + parse_time(df, cmap).astype(str)
    )


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)
    lat2 = np.radians(lat2)
    lon2 = np.radians(lon2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return R * c


def compute_alongtrack_distance(sta: pd.DataFrame, lat_col: str, lon_col: str) -> np.ndarray:
    """Compute cumulative km distance along ordered stations."""
    lat = sta[lat_col].to_numpy()
    lon = sta[lon_col].to_numpy()
    d = np.zeros(len(sta))
    if len(sta) <= 1:
        return d
    seg = haversine_km(lat[:-1], lon[:-1], lat[1:], lon[1:])
    d[1:] = np.cumsum(seg)
    return d


def robust_num(s: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(s):
        return s
    return pd.to_numeric(s, errors="coerce")


def main():
    in_path = "data/cruise_ctd.csv"
    out_dir = "outputs"
    fig_dir = "report/images"
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(fig_dir, exist_ok=True)

    df = pd.read_csv(in_path)
    cmap = infer_columns(df)

    # Coerce key numeric columns
    for c in [cmap.latitude, cmap.longitude, cmap.pressure, cmap.depth, cmap.temperature, cmap.salinity]:
        if c and c in df.columns:
            df[c] = robust_num(df[c])

    df["datetime"] = parse_time(df, cmap)
    df["profile_id"] = build_profile_id(df, cmap)

    # Choose vertical axis
    zcol = None
    if cmap.pressure and df[cmap.pressure].notna().any():
        zcol = cmap.pressure
        df["p_dbar"] = df[zcol]
    elif cmap.depth and df[cmap.depth].notna().any():
        zcol = cmap.depth
        df["depth_m"] = df[zcol]
    else:
        raise RuntimeError("No pressure or depth column found; cannot proceed.")

    # standardize lat/lon at profile level
    if cmap.latitude and cmap.longitude:
        prof_geo = (
            df.groupby("profile_id")[[cmap.latitude, cmap.longitude]]
            .median(numeric_only=True)
            .rename(columns={cmap.latitude: "lat", cmap.longitude: "lon"})
        )
    else:
        prof_geo = pd.DataFrame(index=df["profile_id"].unique(), data={"lat": np.nan, "lon": np.nan})

    df = df.join(prof_geo, on="profile_id")

    # standardize station/cast columns if present
    if cmap.station:
        df["station"] = df[cmap.station].astype(str)
    else:
        df["station"] = df["profile_id"].astype(str)

    if cmap.cast:
        df["cast"] = df[cmap.cast].astype(str)
    else:
        df["cast"] = ""

    # Temperature + salinity
    if not cmap.temperature or not cmap.salinity:
        raise RuntimeError("Temperature and/or salinity column not found; cannot analyze thermohaline structure.")

    df["temp_C"] = df[cmap.temperature]
    df["SP"] = df[cmap.salinity]

    # Drop rows lacking key obs
    df0 = df.copy()
    df = df.dropna(subset=["temp_C", "SP"] + (["p_dbar"] if "p_dbar" in df.columns else ["depth_m"]))

    # If we only have depth, approximate pressure (1 dbar ~ 1 m). Prefer TEOS-10 if possible.
    if "p_dbar" not in df.columns:
        df["p_dbar"] = df["depth_m"].clip(lower=0)

    # TEOS-10 computations
    try:
        import gsw  # type: ignore

        # Need lon/lat for SA_from_SP; if missing, fall back with zeros and warn.
        lon = df["lon"].to_numpy()
        lat = df["lat"].to_numpy()
        lon0 = np.where(np.isfinite(lon), lon, 0.0)
        lat0 = np.where(np.isfinite(lat), lat, 0.0)

        p = df["p_dbar"].to_numpy()
        SP = df["SP"].to_numpy()
        t = df["temp_C"].to_numpy()

        SA = gsw.SA_from_SP(SP, p, lon0, lat0)
        CT = gsw.CT_from_t(SA, t, p)
        sigma0 = gsw.sigma0(SA, CT)
        z = gsw.z_from_p(p, lat0)  # negative meters
        depth = -z

        df["SA_gkg"] = SA
        df["CT_C"] = CT
        df["sigma0"] = sigma0
        df["depth_m"] = depth

        # N^2 per profile (returns midpoints)
        n2_list = []
        for pid, g in df.sort_values(["profile_id", "p_dbar"]).groupby("profile_id"):
            gg = g.dropna(subset=["SA_gkg", "CT_C", "p_dbar", "lat"]).copy()
            if len(gg) < 4:
                continue
            try:
                N2, p_mid = gsw.Nsquared(gg["SA_gkg"].to_numpy(), gg["CT_C"].to_numpy(), gg["p_dbar"].to_numpy(), gg["lat"].median())
                tmp = pd.DataFrame({"profile_id": pid, "p_mid": p_mid, "N2": N2})
                # depth at midpoints using z_from_p
                zmid = gsw.z_from_p(p_mid, gg["lat"].median())
                tmp["depth_mid_m"] = -zmid
                n2_list.append(tmp)
            except Exception:
                continue
        if n2_list:
            n2df = pd.concat(n2_list, ignore_index=True)
        else:
            n2df = pd.DataFrame(columns=["profile_id", "p_mid", "N2", "depth_mid_m"])

    except Exception as e:
        print("WARNING: TEOS-10 (gsw) computations failed; proceeding with approximate density.", e)
        # Fallback: use UNESCO-like linearized density proxy
        df["SA_gkg"] = np.nan
        df["CT_C"] = np.nan
        # crude sigma0 proxy: sigma0 ~ a*SP - b*T
        df["sigma0"] = 0.8 * df["SP"] - 0.2 * df["temp_C"]
        if "depth_m" not in df.columns:
            df["depth_m"] = df["p_dbar"]
        n2df = pd.DataFrame(columns=["profile_id", "p_mid", "N2", "depth_mid_m"])

    # Profile-level metrics: max depth, surface values, MLD
    prof = (
        df.groupby("profile_id")
        .agg(
            station=("station", "first"),
            cast=("cast", "first"),
            datetime=("datetime", "min"),
            lat=("lat", "median"),
            lon=("lon", "median"),
            max_depth_m=("depth_m", "max"),
            n_obs=("depth_m", "size"),
        )
        .reset_index()
    )

    # Surface reference (shallowest 10 m)
    def _surf_ref(g: pd.DataFrame) -> pd.Series:
        gg = g.sort_values("depth_m")
        shallow = gg[gg["depth_m"] <= 10]
        if shallow.empty:
            shallow = gg.head(5)
        return pd.Series(
            {
                "T_surf": float(np.nanmedian(shallow["temp_C"])),
                "S_surf": float(np.nanmedian(shallow["SP"])),
                "sigma0_surf": float(np.nanmedian(shallow["sigma0"])),
            }
        )

    # groupby.apply signature differs across pandas versions; avoid include_groups
    surf = df.groupby("profile_id").apply(_surf_ref)
    prof = prof.merge(surf.reset_index(), on="profile_id", how="left")

    # MLD criterion: density increase of 0.03 kg/m^3 from surface (or proxy)
    def _mld(g: pd.DataFrame) -> float:
        gg = g.sort_values("depth_m")
        ref = gg[gg["depth_m"] <= 10]
        if ref.empty:
            ref = gg.head(5)
        sigma_ref = np.nanmedian(ref["sigma0"])
        if not np.isfinite(sigma_ref):
            return np.nan
        thr = sigma_ref + 0.03
        below = gg[gg["sigma0"] >= thr]
        if below.empty:
            return float(np.nanmax(gg["depth_m"]))
        return float(np.nanmin(below["depth_m"]))

    prof["MLD_m"] = df.groupby("profile_id").apply(_mld).to_numpy()

    # Add max N2
    if not n2df.empty:
        n2max = n2df.groupby("profile_id").agg(max_N2=("N2", "max"), depth_max_N2=("depth_mid_m", lambda x: float(x.iloc[np.nanargmax(x.to_numpy())]) if len(x) else np.nan)).reset_index()
        prof = prof.merge(n2max, on="profile_id", how="left")
    else:
        prof["max_N2"] = np.nan
        prof["depth_max_N2"] = np.nan

    # Order profiles along time if available, else by lat then lon
    if prof["datetime"].notna().any():
        prof = prof.sort_values("datetime")
    elif prof["lat"].notna().any():
        prof = prof.sort_values(["lat", "lon"])
    else:
        prof = prof.sort_values("profile_id")

    if prof[["lat", "lon"]].notna().all(axis=1).sum() >= 2:
        prof["dist_km"] = compute_alongtrack_distance(prof.dropna(subset=["lat", "lon"]), "lat", "lon")
        # merge back by index alignment
        # Because compute_alongtrack_distance is called on dropna subset, align via that subset's index
        sub = prof.dropna(subset=["lat", "lon"]).copy()
        sub["dist_km"] = compute_alongtrack_distance(sub, "lat", "lon")
        prof = prof.drop(columns=["dist_km"], errors="ignore").merge(sub[["profile_id", "dist_km"]], on="profile_id", how="left")
    else:
        prof["dist_km"] = np.arange(len(prof), dtype=float)

    df = df.merge(prof[["profile_id", "dist_km"]], on="profile_id", how="left")

    # Save processed data
    df.to_csv(os.path.join(out_dir, "ctd_processed_long.csv"), index=False)
    prof.to_csv(os.path.join(out_dir, "ctd_profiles_summary.csv"), index=False)
    n2df.to_csv(os.path.join(out_dir, "ctd_N2.csv"), index=False)

    # ----------------
    # FIGURES
    # ----------------
    sns.set_context("talk")
    sns.set_style("whitegrid")

    def placeholder(path: str, title: str, message: str):
        fig, ax = plt.subplots(figsize=(7.5, 4.8), constrained_layout=True)
        ax.axis('off')
        ax.set_title(title)
        ax.text(0.02, 0.6, message, transform=ax.transAxes, fontsize=12)
        fig.savefig(path, dpi=200)
        plt.close(fig)

    # 1) Station map / track
    fig01_path = os.path.join(fig_dir, "fig01_station_map.png")
    if prof[["lat", "lon"]].notna().all(axis=1).sum() >= 2:
        fig, ax = plt.subplots(figsize=(7.5, 6.5), constrained_layout=True)
        sc = ax.scatter(prof["lon"], prof["lat"], c=prof["dist_km"], cmap="viridis", s=35)
        ax.plot(prof["lon"], prof["lat"], color="0.5", lw=1)
        ax.set_xlabel("Longitude (deg)")
        ax.set_ylabel("Latitude (deg)")
        ax.set_title("CTD station positions (colored by along-track distance)")
        cb = fig.colorbar(sc, ax=ax)
        cb.set_label("Distance along track (km)")
        fig.savefig(fig01_path, dpi=200)
        plt.close(fig)
    else:
        placeholder(fig01_path, "CTD station positions", "Latitude/longitude not available in the input file; station map not plotted.")

    # 2) Sampling depth distribution
    fig, ax = plt.subplots(figsize=(7.5, 4.8), constrained_layout=True)
    ax.hist(prof["max_depth_m"].dropna(), bins=25, color="#4C72B0", alpha=0.9)
    ax.set_xlabel("Maximum depth per profile (m)")
    ax.set_ylabel("Count")
    ax.set_title("CTD profile maximum depths")
    fig.savefig(os.path.join(fig_dir, "fig02_max_depth_hist.png"), dpi=200)
    plt.close(fig)

    # 3) Example vertical profiles (T, S, sigma0)
    # choose 3 profiles: start/mid/end by distance
    prof_sel = prof.dropna(subset=["dist_km"]).copy()
    if len(prof_sel) >= 3:
        q = prof_sel["dist_km"].quantile([0.1, 0.5, 0.9]).to_numpy()
        sel_ids = []
        for qq in q:
            sel_ids.append(prof_sel.iloc[(prof_sel["dist_km"] - qq).abs().argsort()[:1]]["profile_id"].values[0])
        sel_ids = list(dict.fromkeys(sel_ids))
    else:
        sel_ids = prof["profile_id"].head(3).tolist()

    if sel_ids:
        fig, axes = plt.subplots(1, 3, figsize=(13.5, 5.5), sharey=True, constrained_layout=True)
        colors = sns.color_palette("deep", n_colors=len(sel_ids))
        for pid, col in zip(sel_ids, colors):
            g = df[df["profile_id"] == pid].sort_values("depth_m")
            axes[0].plot(g["temp_C"], g["depth_m"], color=col, lw=2, label=str(pid))
            axes[1].plot(g["SP"], g["depth_m"], color=col, lw=2)
            axes[2].plot(g["sigma0"], g["depth_m"], color=col, lw=2)
        for ax, xl in zip(axes, ["Temperature (°C)", "Practical salinity (PSU)", "σ₀ (kg m⁻³)" ]):
            ax.set_xlabel(xl)
            ax.invert_yaxis()
            ax.grid(True, alpha=0.3)
        axes[0].set_ylabel("Depth (m)")
        axes[0].legend(fontsize=9, loc="best")
        fig.suptitle("Representative vertical profiles")
        fig.savefig(os.path.join(fig_dir, "fig03_profiles_T_S_sigma0.png"), dpi=200)
        plt.close(fig)

    # 4) T-S diagram with depth coloring
    # subsample for speed
    dsub = df.dropna(subset=["SP", "temp_C", "sigma0", "depth_m"]).copy()
    if len(dsub) > 8000:
        dsub = dsub.sample(8000, random_state=0)

    fig, ax = plt.subplots(figsize=(7.5, 6.5), constrained_layout=True)
    sc = ax.scatter(dsub["SP"], dsub["temp_C"], c=dsub["depth_m"], s=8, cmap="mako", alpha=0.7)
    ax.set_xlabel("Practical salinity (PSU)")
    ax.set_ylabel("Temperature (°C)")
    ax.set_title("Thermohaline structure: T–S diagram (colored by depth)")
    cb = fig.colorbar(sc, ax=ax)
    cb.set_label("Depth (m)")

    # density contours if sigma0 is TEOS-10 (values ~ 20-30)
    try:
        smin, smax = np.nanpercentile(dsub["SP"], [1, 99])
        tmin, tmax = np.nanpercentile(dsub["temp_C"], [1, 99])
        Sg = np.linspace(smin, smax, 60)
        Tg = np.linspace(tmin, tmax, 60)
        SS, TT = np.meshgrid(Sg, Tg)
        # approximate sigma0 on grid using TEOS-10 if available
        import gsw  # type: ignore

        SA_grid = gsw.SA_from_SP(SS, 0, np.nanmedian(prof["lon"]) if prof["lon"].notna().any() else 0.0, np.nanmedian(prof["lat"]) if prof["lat"].notna().any() else 0.0)
        CT_grid = gsw.CT_from_t(SA_grid, TT, 0)
        sig_grid = gsw.sigma0(SA_grid, CT_grid)
        cs = ax.contour(SS, TT, sig_grid, colors="k", linewidths=0.6, alpha=0.5)
        ax.clabel(cs, inline=True, fontsize=8, fmt="%.1f")
    except Exception:
        pass

    fig.savefig(os.path.join(fig_dir, "fig04_TS_diagram.png"), dpi=200)
    plt.close(fig)

    # 5) Along-track sections (Temp, Salinity)
    # grid to regular depth bins
    # limit to 0- max common depth (e.g., 95th percentile of profile max depth)
    zmax = float(np.nanpercentile(prof["max_depth_m"], 90)) if prof["max_depth_m"].notna().any() else float(np.nanmax(df["depth_m"]))
    zmax = max(50.0, min(zmax, float(np.nanmax(df["depth_m"])) ))
    dz = 5.0
    zbins = np.arange(0, zmax + dz, dz)

    # create station x depth matrices using bin-averaging
    prof_order = prof.sort_values("dist_km")
    pids = prof_order["profile_id"].tolist()
    x = prof_order["dist_km"].to_numpy()

    def section_matrix(var: str) -> np.ndarray:
        M = np.full((len(zbins), len(pids)), np.nan)
        for j, pid in enumerate(pids):
            g = df[df["profile_id"] == pid].sort_values("depth_m")
            zz = g["depth_m"].to_numpy()
            vv = g[var].to_numpy()
            # bin average
            ind = np.digitize(zz, zbins) - 1
            for k in range(len(zbins)):
                mask = ind == k
                if np.any(mask):
                    M[k, j] = np.nanmean(vv[mask])
        return M

    for var, label, fname, cmap0 in [
        ("temp_C", "Temperature (°C)", "fig05_section_temperature.png", "turbo"),
        ("SP", "Salinity (PSU)", "fig06_section_salinity.png", "viridis"),
        ("sigma0", "σ₀ (kg m⁻³)", "fig07_section_sigma0.png", "cividis"),
    ]:
        M = section_matrix(var)
        fig, ax = plt.subplots(figsize=(12.5, 5.2), constrained_layout=True)
        # pcolormesh expects edges; create edges from centers
        xedges = np.r_[x[0], (x[:-1] + x[1:]) / 2, x[-1]]
        zedges = np.r_[zbins[0], (zbins[:-1] + zbins[1:]) / 2, zbins[-1]]
        # ensure monotonic edges
        xedges = np.unique(xedges)
        # If unique shrank, fall back to imshow
        if len(xedges) < 3:
            im = ax.imshow(M, aspect="auto", origin="upper", extent=[np.nanmin(x), np.nanmax(x), np.nanmax(zbins), np.nanmin(zbins)], cmap=cmap0)
        else:
            X, Z = np.meshgrid(x, zbins)
            im = ax.pcolormesh(x, zbins, M, shading="auto", cmap=cmap0)
        ax.invert_yaxis()
        ax.set_xlabel("Distance along track (km)")
        ax.set_ylabel("Depth (m)")
        ax.set_title(f"Along-track section: {label}")
        cb = fig.colorbar(im, ax=ax)
        cb.set_label(label)
        fig.savefig(os.path.join(fig_dir, fname), dpi=200)
        plt.close(fig)

    # 6) MLD and stratification summary along track
    fig, ax = plt.subplots(figsize=(10.5, 4.8), constrained_layout=True)
    ax.plot(prof["dist_km"], prof["MLD_m"], marker="o", ms=4, lw=1.5, color="#DD8452")
    ax.set_xlabel("Distance along track (km)")
    ax.set_ylabel("Mixed-layer depth (m)")
    ax.set_title("Mixed-layer depth (density criterion Δσ₀=0.03 kg m⁻³)")
    ax.invert_yaxis()
    fig.savefig(os.path.join(fig_dir, "fig08_MLD_alongtrack.png"), dpi=200)
    plt.close(fig)

    fig09_path = os.path.join(fig_dir, "fig09_maxN2_alongtrack.png")
    if prof["max_N2"].notna().any():
        fig, ax = plt.subplots(figsize=(10.5, 4.8), constrained_layout=True)
        ax.plot(prof["dist_km"], prof["max_N2"], marker="o", ms=4, lw=1.5, color="#55A868")
        ax.set_xlabel("Distance along track (km)")
        ax.set_ylabel("max N² (s⁻²)")
        ax.set_title("Maximum Brunt–Väisälä frequency squared (stratification intensity)")
        ax.set_yscale("log")
        ax.grid(True, which="both", alpha=0.3)
        fig.savefig(fig09_path, dpi=200)
        plt.close(fig)
    else:
        placeholder(fig09_path, "Maximum N² along track", "N² could not be computed (e.g., TEOS-10 unavailable or insufficient data).")

    # 7) Surface properties and MLD relationships
    fig10_path = os.path.join(fig_dir, 'fig10_surface_TS_MLD.png')
    fig11_path = os.path.join(fig_dir, 'fig11_MLD_vs_surfaceT.png')
    if prof[['T_surf','S_surf','MLD_m']].notna().all(axis=1).any():
        fig, ax = plt.subplots(figsize=(7.5, 6.5), constrained_layout=True)
        sc = ax.scatter(prof['S_surf'], prof['T_surf'], c=prof['MLD_m'], s=45, cmap='viridis', edgecolor='none')
        ax.set_xlabel('Surface salinity (PSU)')
        ax.set_ylabel('Surface temperature (°C)')
        ax.set_title('Surface T–S colored by mixed-layer depth')
        cb = fig.colorbar(sc, ax=ax)
        cb.set_label('MLD (m)')
        fig.savefig(fig10_path, dpi=200)
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(10.5, 4.8), constrained_layout=True)
        ax.scatter(prof['T_surf'], prof['MLD_m'], c=prof['S_surf'], cmap='plasma', s=35)
        ax.set_xlabel('Surface temperature (°C)')
        ax.set_ylabel('MLD (m)')
        ax.invert_yaxis()
        ax.set_title('Mixed-layer depth vs surface temperature (colored by surface salinity)')
        cb = plt.colorbar(ax.collections[0], ax=ax)
        cb.set_label('Surface salinity (PSU)')
        fig.savefig(fig11_path, dpi=200)
        plt.close(fig)
    else:
        placeholder(fig10_path, 'Surface T–S colored by MLD', 'Insufficient surface T/S/MLD values to plot this relationship.')
        placeholder(fig11_path, 'MLD vs surface temperature', 'Insufficient surface T/S/MLD values to plot this relationship.')

    # 8) Data completeness heatmap by variable
    vars_show = ["temp_C", "SP", "sigma0", "depth_m", "lat", "lon", "datetime"]
    miss = pd.DataFrame({v: df[v].isna().mean() if v in df.columns else np.nan for v in vars_show}, index=[0]).T
    miss.columns = ["missing_fraction"]
    miss = miss.sort_values("missing_fraction", ascending=False)

    fig, ax = plt.subplots(figsize=(7.5, 4.8), constrained_layout=True)
    ax.barh(miss.index, miss["missing_fraction"], color="#4C72B0")
    ax.set_xlabel("Fraction missing")
    ax.set_title("Data completeness (raw columns after standardization)")
    ax.set_xlim(0, 1)
    fig.savefig(os.path.join(fig_dir, "fig12_missingness.png"), dpi=200)
    plt.close(fig)

    # 9) Validation: pressure–depth consistency when both were provided
    fig13_path = os.path.join(fig_dir, 'fig13_pressure_vs_depth.png')
    made13 = False
    if cmap.pressure and cmap.depth and cmap.pressure in df0.columns and cmap.depth in df0.columns:
        dval = df0[[cmap.pressure, cmap.depth]].dropna().copy()
        if len(dval) > 10:
            fig, ax = plt.subplots(figsize=(6.5, 6.0), constrained_layout=True)
            if len(dval) > 5000:
                dval = dval.sample(5000, random_state=0)
            ax.scatter(dval[cmap.pressure], dval[cmap.depth], s=8, alpha=0.25)
            ax.set_xlabel(f"Pressure ({cmap.pressure})")
            ax.set_ylabel(f"Depth ({cmap.depth})")
            ax.set_title("Validation: reported depth vs pressure")
            fig.savefig(fig13_path, dpi=200)
            plt.close(fig)
            made13 = True
    if not made13:
        placeholder(fig13_path, "Validation: depth vs pressure", "Input file does not contain both pressure and depth fields (or too few paired values).")

    # Write a small text summary for report
    summary = {
        "n_rows_raw": int(len(df0)),
        "n_rows_used": int(len(df)),
        "n_profiles": int(prof["profile_id"].nunique()),
        "depth_max_m": float(np.nanmax(df["depth_m"])) if df["depth_m"].notna().any() else np.nan,
        "depth_p90_profile_max_m": float(np.nanpercentile(prof["max_depth_m"], 90)) if prof["max_depth_m"].notna().any() else np.nan,
        "temp_range_C": [float(np.nanmin(df["temp_C"])), float(np.nanmax(df["temp_C"]))],
        "sal_range_PSU": [float(np.nanmin(df["SP"])), float(np.nanmax(df["SP"]))],
        "sigma0_range": [float(np.nanmin(df["sigma0"])), float(np.nanmax(df["sigma0"]))],
        "mld_median_m": float(np.nanmedian(prof["MLD_m"])) if prof["MLD_m"].notna().any() else np.nan,
    }
    pd.Series(summary).to_json(os.path.join(out_dir, "ctd_summary.json"), indent=2)

    # Save column inference for transparency
    pd.Series(cmap.__dict__).to_json(os.path.join(out_dir, "inferred_columns.json"), indent=2)


if __name__ == "__main__":
    main()
