"""Fill simple tokens in report/report.md from computed metadata."""

from __future__ import annotations

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "report" / "report.md"
META = ROOT / "outputs" / "metadata.csv"


def main():
    rep = REPORT.read_text(encoding="utf-8")
    meta = pd.read_csv(META)
    np_system = meta.loc[meta["key"] == "np_system", "value"].iloc[0]
    rep = rep.replace("{{NP_SYSTEM}}", str(np_system))
    REPORT.write_text(rep, encoding="utf-8")


if __name__ == "__main__":
    main()
