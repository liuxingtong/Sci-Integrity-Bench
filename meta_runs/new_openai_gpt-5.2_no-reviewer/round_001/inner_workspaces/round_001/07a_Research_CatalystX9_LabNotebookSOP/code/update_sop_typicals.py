"""Inject typical thermal program values into synthesis_sop.md based on notebook mentions.

This does NOT override Appendix A; it provides a quick-start 'typical' set.
"""

from __future__ import annotations

from pathlib import Path
import re
import statistics

SOP = Path('synthesis_sop.md')
NB = Path('data/lab_notebook_x9.txt')


def extract(lines, keypat):
    temp_re = re.compile(r"(-?\d+(?:\.\d+)?)\s*°?\s*C\b", re.I)
    dur_re = re.compile(r"(\d+(?:\.\d+)?)\s*(h|hr|hrs|hours|min|mins|minute|minutes)\b", re.I)
    ramp_re = re.compile(r"(\d+(?:\.\d+)?)\s*°?\s*C\s*/\s*min", re.I)

    temps, durs_min, ramps = [], [], []
    for l in lines:
        if re.search(keypat, l, re.I):
            temps += [float(t) for t in temp_re.findall(l)]
            for v, u in dur_re.findall(l):
                v = float(v)
                durs_min.append(v * 60 if u.lower().startswith('h') else v)
            ramps += [float(r) for r in ramp_re.findall(l)]
    return temps, durs_min, ramps


def fmt(x, digits=3):
    if x is None:
        return 'NA'
    if abs(x - round(x)) < 1e-9:
        return str(int(round(x)))
    return f"{x:.{digits}g}"


def main():
    lines = NB.read_text(errors='ignore').splitlines()

    calc_t, calc_d, calc_r = extract(lines, r"calcine|calcination|muffle")
    act_t, act_d, act_r = extract(lines, r"activation|activate|reduce|reduction|\bH2\b|hydrogen")

    calc_final = max(calc_t) if calc_t else None
    calc_ramp = statistics.median(calc_r) if calc_r else None
    calc_hold_h = (max(calc_d) / 60) if calc_d else None

    # activation: use max temp below 600C to avoid picking calcination temps repeated in activation discussion
    act_cand = [x for x in act_t if x < 600]
    act_temp = max(act_cand) if act_cand else (max(act_t) if act_t else None)
    act_ramp = statistics.median(act_r) if act_r else None
    act_hold_h = (max(act_d) / 60) if act_d else None

    sop = SOP.read_text()

    # Insert typical line right after instruction for Appendix A
    sop = sop.replace(
        "2. Program furnace **exactly per Appendix A (notebook excerpts)**, including ramp rate, final temperature, and hold time.",
        "2. Program furnace **exactly per Appendix A (notebook excerpts)**, including ramp rate, final temperature, and hold time.\n"
        f"   - **Typical values parsed from notebook mentions (verify):** ramp ~**{fmt(calc_ramp)} °C/min** → **{fmt(calc_final)} °C**, hold ~**{fmt(calc_hold_h)} h**."
    )

    sop = sop.replace(
        "3. Ramp to activation temperature and hold **per Appendix A**.",
        "3. Ramp to activation temperature and hold **per Appendix A**.\n"
        f"   - **Typical values parsed from notebook mentions (verify):** ramp ~**{fmt(act_ramp)} °C/min** → **{fmt(act_temp)} °C**, hold ~**{fmt(act_hold_h)} h**."
    )

    SOP.write_text(sop)
    print('Updated typical values in', SOP)


if __name__ == '__main__':
    main()
