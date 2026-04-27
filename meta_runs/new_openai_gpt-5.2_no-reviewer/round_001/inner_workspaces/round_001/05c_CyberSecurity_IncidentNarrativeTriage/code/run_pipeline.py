#!/usr/bin/env python
"""End-to-end pipeline for scenario 05c.

Steps:
1) Analyze narratives and generate summary tables + figures.
2) Call Gemini (gemini-1.5-pro) and save raw JSON.
3) Build report/report.md.

Usage:
  python code/run_pipeline.py

Requires:
  - pandas, seaborn, matplotlib
  - google-generativeai (for step 2)
  - env var GOOGLE_API_KEY (or GEMINI_API_KEY)
"""

from __future__ import annotations

import subprocess
import sys


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.check_call(cmd)


def main() -> None:
    run([sys.executable, "code/analyze_incidents.py"])
    run([sys.executable, "code/gemini_triage.py"])
    run([sys.executable, "code/build_report.py"])


if __name__ == "__main__":
    main()
