"""Deprecated: use `update_scenario_trap_index.py` to rebuild scenario_trap_index.json.

The old restore logic inserted id 19 as 07c and broke id 18; kept only as a redirect.
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
subprocess.check_call([sys.executable, str(HERE / "update_scenario_trap_index.py")])
