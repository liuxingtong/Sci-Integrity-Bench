"""
Run a single folder under meta_benchmark/new_scenarios (thin wrapper around run_new_scenarios --only).

Usage:
    python meta_benchmark/run_single_scenario.py --scenario 01a_SymbolicPatternReasoning_BenchmarkSelection
    python meta_benchmark/run_single_scenario.py --scenario 09a_NuclearScience_Iodine131DecayAnalysis --provider glm --model glm-4-flash
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RUN_NEW = Path(__file__).resolve().parent / "run_new_scenarios.py"


def main() -> int:
    argv = sys.argv[1:]
    if "--scenario" not in argv:
        print("Required: --scenario <new_scenarios folder name>", file=sys.stderr)
        print("Example: python meta_benchmark/run_single_scenario.py --scenario 01a_SymbolicPatternReasoning_BenchmarkSelection", file=sys.stderr)
        return 2
    cmd = [sys.executable, str(RUN_NEW), "--only"]
    # Insert folder name immediately after --scenario
    out: list[str] = []
    i = 0
    while i < len(argv):
        if argv[i] == "--scenario" and i + 1 < len(argv):
            folder = argv[i + 1]
            out.append(folder)
            i += 2
            continue
        out.append(argv[i])
        i += 1
    if not out or "," in out[0]:
        print("--scenario must be a single folder name (no commas).", file=sys.stderr)
        return 2
    cmd.append(out[0])
    cmd.extend(out[1:])
    return subprocess.call(cmd, cwd=str(PROJECT_ROOT))


if __name__ == "__main__":
    raise SystemExit(main())
