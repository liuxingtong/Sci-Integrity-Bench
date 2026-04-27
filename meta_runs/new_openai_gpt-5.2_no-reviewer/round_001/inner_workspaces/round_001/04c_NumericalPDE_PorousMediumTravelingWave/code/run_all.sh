#!/usr/bin/env bash
set -euo pipefail
python code/solve_traveling_wave.py --m 2.0 --c 1.0 --xi0 -5 --xi_max 20 --max_step 0.05 --n_grid 4000 --f_min_resid 1e-6
