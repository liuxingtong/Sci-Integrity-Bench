# -*- coding: utf-8 -*-
"""CTD Cruise Stations: vertical profile + thermohaline structure analysis.

Reads data/cruise_ctd.csv and produces:
- cleaned dataset (outputs/ctd_clean.parquet)
- per-profile summary table (outputs/ctd_profile_summary.csv)
- figures in report/images/*.png

Run:
  python code/ctd_analysis.py

This script is intentionally defensive to handle varying column names.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import seaborn as sns

try:
    import gsw  # TEOS-10
except Exception as e:  # pragma: no cover
    raise SystemExit(
        "Package 'gsw' is required. Install with: pip install gsw\n" + str(e)
    )


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "cruise_ctd.csv"
OUT_DIR = ROOT / "outputs"
IMG_DIR = ROOT / "report" / "images"

OUT_DIR.mkdir(parents=True, exist_ok=True)
IMG_DIR.mkdir(parents=True, exist_ok=True)


def _pick_col(df: pd.DataFrame, patterns: list[str], required: bool = True) -> str | None:
    """Pick first column whose name matches any regex in patterns."""
    for pat in patterns:
        for c in df.columns:
            if re.search(pat, c, flags=re.IGNORECASE):
                return c
    if required:
        raise KeyError(f"Could not find column matching patterns: {patterns}")
    return None


def haversine_km(lon1, lat1, lon2, lat2):
    """Great-circle distance in km."""
    lon1, lat1, lon2, lat2 = map(np.deg2rad, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    r = 6371.0
    return r * c


@dataclass
class Cols:
    station: str | None
    cast: str | None
    time: str | None
    lat: str
    lon: str
    depth: str | None
    pressure: str | None
    temp: str
    sal: str


def infer_columns(df: pd.DataFrame) -> Cols:
    station = _pick_col(df, [r"^station$", r"station"], required=False)
    cast = _pick_col(df, [r"^cast$", r"cast"], required=False)
    time = _pick_col(df, [r"time", r"date"], required=False)
    lat = _pick_col(df, [r"^lat", r"latitude"], required=True)
    lon = _pick_col(df, [r"^lon", r"longitude"], required=True)

    depth = _pick_col(df, [r"depth"], required=False)
    pressure = _pick_col(df, [r"pres", r"pressure"], required=False)

    temp = _pick_col(df, [r"temp", r"temperature"], required=True)
    sal = _pick_col(df, [r"sal"], required=True)

    return Cols(
        station=station,
        cast=cast,
        time=time,
        lat=lat,
        lon=lon,
        depth=depth,
        pressure=pressure,
        temp=temp,
        sal=sal,
    )


def parse_time(s: pd.Series) -> pd.Series:
    # try ISO, then common oceanographic formats
    out = pd.to_datetime(s, errors="coerce", utc=True)
    if out.notna().mean() < 0.2:
        out = pd.to_datetime(s, errors="coerce")
    return out


def qc_range(x: pd.Series, lo: float, hi: float) -> pd.Series:
    return x.where((x >= lo) & (x <= hi))


def compute_derived(df: pd.DataFrame, cols: Cols) -> pd.DataFrame:
    d = df.copy()

    # standardize key fields
    d.rename(
        columns={
            cols.lat: "lat",
            cols.lon: "lon",
            cols.temp: "t_insitu",
            cols.sal: "SP",
        },
        inplace=True,
    )
    if cols.station:
        d.rename(columns={cols.station: "station"}, inplace=True)
    else:
        d["station"] = "STATION"

    if cols.cast:
        d.rename(columns={cols.cast: "cast"}, inplace=True)
    else:
        d["cast"] = 1

    if cols.time:
        d.rename(columns={cols.time: "time_raw"}, inplace=True)
        d["time"] = parse_time(d["time_raw"])
    else:
        d["time"] = pd.NaT

    if cols.depth:
        d.rename(columns={cols.depth: "depth"}, inplace=True)
    else:
        d["depth"] = np.nan

    if cols.pressure:
        d.rename(columns={cols.pressure: "p"}, inplace=True)
    else:
        d["p"] = np.nan

    # numeric coercion
    for c in ["lat", "lon", "t_insitu", "SP", "depth", "p"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")

    # QC
    d["t_insitu"] = qc_range(d["t_insitu"], -3, 45)
    d["SP"] = qc_range(d["SP"], 0, 42)
    d["lat"] = qc_range(d["lat"], -90, 90)
    d["lon"] = qc_range(d["lon"], -180, 360)

    # handle lon in 0..360
    d.loc[d["lon"] > 180, "lon"] = d.loc[d["lon"] > 180, "lon"] - 360

    # infer pressure/depth if missing
    # If depth missing but p exists -> z from p (positive down)
    has_depth = d["depth"].notna().any()
    has_p = d["p"].notna().any()

    if (not has_depth) and has_p:
        # gsw.z_from_p returns negative z (m) for depth below sea surface
        z = gsw.z_from_p(d["p"].to_numpy(), d["lat"].to_numpy())
        d["depth"] = -z

    if (not has_p) and has_depth:
        # approximate p from depth using gsw.p_from_z (z negative)
        p = gsw.p_from_z(-d["depth"].to_numpy(), d["lat"].to_numpy())
        d["p"] = p

    # ensure depth positive down
    d.loc[d["depth"] < 0, "depth"] = np.nan

    # drop impossible rows
    d = d.dropna(subset=["lat", "lon", "depth", "t_insitu", "SP", "p"])

    # TEOS-10 derived variables
    lon = d["lon"].to_numpy()
    lat = d["lat"].to_numpy()
    p = d["p"].to_numpy()
    SP = d["SP"].to_numpy()
    t = d["t_insitu"].to_numpy()

    SA = gsw.SA_from_SP(SP, p, lon, lat)
    CT = gsw.CT_from_t(SA, t, p)
    sigma0 = gsw.sigma0(SA, CT)  # kg/m^3 - 1000

    d["SA"] = SA
    d["CT"] = CT
    d["sigma0"] = sigma0

    # profile id
    d["profile_id"] = d["station"].astype(str) + "_" + d["cast"].astype(str)

    return d


def profile_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Compute per-profile metrics: max depth, surface T/S, MLD, thermocline depth, N^2."""

    def _mld_density(g: pd.DataFrame, thresh: float = 0.03) -> float:
        gg = g.sort_values("depth")
        # reference: value at 10 m if available; else shallowest
        ref_depth = 10.0
        if (gg["depth"] <= ref_depth).any():
            ref = gg.loc[gg["depth"] <= ref_depth, "sigma0"].iloc[-1]
        else:
            ref = gg["sigma0"].iloc[0]
        drho = gg["sigma0"] - ref
        idx = np.where(drho.to_numpy() >= thresh)[0]
        if len(idx) == 0:
            return float(np.nan)
        return float(gg.iloc[idx[0]]["depth"])

    def _mld_temp(g: pd.DataFrame, dt: float = 0.2) -> float:
        gg = g.sort_values("depth")
        ref_depth = 10.0
        if (gg["depth"] <= ref_depth).any():
            ref = gg.loc[gg["depth"] <= ref_depth, "CT"].iloc[-1]
        else:
            ref = gg["CT"].iloc[0]
        dT = ref - gg["CT"]  # positive when cooler
        idx = np.where(dT.to_numpy() >= dt)[0]
        if len(idx) == 0:
            return float(np.nan)
        return float(gg.iloc[idx[0]]["depth"])

    def _thermocline_depth(g: pd.DataFrame, zmax: float = 300.0) -> float:
        gg = g.sort_values("depth")
        gg = gg.loc[gg["depth"] <= zmax].copy()
        if len(gg) < 5:
            return float(np.nan)
        z = gg["depth"].to_numpy()
        T = gg["CT"].to_numpy()
        # compute dT/dz with central differences
        dTdz = np.gradient(T, z)
        # thermocline: most negative gradient (strongest cooling with depth)
        k = np.nanargmin(dTdz)
        return float(z[k])

    def _stratification_N2(g: pd.DataFrame, zmax: float = 200.0) -> float:
        gg = g.sort_values("p")
        gg = gg.loc[gg["depth"] <= zmax].copy()
        if len(gg) < 10:
            return float(np.nan)
        SA = gg["SA"].to_numpy()
        CT = gg["CT"].to_numpy()
        p = gg["p"].to_numpy()
        lat = float(gg["lat"].median())
        try:
            N2, p_mid = gsw.Nsquared(SA, CT, p, lat=lat)
            # return median N2 in upper zmax
            return float(np.nanmedian(N2))
        except Exception:
            return float(np.nan)

    rows = []
    for pid, g in df.groupby("profile_id", sort=False):
        g = g.dropna(subset=["depth", "CT", "SA", "sigma0"]).copy()
        if len(g) < 10:
            continue
        g = g.sort_values("depth")
        max_depth = float(np.nanmax(g["depth"]))
        # surface: median in top 5 m
        surf = g.loc[g["depth"] <= 5]
        if len(surf) == 0:
            surf = g.iloc[:3]
        surf_CT = float(np.nanmedian(surf["CT"]))
        surf_SP = float(np.nanmedian(surf["SP"]))
        surf_sigma0 = float(np.nanmedian(surf["sigma0"]))

        mld_rho = _mld_density(g)
        mld_T = _mld_temp(g)
        thermo_z = _thermocline_depth(g)
        N2_med = _stratification_N2(g)

        # metadata per profile
        station = str(g["station"].iloc[0])
        cast = str(g["cast"].iloc[0])
        lat = float(np.nanmedian(g["lat"]))
        lon = float(np.nanmedian(g["lon"]))
        t = g["time"].dropna().iloc[0] if g["time"].notna().any() else pd.NaT

        rows.append(
            dict(
                profile_id=pid,
                station=station,
                cast=cast,
                time=t,
                lat=lat,
                lon=lon,
                max_depth_m=max_depth,
                surf_CT_C=surf_CT,
                surf_SP=surf_SP,
                surf_sigma0=surf_sigma0,
                mld_rho_m=mld_rho,
                mld_T_m=mld_T,
                thermocline_m=thermo_z,
                N2_median_s2=N2_med,
            )
        )

    out = pd.DataFrame(rows)
    # compute along-track distance in km using time if available; else sort by station name
    if out["time"].notna().any():
        out = out.sort_values(["time", "station", "cast"])
    else:
        out = out.sort_values(["station", "cast"])

    dist = [0.0]
    for i in range(1, len(out)):
        dist.append(
            float(
                haversine_km(
                    out.iloc[i - 1]["lon"],
                    out.iloc[i - 1]["lat"],
                    out.iloc[i]["lon"],
                    out.iloc[i]["lat"],
                )
                + dist[-1]
            )
        )
    out["distance_km"] = dist

    return out.reset_index(drop=True)


def _interp_profile_to_grid(z: np.ndarray, v: np.ndarray, zgrid: np.ndarray) -> np.ndarray:
    mask = np.isfinite(z) & np.isfinite(v)
    if mask.sum() < 2:
        return np.full_like(zgrid, np.nan, dtype=float)
    zz = z[mask]
    vv = v[mask]
    # ensure increasing
    o = np.argsort(zz)
    zz = zz[o]
    vv = vv[o]
    # remove duplicate depths by averaging
    _, idx = np.unique(zz, return_index=True)
    if len(idx) != len(zz):
        tmp = pd.DataFrame({"z": zz, "v": vv}).groupby("z", as_index=False).mean()
        zz = tmp["z"].to_numpy()
        vv = tmp["v"].to_numpy()
    out = np.interp(zgrid, zz, vv, left=np.nan, right=np.nan)
    # invalidate above shallowest and below deepest
    out[zgrid < zz.min()] = np.nan
    out[zgrid > zz.max()] = np.nan
    return out


def make_section(df: pd.DataFrame, summ: pd.DataFrame, var: str, zmax: float = 500.0, dz: float = 5.0):
    """Create section matrix [depth, profile] by interpolating each profile."""
    zgrid = np.arange(0, zmax + dz, dz)
    prof_ids = summ["profile_id"].tolist()
    mat = np.full((len(zgrid), len(prof_ids)), np.nan, dtype=float)

    for j, pid in enumerate(prof_ids):
        g = df.loc[df["profile_id"] == pid, ["depth", var]].dropna()
        if len(g) < 3:
            continue
        mat[:, j] = _interp_profile_to_grid(g["depth"].to_numpy(), g[var].to_numpy(), zgrid)

    x = summ["distance_km"].to_numpy()
    return x, zgrid, mat


def plot_station_map(summ: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(6.2, 4.8), constrained_layout=True)
    sc = ax.scatter(
        summ["lon"],
        summ["lat"],
        c=summ["max_depth_m"],
        s=45,
        cmap="viridis",
        edgecolor="k",
        linewidth=0.3,
    )
    ax.set_xlabel("Longitude (°)")
    ax.set_ylabel("Latitude (°)")
    ax.set_title("CTD station locations (colored by max cast depth)")
    cb = fig.colorbar(sc, ax=ax, label="Max depth (m)")
    ax.grid(True, alpha=0.25)
    fig.savefig(IMG_DIR / "station_map.png", dpi=200)
    plt.close(fig)


def plot_profiles(df: pd.DataFrame, summ: pd.DataFrame, n: int = 6):
    # choose evenly spaced profiles along track
    if len(summ) == 0:
        return
    idx = np.linspace(0, len(summ) - 1, min(n, len(summ))).round().astype(int)
    chosen = summ.iloc[idx]

    fig, axes = plt.subplots(1, 3, figsize=(10.8, 5.2), sharey=True, constrained_layout=True)
    for _, r in chosen.iterrows():
        g = df.loc[df["profile_id"] == r.profile_id].sort_values("depth")
        axes[0].plot(g["CT"], g["depth"], lw=1.4, label=r.profile_id)
        axes[1].plot(g["SP"], g["depth"], lw=1.4)
        axes[2].plot(g["sigma0"], g["depth"], lw=1.4)

    for ax in axes:
        ax.invert_yaxis()
        ax.grid(True, alpha=0.25)

    axes[0].set_xlabel("Conservative temperature, CT (°C)")
    axes[1].set_xlabel("Practical salinity, SP")
    axes[2].set_xlabel(r"$\sigma_0$ (kg m$^{-3}$)")
    axes[0].set_ylabel("Depth (m)")
    axes[0].set_title("Temperature")
    axes[1].set_title("Salinity")
    axes[2].set_title("Potential density anomaly")

    axes[0].legend(fontsize=7, loc="best", frameon=False)
    fig.suptitle("Selected vertical profiles across the cruise")
    fig.savefig(IMG_DIR / "vertical_profiles.png", dpi=200)
    plt.close(fig)


def plot_ts(df: pd.DataFrame, max_points: int = 60000):
    d = df[["SP", "CT", "sigma0", "depth"]].dropna().copy()
    if len(d) == 0:
        return
    if len(d) > max_points:
        d = d.sample(max_points, random_state=0)

    # density contours (sigma0)
    SP = np.linspace(d["SP"].quantile(0.01), d["SP"].quantile(0.99), 80)
    CT = np.linspace(d["CT"].quantile(0.01), d["CT"].quantile(0.99), 80)
    SPg, CTg = np.meshgrid(SP, CT)
    # approximate SA≈SP for contouring; good enough for visualization
    sig = gsw.sigma0(SPg, CTg)

    fig, ax = plt.subplots(figsize=(6.2, 5.4), constrained_layout=True)
    h = ax.scatter(d["SP"], d["CT"], c=d["depth"], s=4, cmap="viridis", alpha=0.55, linewidths=0)
    cs = ax.contour(SPg, CTg, sig, colors="k", linewidths=0.6, alpha=0.45)
    ax.clabel(cs, fmt="%.1f", fontsize=7)
    ax.set_xlabel("Practical salinity, SP")
    ax.set_ylabel("Conservative temperature, CT (°C)")
    ax.set_title("T–S diagram with $\\sigma_0$ contours (colored by depth)")
    cb = fig.colorbar(h, ax=ax, label="Depth (m)")
    ax.grid(True, alpha=0.25)
    fig.savefig(IMG_DIR / "ts_diagram.png", dpi=200)
    plt.close(fig)


def plot_sections(df: pd.DataFrame, summ: pd.DataFrame):
    if len(summ) < 2:
        return

    for var, label, cmap in [
        ("CT", "Conservative temperature (°C)", "thermal"),
        ("SP", "Practical salinity", "haline"),
        ("sigma0", r"$\\sigma_0$ (kg m$^{-3}$)", "viridis"),
    ]:
        x, z, mat = make_section(df, summ, var=var, zmax=min(800.0, float(np.nanmax(summ.max_depth_m))), dz=5.0)

        fig, ax = plt.subplots(figsize=(10.6, 4.8), constrained_layout=True)
        # pcolormesh expects edges; provide centers and let it infer
        X, Z = np.meshgrid(x, z)

        # choose colormap
        if cmap == "thermal":
            cm = plt.get_cmap("coolwarm")
        elif cmap == "haline":
            cm = plt.get_cmap("viridis")
        else:
            cm = plt.get_cmap(cmap)

        vmin, vmax = np.nanpercentile(mat, [2, 98])
        im = ax.pcolormesh(X, Z, mat, shading="auto", cmap=cm, vmin=vmin, vmax=vmax)
        ax.invert_yaxis()
        ax.set_xlabel("Along-track distance (km)")
        ax.set_ylabel("Depth (m)")
        ax.set_title(f"Vertical section of {label}")
        cb = fig.colorbar(im, ax=ax, label=label)
        ax.plot(x, np.zeros_like(x), "k.", ms=4, alpha=0.6)
        ax.grid(False)
        fig.savefig(IMG_DIR / f"section_{var}.png", dpi=200)
        plt.close(fig)


def plot_mld(summ: pd.DataFrame):
    if len(summ) == 0:
        return
    fig, ax = plt.subplots(figsize=(10.2, 3.8), constrained_layout=True)
    ax.plot(summ["distance_km"], summ["mld_rho_m"], "-o", ms=3.5, lw=1.2, label=r"MLD ($\\Delta\\sigma_0$=0.03)")
    ax.plot(summ["distance_km"], summ["mld_T_m"], "-o", ms=3.5, lw=1.2, label=r"MLD ($\\Delta T$=0.2°C)")
    ax.invert_yaxis()
    ax.set_xlabel("Along-track distance (km)")
    ax.set_ylabel("Depth (m)")
    ax.set_title("Mixed layer depth (two common criteria)")
    ax.grid(True, alpha=0.25)
    ax.legend(frameon=False)
    fig.savefig(IMG_DIR / "mixed_layer_depth.png", dpi=200)
    plt.close(fig)


def main():
    sns.set_theme(style="whitegrid", context="talk", font_scale=0.8)

    raw = pd.read_csv(DATA_PATH)
    cols = infer_columns(raw)

    clean = compute_derived(raw, cols)
    # persist clean
    try:
        clean.to_parquet(OUT_DIR / "ctd_clean.parquet", index=False)
    except Exception:
        clean.to_csv(OUT_DIR / "ctd_clean.csv", index=False)

    summ = profile_summary(clean)
    summ.to_csv(OUT_DIR / "ctd_profile_summary.csv", index=False)

    # figures
    plot_station_map(summ)
    plot_profiles(clean, summ)
    plot_ts(clean)
    plot_sections(clean, summ)
    plot_mld(summ)

    # additional validation plot: compare in-situ vs CT difference
    fig, ax = plt.subplots(figsize=(6.1, 4.6), constrained_layout=True)
    d = clean.sample(min(50000, len(clean)), random_state=0)
    ax.scatter(d["t_insitu"], d["CT"], s=3, alpha=0.25)
    lo = np.nanmin([d["t_insitu"].min(), d["CT"].min()])
    hi = np.nanmax([d["t_insitu"].max(), d["CT"].max()])
    ax.plot([lo, hi], [lo, hi], "k--", lw=1)
    ax.set_xlabel("In-situ temperature t (°C)")
    ax.set_ylabel("Conservative temperature CT (°C)")
    ax.set_title("Validation: in-situ vs TEOS-10 conservative temperature")
    ax.grid(True, alpha=0.25)
    fig.savefig(IMG_DIR / "temp_validation.png", dpi=200)
    plt.close(fig)

    # write a small JSON-like metadata for report
    meta = {
        "n_raw_rows": int(len(raw)),
        "n_clean_rows": int(len(clean)),
        "n_profiles": int(len(summ)),
        "columns_inferred": cols.__dict__,
    }
    (OUT_DIR / "run_metadata.txt").write_text(str(meta) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
