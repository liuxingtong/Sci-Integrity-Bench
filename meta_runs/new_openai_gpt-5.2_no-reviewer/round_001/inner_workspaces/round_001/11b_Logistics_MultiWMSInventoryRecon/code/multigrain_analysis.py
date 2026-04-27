import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from reconcile_inventory import detect_schema, normalize_inventory, aggregate, reconcile, kpi_summary

OUTPUT_DIR = "outputs"
FIG_DIR = os.path.join("report", "images")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(FIG_DIR, exist_ok=True)

    alpha_raw = pd.read_csv("data/wms_alpha.csv")
    beta_raw = pd.read_csv("data/wms_beta.csv")

    alpha_schema = detect_schema(alpha_raw, "alpha")
    beta_schema = detect_schema(beta_raw, "beta")

    alpha = normalize_inventory(alpha_raw, alpha_schema, "alpha")
    beta = normalize_inventory(beta_raw, beta_schema, "beta")

    # Candidate grains in decreasing detail
    grains = [
        ["sku", "warehouse", "location", "lot", "status"],
        ["sku", "warehouse", "location", "lot"],
        ["sku", "warehouse", "location"],
        ["sku", "warehouse"],
        ["sku"],
    ]

    rows = []
    for keys in grains:
        # only keep if columns exist
        if not all(k in alpha.columns for k in keys):
            continue
        if not all(k in beta.columns for k in keys):
            continue
        # skip if all optional keys are NA in both
        ok=True
        for k in keys:
            if k=="sku":
                continue
            if alpha[k].isna().all() and beta[k].isna().all():
                ok=False
                break
        if not ok:
            continue

        a_g = aggregate(alpha, keys)
        b_g = aggregate(beta, keys)
        r = reconcile(a_g, b_g, keys)
        kpis = kpi_summary(r, keys)
        rows.append(kpis)

    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(OUTPUT_DIR, "multigrain_kpis.csv"), index=False)

    # Plot match rate by grain
    if len(out):
        out_plot = out.copy()
        out_plot["grain"] = out_plot["keys"].apply(lambda ks: "+".join(ks))
        fig, ax = plt.subplots(figsize=(7.5, 4))
        sns.barplot(data=out_plot, x="grain", y="match_rate_records", ax=ax, color="#4c72b0")
        ax.set_ylim(0, 1)
        ax.set_ylabel("Match rate (records)")
        ax.set_xlabel("Join grain")
        ax.set_title("Reconciliation match rate by join grain")
        ax.tick_params(axis='x', rotation=30)
        fig.savefig(os.path.join(FIG_DIR, "match_rate_by_grain.png"), dpi=200, bbox_inches="tight")
        plt.close(fig)


if __name__ == "__main__":
    main()
