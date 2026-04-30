"""Parse data/protocol.md to infer the evaluation metric parameters.

Writes outputs/metric_spec.json so the rest of the pipeline can use it.
This is best-effort and falls back to defaults if parsing fails.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


def main():
    proto = Path('data/protocol.md').read_text(encoding='utf-8')
    spec = {'name': 'SPR', 'top_frac': 0.05}

    # Look for something like "top 5%" or "top 10%" or "top_k=0.05"
    m = re.search(r"top\s*(\d+(?:\.\d+)?)\s*%", proto, flags=re.IGNORECASE)
    if m:
        spec['top_frac'] = float(m.group(1)) / 100.0

    m2 = re.search(r"top_frac\s*=?\s*(0\.\d+)", proto, flags=re.IGNORECASE)
    if m2:
        spec['top_frac'] = float(m2.group(1))

    # Another common: k = int(0.05 * N)
    m3 = re.search(r"int\s*\(\s*(0\.\d+)\s*\*\s*N\s*\)", proto, flags=re.IGNORECASE)
    if m3:
        spec['top_frac'] = float(m3.group(1))

    Path('outputs').mkdir(parents=True, exist_ok=True)
    Path('outputs/metric_spec.json').write_text(json.dumps(spec, indent=2))
    print('Wrote', spec)


if __name__ == '__main__':
    main()
