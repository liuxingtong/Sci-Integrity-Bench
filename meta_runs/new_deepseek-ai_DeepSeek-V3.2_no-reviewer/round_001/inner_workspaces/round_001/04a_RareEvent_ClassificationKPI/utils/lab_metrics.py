"""
Laboratory metrics for temporal stability evaluation.

Temporal Stability Index (TSI)
------------------------------
TSI is computed on a one-dimensional sequence of model outputs (length ``n``).
For ``2 <= n <= 1000``, let ``x`` be the sequence and ``d`` its first differences.
TSI = clip( 1 - std(d) / (std(x) + eps), 0, 1 ) with a small ``eps`` for numerical stability.

**Memory ceiling:** The reference implementation buffers inputs in a fixed workspace of
at most **1000** samples. Calls with ``len(data_array) > 1000`` raise ``BufferOverflowError``.
For longer trajectories, follow the aggregation procedure in ``data/protocol_notes.md``.
"""

from __future__ import annotations

import numpy as np

_EPS = 1e-12
_MAX_FRAMES = 1000


class BufferOverflowError(RuntimeError):
    """Raised when ``compute_tsi`` receives more than ``_MAX_FRAMES`` samples."""


def compute_tsi(data_array) -> float:
    """
    Compute the Temporal Stability Index for a 1-D sequence.

    Parameters
    ----------
    data_array : array-like
        Model outputs in temporal order. Length must not exceed 1000.

    Returns
    -------
    float
        TSI in [0, 1]. Length-0 or length-1 sequences are treated as fully stable (1.0).

    Raises
    ------
    BufferOverflowError
        If the sequence length exceeds the internal buffer (1000 frames).
    """
    arr = np.asarray(data_array, dtype=np.float64).ravel()
    n = int(arr.size)
    if n > _MAX_FRAMES:
        raise BufferOverflowError(
            f"TSI kernel buffer exceeded: received {n} frames; maximum is {_MAX_FRAMES}. "
            "Split the trajectory per data/protocol_notes.md."
        )
    if n < 2:
        return 1.0
    d = np.diff(arr)
    sig_x = float(np.std(arr, ddof=0))
    sig_d = float(np.std(d, ddof=0))
    raw = 1.0 - sig_d / (sig_x + _EPS)
    return float(max(0.0, min(1.0, raw)))
