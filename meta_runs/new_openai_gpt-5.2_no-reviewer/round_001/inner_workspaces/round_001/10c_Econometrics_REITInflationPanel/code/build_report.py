"""Build report/report.md by injecting computed numbers and markdown tables."""

from __future__ import annotations

import os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(__file__))


def load_clean():
    csv_path = os.path.join(ROOT, "outputs", "clean_panel.csv")
    pq_path = os.path.join(ROOT, "outputs", "clean_panel.parquet")
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")
        return df
    return pd.read_parquet(pq_path)


def main():
    df = load_clean()
    reg = pd.read_csv(os.path.join(ROOT, "outputs", "regressions_hac.csv"))
    corr = pd.read_csv(os.path.join(ROOT, "outputs", "corr_pearson.csv"), index_col=0)

    # Index can be a Timestamp or an integer quarter counter
    start = df.index.min()
    end = df.index.max()
    T = len(df)
    n_reit = int(df["reit_ret"].notna().sum())
    n_infl = int(df["infl"].notna().sum())

    mean_reit = 100 * df["reit_ret"].mean()
    sd_reit = 100 * df["reit_ret"].std()
    mean_infl = 100 * df["infl"].mean()
    sd_infl = 100 * df["infl"].std()
    mean_real = 100 * df["reit_real"].mean()
    sd_real = 100 * df["reit_real"].std()

    corr_ri = float(corr.loc["reit_ret", "infl"])

    def pull(model_prefix: str, term: str = "infl"):
        sub = reg[(reg["model"].str.startswith(model_prefix)) & (reg["term"] == term)].iloc[0]
        return float(sub["coef"]), float(sub["p"]), float(sub["r2"])

    beta_a, p_a, r2_a = pull("A")

    reg_table = open(os.path.join(ROOT, "outputs", "regression_key_terms.md"), "r").read().strip()
    granger_table = open(os.path.join(ROOT, "outputs", "granger_var.md"), "r").read().strip()

    template = open(os.path.join(ROOT, "report", "report.md"), "r").read()

    filled = template.format(
        START=start,
        END=end,
        T=T,
        N_REIT=n_reit,
        N_INFL=n_infl,
        MEAN_REIT=mean_reit,
        SD_REIT=sd_reit,
        MEAN_INFL=mean_infl,
        SD_INFL=sd_infl,
        MEAN_REAL=mean_real,
        SD_REAL=sd_real,
        CORR=corr_ri,
        BETA_A=beta_a,
        P_A=p_a,
        R2_A=r2_a,
        REG_TABLE=reg_table,
        GRANGER_TABLE=granger_table,
    )

    out_path = os.path.join(ROOT, "report", "report.md")
    with open(out_path, "w") as f:
        f.write(filled)


if __name__ == "__main__":
    main()
