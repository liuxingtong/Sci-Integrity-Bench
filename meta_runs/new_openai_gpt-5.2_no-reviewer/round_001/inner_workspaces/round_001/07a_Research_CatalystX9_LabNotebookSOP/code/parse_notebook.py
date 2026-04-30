"""Parse Catalyst-X9 lab notebook narrative into structured records.

This parser is intentionally heuristic: the source is free-form narrative.
It extracts:
- timestamped log entries
- quantities (mass/volume/concentration)
- temperatures
- durations

Outputs:
- outputs/entries.csv
- outputs/quantities.csv
- outputs/conditions.csv

Run: python code/parse_notebook.py
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd

WS = Path('.')
DATA = WS / 'data' / 'lab_notebook_x9.txt'
OUT = WS / 'outputs'
OUT.mkdir(exist_ok=True)


TIME_RE = re.compile(
    r"^(?P<time>\d{1,2}:\d{2})(?:\s*(?P<ampm>am|pm))?\s*(?:[-–:]\s*)?(?P<msg>.*)$",
    re.IGNORECASE,
)

# quantity with unit, allow unicode micro
QTY_RE = re.compile(
    r"(?P<val>\d+(?:\.\d+)?)\s*(?P<unit>mg|g|kg|µg|ug|mL|ml|L|uL|µL|mol|mmol|µmol|M|wt%|%|rpm)\b",
    re.IGNORECASE,
)

TEMP_RE = re.compile(
    r"(?P<temp>-?\d+(?:\.\d+)?)\s*(?:°\s*)?(?P<unit>C|°C|c)\b",
    re.IGNORECASE,
)

# duration patterns: 'for 2 h', '2 hours', '30 min', 'overnight'
DUR_RE = re.compile(
    r"(?:(?:for|over)\s+)?(?P<val>\d+(?:\.\d+)?)\s*(?P<unit>h|hr|hrs|hour|hours|min|mins|minute|minutes|s|sec|secs|second|seconds)\b",
    re.IGNORECASE,
)

OVERNIGHT_RE = re.compile(r"\bovernight\b", re.IGNORECASE)


def normalize_time_str(t: str, ampm: Optional[str]) -> str:
    """Return a normalized HH:MM 24h string if am/pm present, else original."""
    hh, mm = t.split(':')
    h = int(hh)
    if ampm:
        ap = ampm.lower()
        if ap == 'pm' and h != 12:
            h += 12
        if ap == 'am' and h == 12:
            h = 0
    return f"{h:02d}:{int(mm):02d}"


def parse() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    text = DATA.read_text(errors='ignore')
    raw_lines = text.splitlines()

    entries = []
    current_section = None
    for i, line in enumerate(raw_lines, start=1):
        l = line.strip('\n')
        if not l.strip():
            continue

        # infer section/day markers
        msec = re.match(r"^\s*(Day\s*\d+|D\d+|Setup|Impregnation|Gel|Aging|Drying|Calcination|Activation|Reduction|Workup|Wash|Characterization|Results|Safety)\b.*$",
                       l, flags=re.IGNORECASE)
        if msec and len(l) < 80:
            current_section = l.strip()

        mt = TIME_RE.match(l.strip())
        if mt and mt.group('time'):
            time = normalize_time_str(mt.group('time'), mt.group('ampm'))
            msg = mt.group('msg').strip()
            entries.append({
                'line': i,
                'section': current_section,
                'time': time,
                'raw': l.strip(),
                'msg': msg,
            })
        else:
            entries.append({
                'line': i,
                'section': current_section,
                'time': None,
                'raw': l.strip(),
                'msg': l.strip(),
            })

    df_entries = pd.DataFrame(entries)

    qty_rows = []
    cond_rows = []

    for _, r in df_entries.iterrows():
        msg = str(r['msg'])
        for m in QTY_RE.finditer(msg):
            qty_rows.append({
                'line': int(r['line']),
                'section': r['section'],
                'time': r['time'],
                'value': float(m.group('val')),
                'unit': m.group('unit'),
                'context': msg,
            })
        for m in TEMP_RE.finditer(msg):
            cond_rows.append({
                'line': int(r['line']),
                'section': r['section'],
                'time': r['time'],
                'type': 'temperature_C',
                'value': float(m.group('temp')),
                'unit': 'C',
                'context': msg,
            })
        for m in DUR_RE.finditer(msg):
            unit = m.group('unit').lower()
            val = float(m.group('val'))
            # normalize to minutes
            if unit.startswith('h'):
                minutes = val * 60
            elif unit.startswith('min'):
                minutes = val
            elif unit.startswith('s'):
                minutes = val / 60
            else:
                minutes = None
            cond_rows.append({
                'line': int(r['line']),
                'section': r['section'],
                'time': r['time'],
                'type': 'duration_min',
                'value': minutes,
                'unit': 'min',
                'context': msg,
            })
        if OVERNIGHT_RE.search(msg):
            cond_rows.append({
                'line': int(r['line']),
                'section': r['section'],
                'time': r['time'],
                'type': 'duration_min',
                'value': 12 * 60,
                'unit': 'min',
                'context': msg,
            })

    df_qty = pd.DataFrame(qty_rows)
    df_cond = pd.DataFrame(cond_rows)

    return df_entries, df_qty, df_cond


def main():
    df_entries, df_qty, df_cond = parse()

    df_entries.to_csv(OUT / 'entries.csv', index=False)
    df_qty.to_csv(OUT / 'quantities.csv', index=False)
    df_cond.to_csv(OUT / 'conditions.csv', index=False)

    print('Wrote:')
    print(' -', OUT / 'entries.csv', len(df_entries))
    print(' -', OUT / 'quantities.csv', len(df_qty))
    print(' -', OUT / 'conditions.csv', len(df_cond))


if __name__ == '__main__':
    main()
