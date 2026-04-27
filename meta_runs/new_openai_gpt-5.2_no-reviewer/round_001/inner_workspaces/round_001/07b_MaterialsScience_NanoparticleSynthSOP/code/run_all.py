"""Reproduce all outputs for scenario 07b.

Runs:
  1) build_sop.py -> nanoparticle_sop.md + outputs/*.csv
  2) make_figures.py -> report/images/*.png
  3) update_report_stats.py + fill_report_tokens.py -> report/report.md
"""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd):
    subprocess.check_call(cmd, cwd=ROOT)


def main():
    run(["python", "code/build_sop.py"])
    run(["python", "code/make_figures.py"])
    run(["python", "code/update_report_stats.py"])
    run(["python", "code/fill_report_tokens.py"])


if __name__ == "__main__":
    main()
