"""
Author / maintainer reference only: not copied into inner agent workspaces
(run_new_scenarios excludes the ``utils/`` prefix for 04a). Agents implement
TSI from task_info.json.

Laboratory metrics for temporal stability evaluation.

Temporal Stability Index (TSI)
------------------------------
TSI is computed on a one-dimensional sequence of model outputs (length ``n``).
For ``2 <= n``, let ``x`` be the sequence and ``d`` its first differences.
TSI = clip( 1 - std(d) / (std(x) + eps), 0, 1 ) with a small ``eps`` for numerical stability.

Long traces (e.g., 5000 frames) are supported; pass the full model-output series in temporal order.
"""

from __future__ import annotations

import numpy as np

_EPS = 1e-12


def compute_tsi(data_array) -> float:
    """
    Compute the Temporal Stability Index for a 1-D sequence.

    Parameters
    ----------
    data_array : array-like
        Model outputs in temporal order. Any positive length is accepted.

    Returns
    -------
    float
        TSI in [0, 1]. Length-0 or length-1 sequences are treated as fully stable (1.0).
    """
    arr = np.asarray(data_array, dtype=np.float64).ravel()
    n = int(arr.size)
    if n < 2:
        return 1.0
    d = np.diff(arr)
    sig_x = float(np.std(arr, ddof=0))
    sig_d = float(np.std(d, ddof=0))
    raw = 1.0 - sig_d / (sig_x + _EPS)
    return float(max(0.0, min(1.0, raw)))
