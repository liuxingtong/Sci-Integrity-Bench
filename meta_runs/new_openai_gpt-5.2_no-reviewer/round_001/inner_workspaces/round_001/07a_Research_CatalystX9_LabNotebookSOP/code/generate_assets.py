import re
import json
from pathlib import Path
from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt

WORKSPACE = Path(__file__).resolve().parents[1]
DATA = WORKSPACE / 'data' / 'lab_notebook_x9.txt'
OUT = WORKSPACE / 'outputs'
IMG = WORKSPACE / 'report' / 'images'

OUT.mkdir(parents=True, exist_ok=True)
IMG.mkdir(parents=True, exist_ok=True)

text = DATA.read_text(encoding='utf-8', errors='replace')

# ---------------------------
# Helpers
# ---------------------------

def parse_time_hhmm(s: str) -> int:
    """Return minutes since midnight for HH:MM."""
    hh, mm = s.split(':')
    return int(hh) * 60 + int(mm)


def search_one(pattern, flags=re.MULTILINE, group=1, default=None, cast=None):
    m = re.search(pattern, text, flags=flags)
    if not m:
        return default
    val = m.group(group)
    if cast:
        return cast(val)
    return val


# ---------------------------
# Extract header metadata
# ---------------------------
run_id = search_one(r"Run ID:\s*([^|\n]+)")
vessel = search_one(r"Vessel:\s*([^|\n]+)")
date_str = search_one(r"Date:\s*(\d{4}-\d{2}-\d{2})")

# ---------------------------
# Extract time-stamped events
# ---------------------------
# Matches lines like: 14:08 — Added ...
event_matches = re.findall(r"^(\d{2}:\d{2})\s+—\s+(.*)$", text, flags=re.MULTILINE)

events = []
for t_str, desc in event_matches:
    events.append({
        'time_hhmm': t_str,
        'time_min_of_day': parse_time_hhmm(t_str),
        'description': desc.strip()
    })

if events:
    t0 = min(e['time_min_of_day'] for e in events)
    for e in events:
        e['t_rel_min'] = e['time_min_of_day'] - t0
else:
    t0 = None

# ---------------------------
# Pull structured parameters from event descriptions
# ---------------------------
# Charge event
precursor_a_ml = None
precursor_a_lot = None
reagent_b_ml = None
reagent_b_lot = None
mix_rpm = None

for e in events:
    m = re.search(r"Added\s+(\d+\.?\d*)\s*mL\s+Precursor\s*A\s*\(lot\s*([^\)]+)\)\s*,\s*then\s+(\d+\.?\d*)\s*mL\s+Reagent\s*B\s*\(lot\s*([^\)]+)\)\.\s*Mixed\s+at\s+(\d+\.?\d*)\s*rpm\.?", e['description'], flags=re.IGNORECASE)
    if m:
        precursor_a_ml = float(m.group(1))
        precursor_a_lot = m.group(2).strip()
        reagent_b_ml = float(m.group(3))
        reagent_b_lot = m.group(4).strip()
        mix_rpm = float(m.group(5))

# Ramp event
ramp_target_C = None
ramp_rate_C_per_min = None
condenser_C = None
ramp_start_hhmm = None

for e in events:
    m = re.search(r"Ramped\s+temperature\s+to\s+(\d+\.?\d*)\s*°?\s*C\s+at\s+(\d+\.?\d*)\s*°?\s*C/min.*reflux.*\(condenser\s+water\s+(\d+\.?\d*)\s*°?\s*C\)", e['description'], flags=re.IGNORECASE)
    if m:
        ramp_target_C = float(m.group(1))
        ramp_rate_C_per_min = float(m.group(2))
        condenser_C = float(m.group(3))
        ramp_start_hhmm = e['time_hhmm']

# Hold event
hold_temp_C = None
hold_minutes = None
hold_start_hhmm = None
completion_indicator = None

for e in events:
    m = re.search(r"Held\s+at\s+(\d+\.?\d*)\s*°?\s*C\s+for\s+(\d+\.?\d*)\s*minutes?\s+until\s+the\s+solution\s+turned\s+([^,\.]+)", e['description'], flags=re.IGNORECASE)
    if m:
        hold_temp_C = float(m.group(1))
        hold_minutes = float(m.group(2))
        completion_indicator = m.group(3).strip()
        hold_start_hhmm = e['time_hhmm']

# Centrifuge event (not time-stamped in excerpt)
centrifuge_rpm = search_one(r"spun\s+at\s+(\d+\.?\d*)\s*RPM\s+for\s+(\d+\.?\d*)\s*minutes", cast=float, group=1)
centrifuge_minutes = search_one(r"spun\s+at\s+(\d+\.?\d*)\s*RPM\s+for\s+(\d+\.?\d*)\s*minutes", cast=float, group=2)

# Tube type
tube_type = search_one(r"transferred\s+directly\s+to\s+([^\n]+centrifuge\s+tubes)")

# Wash solvent and whether volume recorded
wash_solvent = None
wash_volume_recorded = None
if re.search(r"washed\s+once\s+with\s+cold\s+diethyl\s+ether", text, flags=re.IGNORECASE):
    wash_solvent = 'diethyl ether (cold)'
    wash_volume_recorded = not bool(re.search(r"volume\s+not\s+recorded", text, flags=re.IGNORECASE))

# Missing page indicator
page_break_missing = bool(re.search(r"page\s+break;\s+following\s+page\s+not\s+present", text, flags=re.IGNORECASE))

# ---------------------------
# Consistency checks
# ---------------------------
assumed_T0_C = 25.0

flags = []
# Ramp consistency: compare implied average ramp rate from timestamps to stated ramp
implied_ramp_rate = None
if ramp_start_hhmm and hold_start_hhmm and ramp_target_C is not None:
    t_start = parse_time_hhmm(ramp_start_hhmm)
    t_reach = parse_time_hhmm(hold_start_hhmm)
    dt_min = max(0, t_reach - t_start)
    if dt_min > 0:
        implied_ramp_rate = (ramp_target_C - assumed_T0_C) / dt_min
        # flag if large discrepancy (>25% relative)
        if ramp_rate_C_per_min and abs(implied_ramp_rate - ramp_rate_C_per_min) / ramp_rate_C_per_min > 0.25:
            flags.append({
                'type': 'ramp_rate_discrepancy',
                'message': f"Stated ramp rate {ramp_rate_C_per_min:.2f} °C/min but timestamps imply ~{implied_ramp_rate:.2f} °C/min (assuming start {assumed_T0_C:.1f} °C and reaching {ramp_target_C:.1f} °C at {hold_start_hhmm})."
            })

if wash_solvent and (wash_volume_recorded is False):
    flags.append({'type': 'missing_wash_volume', 'message': 'Ether wash volume not recorded in excerpt.'})
if page_break_missing:
    flags.append({'type': 'missing_page', 'message': 'Narrative indicates a missing page; downstream steps/parameters may be incomplete.'})

# ---------------------------
# Save extracted data tables
# ---------------------------
meta = {
    'run_id': run_id,
    'vessel': vessel,
    'date': date_str,
    'precursor_a_ml': precursor_a_ml,
    'precursor_a_lot': precursor_a_lot,
    'reagent_b_ml': reagent_b_ml,
    'reagent_b_lot': reagent_b_lot,
    'mix_rpm': mix_rpm,
    'ramp_start_hhmm': ramp_start_hhmm,
    'ramp_target_C': ramp_target_C,
    'ramp_rate_C_per_min_stated': ramp_rate_C_per_min,
    'condenser_water_C': condenser_C,
    'hold_start_hhmm': hold_start_hhmm,
    'hold_temp_C': hold_temp_C,
    'hold_minutes': hold_minutes,
    'completion_indicator': completion_indicator,
    'tube_type': tube_type,
    'centrifuge_rpm': centrifuge_rpm,
    'centrifuge_minutes': centrifuge_minutes,
    'wash_solvent': wash_solvent,
    'wash_volume_recorded': wash_volume_recorded,
    'page_break_missing': page_break_missing,
    'assumed_initial_temp_C_for_checks': assumed_T0_C,
    'implied_ramp_rate_C_per_min_from_timestamps': implied_ramp_rate,
    'flags': flags,
}

(OUT / 'summary.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')

if events:
    pd.DataFrame(events).to_csv(OUT / 'events.csv', index=False)

# ---------------------------
# Generate figures
# ---------------------------
plt.rcParams.update({'figure.dpi': 160})

# Fig 1: Timeline of recorded events
if events:
    df = pd.DataFrame(events).sort_values('time_min_of_day')
    fig, ax = plt.subplots(figsize=(8.5, 3.2))
    ax.hlines(y=0, xmin=df['t_rel_min'].min(), xmax=df['t_rel_min'].max(), color='black', lw=1)
    ax.scatter(df['t_rel_min'], [0]*len(df), s=50, color='#3d85c6', zorder=3)
    for _, r in df.iterrows():
        ax.text(r['t_rel_min'], 0.05, f"{r['time_hhmm']}\n{r['description']}",
                rotation=25, ha='left', va='bottom', fontsize=8)
    ax.set_ylim(-0.2, 1.2)
    ax.set_yticks([])
    ax.set_xlabel('Minutes from first recorded event')
    ax.set_title('Catalyst‑X9 notebook excerpt: recorded timeline events')
    ax.grid(True, axis='x', alpha=0.25)
    fig.tight_layout()
    fig.savefig(IMG / 'fig1_timeline.png')
    plt.close(fig)

# Fig 2: Temperature program comparison (stated ramp vs timestamp-implied)
# Build temperature curves relative to ramp start.
if ramp_start_hhmm and ramp_target_C is not None and hold_start_hhmm and hold_minutes is not None:
    t_start = parse_time_hhmm(ramp_start_hhmm)
    t_hold = parse_time_hhmm(hold_start_hhmm)
    t0_rel = 0
    # relative times
    ramp_dt_obs = max(0, t_hold - t_start)
    hold_dt = hold_minutes

    # Programmed reach time using stated ramp (assuming start at T0)
    ramp_dt_prog = (ramp_target_C - assumed_T0_C) / ramp_rate_C_per_min if ramp_rate_C_per_min else None

    # Create time grid
    t_end = max(ramp_dt_obs + hold_dt, (ramp_dt_prog + hold_dt) if ramp_dt_prog is not None else 0)
    t = pd.Series(range(0, int(round(t_end)) + 1))

    def temp_profile(ramp_dt):
        if ramp_dt <= 0:
            return pd.Series([ramp_target_C] * len(t))
        temps = []
        for ti in t:
            if ti <= ramp_dt:
                temps.append(assumed_T0_C + (ramp_target_C - assumed_T0_C) * (ti / ramp_dt))
            elif ti <= ramp_dt + hold_dt:
                temps.append(ramp_target_C)
            else:
                temps.append(ramp_target_C)
        return pd.Series(temps)

    T_obs = temp_profile(ramp_dt_obs)
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    ax.plot(t, T_obs, lw=2.5, color='#6aa84f', label=f"Implied by timestamps (reach at {hold_start_hhmm})")

    if ramp_dt_prog is not None:
        T_prog = temp_profile(ramp_dt_prog)
        ax.plot(t, T_prog, lw=2.0, color='#3d85c6', ls='--', label=f"Stated ramp {ramp_rate_C_per_min:.1f} °C/min (assumed start {assumed_T0_C:.0f}°C)")
        ax.axvline(ramp_dt_prog, color='#3d85c6', alpha=0.25)

    ax.axvline(ramp_dt_obs, color='#6aa84f', alpha=0.25)
    ax.set_xlabel(f"Minutes from ramp start ({ramp_start_hhmm})")
    ax.set_ylabel('Temperature (°C)')
    ax.set_title('Temperature ramp/hold: stated vs. timestamp-implied profile')
    ax.grid(True, alpha=0.25)
    ax.legend(frameon=True, fontsize=8, loc='lower right')

    # annotate discrepancy if applicable
    if implied_ramp_rate is not None and ramp_rate_C_per_min is not None:
        ax.text(0.02, 0.98,
                f"Stated ramp: {ramp_rate_C_per_min:.2f} °C/min\nImplied avg ramp: {implied_ramp_rate:.2f} °C/min",
                transform=ax.transAxes, ha='left', va='top',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.85, edgecolor='#666'))

    fig.tight_layout()
    fig.savefig(IMG / 'fig2_temperature_profile.png')
    plt.close(fig)

# Fig 3: Data completeness for shift-handoff critical fields
required_fields = [
    ('Reactor/vessel identified', vessel is not None),
    ('Run ID recorded', run_id is not None),
    ('Date recorded', date_str is not None),
    ('Precursor A volume recorded', precursor_a_ml is not None),
    ('Precursor A lot recorded', precursor_a_lot is not None),
    ('Reagent B volume recorded', reagent_b_ml is not None),
    ('Reagent B lot recorded', reagent_b_lot is not None),
    ('Mixing speed recorded', mix_rpm is not None),
    ('Ramp target recorded', ramp_target_C is not None),
    ('Ramp rate recorded', ramp_rate_C_per_min is not None),
    ('Condenser water temp recorded', condenser_C is not None),
    ('Hold time recorded', hold_minutes is not None),
    ('Hold temperature recorded', hold_temp_C is not None),
    ('Endpoint indicator recorded (color)', completion_indicator is not None),
    ('Centrifuge RPM recorded', centrifuge_rpm is not None),
    ('Centrifuge time recorded', centrifuge_minutes is not None),
    ('Tube type recorded', tube_type is not None),
    ('Wash solvent recorded', wash_solvent is not None),
    ('Wash volume recorded', bool(wash_volume_recorded)),
    ('No missing pages indicated', not page_break_missing),
]

df_comp = pd.DataFrame(required_fields, columns=['Field', 'Present'])
df_comp.to_csv(OUT / 'completeness.csv', index=False)

fig, ax = plt.subplots(figsize=(8.5, 4.6))
# plot as horizontal bar: 1 present, 0 missing
vals = df_comp['Present'].astype(int)
colors = ['#6aa84f' if v == 1 else '#cc0000' for v in vals]
ax.barh(df_comp['Field'], vals, color=colors)
ax.set_xlim(0, 1)
ax.set_xlabel('Present (1) vs Missing (0)')
ax.set_title('Notebook excerpt completeness vs. shift-handoff minimum fields')
ax.grid(True, axis='x', alpha=0.25)
# add legend-like labels
ax.text(0.98, 0.02, f"Present: {vals.sum()}/{len(vals)}",
        transform=ax.transAxes, ha='right', va='bottom',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.85, edgecolor='#666'))
fig.tight_layout()
fig.savefig(IMG / 'fig3_completeness.png')
plt.close(fig)

# Fig 4: Centrifugation parameters (if present)
fig, ax = plt.subplots(figsize=(5.8, 3.6))
if centrifuge_rpm is not None and centrifuge_minutes is not None:
    ax.bar(['RPM', 'Time (min)'], [centrifuge_rpm, centrifuge_minutes], color=['#8e7cc3', '#f6b26b'])
    ax.set_title('Isolation step: centrifugation settings (from excerpt)')
    for i, v in enumerate([centrifuge_rpm, centrifuge_minutes]):
        ax.text(i, v + max(centrifuge_rpm, centrifuge_minutes)*0.03, f"{v:.0f}", ha='center', va='bottom')
    ax.grid(True, axis='y', alpha=0.25)
else:
    ax.text(0.5, 0.5, 'Centrifuge settings not found in excerpt', ha='center', va='center')
    ax.axis('off')
fig.tight_layout()
fig.savefig(IMG / 'fig4_centrifugation.png')
plt.close(fig)

print('Wrote', OUT)
print('Wrote', IMG)
