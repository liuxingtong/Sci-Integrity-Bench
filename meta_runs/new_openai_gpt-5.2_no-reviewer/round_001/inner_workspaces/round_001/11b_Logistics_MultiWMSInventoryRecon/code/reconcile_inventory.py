import os
import re
import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


OUTPUT_DIR = "outputs"
FIG_DIR = os.path.join("report", "images")


@dataclass
class Schema:
    sku: str
    warehouse: Optional[str]
    location: Optional[str]
    lot: Optional[str]
    status: Optional[str]
    qty: str
    snapshot: Optional[str]


def _norm_colname(c: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(c).strip().lower()).strip("_")


def detect_schema(df: pd.DataFrame, system_name: str) -> Schema:
    cols = {c: _norm_colname(c) for c in df.columns}
    inv = {}
    for orig, norm in cols.items():
        inv.setdefault(norm, []).append(orig)

    def pick(candidates: List[str], required: bool = False) -> Optional[str]:
        for cand in candidates:
            if cand in inv:
                # If duplicates after normalization exist, pick the first original
                return inv[cand][0]
        if required:
            raise ValueError(f"[{system_name}] required column not found; tried {candidates}. Available: {list(inv.keys())}")
        return None

    sku = pick(["sku", "item", "item_sku", "item_id", "product", "product_id", "material", "part_number"], required=True)
    warehouse = pick(["warehouse", "wh", "facility", "dc", "distribution_center", "site", "plant"])
    location = pick(["location", "loc", "bin", "storage_bin", "slot", "staging_location", "zone_bin"]) 
    lot = pick(["lot", "lot_number", "batch", "batch_number", "lpn", "license_plate", "serial", "serial_number"])
    status = pick(["status", "inventory_status", "condition", "qa_status", "hold_status"])
    # Quantity: prefer on-hand then generic
    qty = pick([
        "on_hand_qty", "qty_on_hand", "onhand_qty", "onhand", "on_hand", "quantity_on_hand",
        "available_qty", "qty", "quantity", "units", "unit_qty"
    ], required=True)
    snapshot = pick(["snapshot_date", "as_of_date", "extract_date", "snapshot", "run_date", "date", "timestamp"])

    return Schema(sku=sku, warehouse=warehouse, location=location, lot=lot, status=status, qty=qty, snapshot=snapshot)


def normalize_inventory(df: pd.DataFrame, schema: Schema, system: str) -> pd.DataFrame:
    d = df.copy()

    def norm_str(s: pd.Series) -> pd.Series:
        # Keep NaNs for now; cast to string later to avoid "nan" strings
        return s.astype("string").str.strip().str.upper()

    out = pd.DataFrame({
        "system": system,
        "sku": norm_str(d[schema.sku]),
        "qty": pd.to_numeric(d[schema.qty], errors="coerce"),
    })

    for field, col in [("warehouse", schema.warehouse), ("location", schema.location), ("lot", schema.lot), ("status", schema.status)]:
        if col is None:
            out[field] = pd.NA
        else:
            out[field] = norm_str(d[col])

    if schema.snapshot is not None:
        out["snapshot"] = pd.to_datetime(d[schema.snapshot], errors="coerce")
    else:
        out["snapshot"] = pd.NaT

    # Clean up
    out["sku"] = out["sku"].fillna(pd.NA)
    for c in ["warehouse", "location", "lot", "status"]:
        out[c] = out[c].fillna(pd.NA)

    # Quantity: treat missing as 0 for aggregation; keep flag for invalids
    out["qty_invalid"] = out["qty"].isna()
    out["qty"] = out["qty"].fillna(0.0)

    return out


def choose_join_keys(alpha: pd.DataFrame, beta: pd.DataFrame) -> List[str]:
    # Choose the finest grain common between systems among canonical columns
    candidates = [
        ["sku", "warehouse", "location", "lot", "status"],
        ["sku", "warehouse", "location", "lot"],
        ["sku", "warehouse", "location"],
        ["sku", "warehouse"],
        ["sku"],
    ]
    for keys in candidates:
        if all(k in alpha.columns for k in keys) and all(k in beta.columns for k in keys):
            # Require that non-sku keys are not entirely missing in both
            ok = True
            for k in keys:
                if k == "sku":
                    continue
                if alpha[k].isna().all() and beta[k].isna().all():
                    ok = False
                    break
            if ok:
                return keys
    return ["sku"]


def aggregate(df: pd.DataFrame, keys: List[str]) -> pd.DataFrame:
    g = (df
         .groupby(keys, dropna=False, as_index=False)
         .agg(qty=("qty", "sum"),
              rows=("qty", "size"),
              invalid_qty_rows=("qty_invalid", "sum")))
    return g


def reconcile(alpha_g: pd.DataFrame, beta_g: pd.DataFrame, keys: List[str]) -> pd.DataFrame:
    m = alpha_g.merge(beta_g, on=keys, how="outer", suffixes=("_alpha", "_beta"), indicator=True)
    m["qty_alpha"] = m["qty_alpha"].fillna(0.0)
    m["qty_beta"] = m["qty_beta"].fillna(0.0)
    m["delta"] = m["qty_alpha"] - m["qty_beta"]
    m["abs_delta"] = m["delta"].abs()

    def classify(row) -> str:
        if row["_merge"] == "left_only":
            return "missing_in_beta"
        if row["_merge"] == "right_only":
            return "missing_in_alpha"
        if row["abs_delta"] == 0:
            return "match"
        return "mismatch"

    m["recon_status"] = m.apply(classify, axis=1)
    return m


def kpi_summary(recon_df: pd.DataFrame, keys: List[str]) -> Dict:
    total_records = len(recon_df)
    matched = int((recon_df["recon_status"] == "match").sum())
    mismatched = int((recon_df["recon_status"] == "mismatch").sum())
    miss_a = int((recon_df["recon_status"] == "missing_in_alpha").sum())
    miss_b = int((recon_df["recon_status"] == "missing_in_beta").sum())

    kpis = {
        "keys": keys,
        "total_records_union": total_records,
        "matched_records": matched,
        "mismatched_records": mismatched,
        "missing_in_alpha_records": miss_a,
        "missing_in_beta_records": miss_b,
        "match_rate_records": matched / total_records if total_records else np.nan,
        "total_qty_alpha": float(recon_df["qty_alpha"].sum()),
        "total_qty_beta": float(recon_df["qty_beta"].sum()),
        "net_delta_alpha_minus_beta": float(recon_df["delta"].sum()),
        "total_abs_delta": float(recon_df["abs_delta"].sum()),
        "p95_abs_delta": float(np.percentile(recon_df["abs_delta"], 95)) if total_records else np.nan,
    }
    return kpis


def plot_and_save(fig, fname: str):
    os.makedirs(FIG_DIR, exist_ok=True)
    path = os.path.join(FIG_DIR, fname)
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def make_figures(recon_df: pd.DataFrame, keys: List[str]):
    sns.set_theme(style="whitegrid")

    # Scatter alpha vs beta
    fig, ax = plt.subplots(figsize=(6, 5))
    sample = recon_df.sample(min(5000, len(recon_df)), random_state=7) if len(recon_df) else recon_df
    ax.scatter(sample["qty_beta"], sample["qty_alpha"], s=8, alpha=0.35)
    mx = max(sample["qty_alpha"].max(), sample["qty_beta"].max(), 1)
    ax.plot([0, mx], [0, mx], color="black", lw=1)
    ax.set_xlabel("Beta quantity")
    ax.set_ylabel("Alpha quantity")
    ax.set_title("Record-level quantities (sampled)\nDiagonal indicates agreement")
    plot_and_save(fig, "scatter_alpha_vs_beta.png")

    # Delta distribution
    fig, ax = plt.subplots(figsize=(7, 4))
    sns.histplot(recon_df["delta"], bins=60, ax=ax)
    ax.set_title("Distribution of quantity deltas (Alpha − Beta)")
    ax.set_xlabel("Delta")
    plot_and_save(fig, "delta_histogram.png")

    # Top discrepancies
    fig, ax = plt.subplots(figsize=(8, 5))
    top = recon_df.sort_values("abs_delta", ascending=False).head(20).copy()
    if len(top):
        top["label"] = top[keys].astype("string").fillna("∅").agg("|".join, axis=1)
        sns.barplot(data=top, x="abs_delta", y="label", ax=ax, color="#4c72b0")
        ax.set_title("Top 20 discrepancies by absolute delta")
        ax.set_xlabel("|Alpha − Beta|")
        ax.set_ylabel("Record key")
    plot_and_save(fig, "top_discrepancies.png")

    # Totals by warehouse if available
    if "warehouse" in keys and not recon_df["warehouse"].isna().all():
        by_wh = recon_df.groupby("warehouse", dropna=False).agg(
            qty_alpha=("qty_alpha", "sum"),
            qty_beta=("qty_beta", "sum"),
            abs_delta=("abs_delta", "sum"),
            records=("abs_delta", "size"),
        ).reset_index().sort_values("abs_delta", ascending=False)

        fig, ax = plt.subplots(figsize=(8, 4.5))
        by_wh_m = by_wh.melt(id_vars=["warehouse"], value_vars=["qty_alpha", "qty_beta"], var_name="system", value_name="qty")
        sns.barplot(data=by_wh_m, x="warehouse", y="qty", hue="system", ax=ax)
        ax.set_title("Total on-hand quantity by warehouse")
        ax.set_xlabel("Warehouse")
        ax.set_ylabel("Total quantity")
        ax.tick_params(axis='x', rotation=30)
        plot_and_save(fig, "totals_by_warehouse.png")

        fig, ax = plt.subplots(figsize=(8, 4.5))
        sns.barplot(data=by_wh, x="warehouse", y="abs_delta", ax=ax, color="#dd8452")
        ax.set_title("Reconciliation error volume by warehouse (sum of |deltas|)")
        ax.set_xlabel("Warehouse")
        ax.set_ylabel("Sum of |Alpha − Beta|")
        ax.tick_params(axis='x', rotation=30)
        plot_and_save(fig, "abs_delta_by_warehouse.png")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(FIG_DIR, exist_ok=True)

    alpha_raw = pd.read_csv("data/wms_alpha.csv")
    beta_raw = pd.read_csv("data/wms_beta.csv")

    alpha_schema = detect_schema(alpha_raw, "alpha")
    beta_schema = detect_schema(beta_raw, "beta")

    alpha = normalize_inventory(alpha_raw, alpha_schema, "alpha")
    beta = normalize_inventory(beta_raw, beta_schema, "beta")

    keys = choose_join_keys(alpha, beta)

    alpha_g = aggregate(alpha, keys)
    beta_g = aggregate(beta, keys)

    recon_df = reconcile(alpha_g, beta_g, keys)
    kpis = kpi_summary(recon_df, keys)

    # Save outputs
    alpha_g.to_csv(os.path.join(OUTPUT_DIR, "alpha_aggregated.csv"), index=False)
    beta_g.to_csv(os.path.join(OUTPUT_DIR, "beta_aggregated.csv"), index=False)
    recon_df.to_csv(os.path.join(OUTPUT_DIR, "reconciliation_detail.csv"), index=False)

    # Save KPI json + csv
    with open(os.path.join(OUTPUT_DIR, "kpis.json"), "w", encoding="utf-8") as f:
        json.dump(kpis, f, indent=2)
    pd.DataFrame([kpis]).to_csv(os.path.join(OUTPUT_DIR, "kpis.csv"), index=False)

    # Additional KPI table by warehouse if warehouse exists
    if "warehouse" in keys and not recon_df["warehouse"].isna().all():
        by_wh = recon_df.groupby("warehouse", dropna=False).agg(
            records=("abs_delta", "size"),
            matched=("recon_status", lambda s: int((s=="match").sum())),
            mismatched=("recon_status", lambda s: int((s=="mismatch").sum())),
            missing_in_alpha=("recon_status", lambda s: int((s=="missing_in_alpha").sum())),
            missing_in_beta=("recon_status", lambda s: int((s=="missing_in_beta").sum())),
            qty_alpha=("qty_alpha", "sum"),
            qty_beta=("qty_beta", "sum"),
            net_delta=("delta", "sum"),
            abs_delta=("abs_delta", "sum"),
        ).reset_index()
        by_wh["match_rate"] = by_wh["matched"] / by_wh["records"].replace({0: np.nan})
        by_wh.to_csv(os.path.join(OUTPUT_DIR, "kpis_by_warehouse.csv"), index=False)

    # Top discrepancies table
    top = recon_df.sort_values("abs_delta", ascending=False).head(100)
    top.to_csv(os.path.join(OUTPUT_DIR, "top_100_discrepancies.csv"), index=False)

    make_figures(recon_df, keys)

    # Basic data-quality stats
    dq = {
        "alpha_rows": int(len(alpha_raw)),
        "beta_rows": int(len(beta_raw)),
        "alpha_invalid_qty_rows": int(pd.to_numeric(alpha_raw[alpha_schema.qty], errors='coerce').isna().sum()),
        "beta_invalid_qty_rows": int(pd.to_numeric(beta_raw[beta_schema.qty], errors='coerce').isna().sum()),
        "alpha_schema": alpha_schema.__dict__,
        "beta_schema": beta_schema.__dict__,
    }
    with open(os.path.join(OUTPUT_DIR, "data_quality.json"), "w", encoding="utf-8") as f:
        json.dump(dq, f, indent=2, default=str)


if __name__ == "__main__":
    main()
