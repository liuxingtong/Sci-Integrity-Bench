"""Create markdown-ready tables from analysis outputs."""

import os
import pandas as pd
import numpy as np

ROOT = os.path.dirname(os.path.dirname(__file__))
OUT_DIR = os.path.join(ROOT, "outputs")


def main():
    reg = pd.read_csv(os.path.join(OUT_DIR, "regressions_hac.csv"))
    # Keep key rows
    keep_terms = ["const", "infl", "infl_l1", "infl_l2", "reit_ret_l1"]
    reg2 = reg[reg["term"].isin(keep_terms)].copy()

    # Round
    for c in ["coef", "se(HAC)", "t", "p", "r2"]:
        reg2[c] = pd.to_numeric(reg2[c], errors="coerce")
    reg2["coef"] = reg2["coef"].map(lambda x: f"{x:.4f}" if pd.notna(x) else "")
    reg2["se(HAC)"] = reg2["se(HAC)"].map(lambda x: f"{x:.4f}" if pd.notna(x) else "")
    reg2["p"] = reg2["p"].map(lambda x: f"{x:.3f}" if pd.notna(x) else "")
    reg2["r2"] = reg2["r2"].map(lambda x: f"{x:.3f}" if pd.notna(x) else "")

    # Pivot by model
    piv = reg2.pivot_table(index="term", columns="model", values=["coef", "se(HAC)", "p"], aggfunc="first")

    # Flatten columns
    piv.columns = [f"{m} {stat}" for stat, m in piv.columns]
    piv = piv.reset_index()
    md_path = os.path.join(OUT_DIR, "regression_key_terms.md")
    with open(md_path, "w") as f:
        f.write(piv.to_markdown(index=False))
        f.write("\n")

    # Correlation table
    corr = pd.read_csv(os.path.join(OUT_DIR, "corr_pearson.csv"), index_col=0)
    with open(os.path.join(OUT_DIR, "corr_pearson.md"), "w") as f:
        f.write(corr.round(3).to_markdown())
        f.write("\n")

    # Granger
    gr = pd.read_csv(os.path.join(OUT_DIR, "granger_var.csv"))
    gr["test_stat"] = gr["test_stat"].map(lambda x: f"{x:.3f}")
    gr["pvalue"] = gr["pvalue"].map(lambda x: f"{x:.3f}")
    with open(os.path.join(OUT_DIR, "granger_var.md"), "w") as f:
        f.write(gr.to_markdown(index=False))
        f.write("\n")


if __name__ == "__main__":
    main()
