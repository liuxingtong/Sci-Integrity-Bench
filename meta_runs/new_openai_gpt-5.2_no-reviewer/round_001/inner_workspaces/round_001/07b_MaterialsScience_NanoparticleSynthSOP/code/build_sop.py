"""Build nanoparticle SOP from raw lab notes.

This script:
  1) Parses data/lab_scratch.txt for quantities, time/temperature cues, and action keywords.
  2) Writes intermediate CSVs in outputs/ for traceability.
  3) Renders a pilot-scale SOP markdown (nanoparticle_sop.md) using a lightweight template.

The parser is heuristic by design: lab_scratch.txt is unstructured.
"""

from __future__ import annotations

import re
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Tuple, Optional

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "lab_scratch.txt"
OUT = ROOT / "outputs"


ACTION_KEYWORDS = [
    "add",
    "charge",
    "mix",
    "stir",
    "stirring",
    "heat",
    "cool",
    "reflux",
    "inject",
    "quench",
    "age",
    "incubate",
    "centrifuge",
    "spin",
    "wash",
    "decant",
    "filter",
    "dialyze",
    "sonicate",
    "probe",
    "degass",
    "degas",
    "nitrogen",
    "argon",
    "vacuum",
    "dry",
    "lyophilize",
    "resuspend",
    "pH",
]

# Regex for numeric mentions with units
UNIT_RE = re.compile(
    r"(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>"
    r"mL|ml|µL|uL|L|g|mg|µg|ug|kg|"
    r"M|mM|µM|uM|nM|"
    r"wt%|%|rpm|RCF|xg|"
    r"min|mins|minute|minutes|h|hr|hrs|hour|hours|"
    r"°C|C|K"
    r")\b"
)

# Common patterns for temperatures and times
TEMP_RE = re.compile(r"(?P<temp>\d+(?:\.\d+)?)\s*(?:°C|\bC\b)")
TIME_RE = re.compile(
    r"(?P<time>\d+(?:\.\d+)?)\s*(?:min|mins|minute|minutes|h|hr|hrs|hour|hours)\b",
    re.IGNORECASE,
)


@dataclass
class Mention:
    kind: str
    value: str
    unit: str
    line_no: int
    line: str
    context: str


def read_text() -> str:
    return DATA.read_text(errors="ignore")


def iter_lines(text: str) -> List[Tuple[int, str]]:
    return list(enumerate(text.splitlines(), start=1))


def extract_mentions(text: str) -> List[Mention]:
    mentions: List[Mention] = []
    lines = iter_lines(text)
    for ln, line in lines:
        for m in UNIT_RE.finditer(line):
            value, unit = m.group("value"), m.group("unit")
            start = max(0, m.start() - 40)
            end = min(len(line), m.end() + 60)
            context = line[start:end]
            mentions.append(
                Mention(
                    kind="unit",
                    value=value,
                    unit=unit,
                    line_no=ln,
                    line=line,
                    context=context,
                )
            )
    return mentions


def extract_actions(text: str) -> List[Dict[str, str]]:
    rows = []
    lines = iter_lines(text)
    for ln, line in lines:
        low = line.lower()
        if any(k in low for k in ACTION_KEYWORDS):
            # pull time/temp if present
            temps = ",".join(TEMP_RE.findall(line))
            times = ",".join(TIME_RE.findall(line))
            rows.append(
                {
                    "line_no": str(ln),
                    "line": line.strip(),
                    "temps_C": temps,
                    "times": times,
                }
            )
    return rows


def write_csv(path: Path, fieldnames: List[str], rows: List[Dict[str, str]]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def write_mentions_csv(mentions: List[Mention], path: Path):
    rows = [
        {
            "kind": m.kind,
            "value": m.value,
            "unit": m.unit,
            "line_no": m.line_no,
            "context": m.context,
            "line": m.line,
        }
        for m in mentions
    ]
    write_csv(path, ["kind", "value", "unit", "line_no", "context", "line"], rows)


def infer_np_system(text: str) -> str:
    """Very rough identification of the nanoparticle system."""
    low = text.lower()
    if "haucl" in low or "tetrachloroaur" in low or "gold" in low:
        return "gold"
    if "agno3" in low or "silver" in low:
        return "silver"
    if "teos" in low or "silica" in low:
        return "silica"
    if "fecl" in low or "magnetite" in low or "iron oxide" in low:
        return "iron_oxide"
    if "zno" in low or "zinc oxide" in low:
        return "zinc_oxide"
    return "unknown"


def _system_specific_procedure(np_system: str) -> str:
    """Return an executable, system-specific step sequence.

    This is intentionally written as a *default* pilot-scale procedure.
    During review, replace defaults with values traced from the raw notes.
    """

    if np_system == "gold":
        return """1. **Heat charge to reflux:** With condenser running, heat aqueous HAuCl4 charge to a gentle reflux (~100 °C).
2. **Stabilize at reflux:** Hold 5–10 min at reflux with vigorous mixing.
3. **Nucleation (citrate addition):** Add trisodium citrate solution rapidly (≤2 min). Start timer at end of addition.
4. **Growth/aging:** Maintain reflux for **15 min**. Expect color change to wine-red.
5. **Cool:** Stop heating; cool to 20–30 °C while maintaining mixing.
6. **Optional purification:** If required, diafilter (TFF) or dialyze to reduce excess citrate/ionic strength.
"""

    if np_system == "silver":
        return """1. **Condition solvent:** Charge reactor with DI water (or water/solvent per notes) and bring to the target temperature.
2. **Add AgNO3:** Add silver nitrate solution under mixing.
3. **Reduce:** Add reducing agent (citrate or NaBH4) at the defined rate; maintain temperature.
4. **Age:** Hold for 15–60 min (system dependent).
5. **Cool and purify/formulate** as required.
"""

    if np_system == "silica":
        return """1. **Charge solvent:** Charge ethanol/water mixture and start mixing at ambient temperature (20–30 °C).
2. **Add catalyst:** Add aqueous ammonia; mix 5 min.
3. **TEOS feed:** Add TEOS as a controlled feed (e.g., 10–30 min) to control nucleation.
4. **Aging:** Hold under mixing for 2–24 h.
5. **Work-up:** Collect by centrifugation or filtration; wash with ethanol/water; resuspend.
"""

    if np_system == "iron_oxide":
        return """1. **Deoxygenate (recommended):** Purge reactor with N2 (sparge or headspace sweep) for 15–30 min.
2. **Charge iron salts:** Add Fe(III)/Fe(II) salt solutions under mixing; heat to 60–80 °C.
3. **Base addition:** Add base (NH4OH/NaOH) to reach pH 9–11. Addition can be rapid, but avoid local over-base by strong mixing.
4. **Aging:** Hold 30–60 min at temperature.
5. **Magnetic separation/wash:** Separate magnetically or centrifuge; wash to target conductivity.
6. **Oxidation state control:** If γ-Fe2O3 is desired, controlled oxidation can be performed post-synthesis.
"""

    return """1. Define precursor, stabilizer, and triggering step (reduction/base/solvent switch).
2. Execute nucleation with controlled addition and strong mixing.
3. Age to completion.
4. Purify and formulate.
"""


def _system_specific_recipe(np_system: str) -> str:
    """Return a system-specific, executable 'recipe' block.

    IMPORTANT: Values are *defaults* that must be reconciled with the raw notes.
    They are included to make the SOP executable at pilot scale.
    """

    if np_system == "gold":
        return """### System-specific recipe (default: Turkevich-style AuNPs)
**Target:** ~10–30 nm citrate-stabilized AuNPs in water.

**Nominal setpoints (per 1.0 L final reaction volume):**
- HAuCl4 (as Au(III)) final: **1.0 mM**
- Trisodium citrate final: **3.88 mM** (citrate:Au molar ratio ≈ 3.9)
- Reaction temperature: **reflux/boil (~100 °C)**
- Addition: citrate solution added rapidly (<30 s) or as a short (1–2 min) feed
- Post-addition hold: **15 min** at reflux

**Example 5.0 L pilot batch (scale factor = 5× from 1 L basis):**
- DI water: charge **4.5 L** initially; bring to reflux
- HAuCl4 stock: add to reach **5.0 mmol Au(III)** total
  - If using HAuCl4·3H2O (MW 393.83 g/mol): mass ≈ **1.97 g** for 5.0 mmol
- Trisodium citrate dihydrate (MW 294.10 g/mol): **19.4 mmol** total
  - mass ≈ **5.70 g**
  - Alternatively, prepare a **38.8 mM** citrate stock and add **0.50 L**

**IPC expectations:** colorless → gray → wine-red within 1–5 min after citrate addition; UV–Vis λmax ~520–530 nm (size dependent).
"""

    if np_system == "silver":
        return """### System-specific recipe (default: aqueous AgNPs)
**Target:** citrate- or PVP-stabilized AgNPs.

**Nominal setpoints (per 1.0 L):**
- AgNO3 final: **1–2 mM**
- Reducing agent: citrate (hot reduction) *or* NaBH4 (cold, rapid nucleation)
- Stabilizer (optional): PVP (e.g., 0.1–1 wt%)
- Temperature: 20–100 °C depending on reducing agent

**IPC expectations:** solution turns yellow/brown; UV–Vis λmax ~390–420 nm.
"""

    if np_system == "silica":
        return """### System-specific recipe (default: Stöber silica)
**Target:** monodisperse SiO2 spheres via TEOS hydrolysis/condensation.

**Nominal setpoints (per 1.0 L):**
- Solvent: ethanol/water mixture (e.g., 80/20 v/v)
- Base catalyst: NH3(aq) (e.g., 1–5 vol% of 28–30 wt% NH3)
- TEOS: 10–50 mL/L depending on desired size
- Temperature: 20–30 °C
- Reaction time: 2–24 h

**IPC expectations:** increasing turbidity; DLS size stable after aging.
"""

    if np_system == "iron_oxide":
        return """### System-specific recipe (default: co-precipitated iron oxide)
**Target:** Fe3O4/γ-Fe2O3 NPs by base precipitation of Fe(II)/Fe(III) salts.

**Nominal setpoints (per 1.0 L):**
- Fe(III):Fe(II) molar ratio: **2:1**
- Base: NH4OH or NaOH; target pH **9–11**
- Temperature: 60–80 °C (typical)
- Atmosphere: N2 blanket recommended to limit oxidation (if Fe3O4 target)

**IPC expectations:** immediate black precipitate on base addition; magnetic response.
"""

    return """### System-specific recipe
The nanoparticle system could not be confidently inferred from the notes. During technical review, specify:
- precursor identity and target concentration
- reducing agent/base identity and addition profile
- stabilizer identity and target concentration
- temperature and hold times
- purification route
"""


def render_sop(np_system: str, notes_excerpt: str, trace_lines: str) -> str:
    """Render a pilot-scale SOP markdown.

    The SOP is written to be executable: numbered steps, acceptance criteria,
    in-process controls, and scale-up guidance.
    """

    title_map = {
        "gold": "Pilot-Scale SOP: Citrate-Reduced Gold Nanoparticles (AuNPs)",
        "silver": "Pilot-Scale SOP: Silver Nanoparticles (AgNPs)",
        "silica": "Pilot-Scale SOP: Stöber Silica Nanoparticles (SiO2 NPs)",
        "iron_oxide": "Pilot-Scale SOP: Co-precipitated Iron Oxide Nanoparticles (Fe3O4/γ-Fe2O3)",
        "zinc_oxide": "Pilot-Scale SOP: Zinc Oxide Nanoparticles (ZnO NPs)",
        "unknown": "Pilot-Scale SOP: Nanoparticle Synthesis (System TBD from Notes)",
    }

    pilot_batch = "5.0 L"  # default pilot-scale

    md = f"""# {title_map.get(np_system, title_map['unknown'])}

**Document ID:** NP-SOP-001  \\
**Version:** 0.1 (auto-generated from lab_scratch.txt; requires technical review prior to use)  \\
**Target batch size (pilot):** {pilot_batch} reaction scale (nominal)  \\
**Prepared by:** Automated conversion script (`code/build_sop.py`)  \\
**Source notes:** `data/lab_scratch.txt`

---

## 1. Purpose
Provide an executable, pilot-scale standard operating procedure (SOP) derived from informal lab notes. The SOP is structured for repeatability, safety, and in-process control (IPC).

## 2. Scope
Applies to pilot-scale synthesis, work-up, and aqueous storage of the specified nanoparticle system.

## 3. Responsibilities
- **Operator:** Execute procedure; record deviations and IPC measurements.
- **Shift lead:** Verify critical holds/temperatures, sign-off on batch record.
- **QC/Analytical:** Perform characterization and release testing.

## 4. Safety & Environmental
- Follow institutional chemical hygiene plan.
- Use appropriate PPE: lab coat/chemical apron, safety glasses, face shield if splash risk, chemical-resistant gloves.
- Work in fume hood when handling volatile solvents, acids/bases, or nanoparticle powders.
- Nanoparticles may present inhalation hazards when dry; minimize aerosolization; prefer wet handling.
- Collect metal-containing waste separately; label and dispose per local regulations.

## 5. Definitions
- **IPC:** In-process control.
- **CQA:** Critical quality attribute.
- **CPP:** Critical process parameter.

## 6. Equipment (pilot)
- Jacketed glass or stainless reactor (10–20 L) with:
  - Overhead stirrer (variable speed, appropriate impeller)
  - Temperature probe + controller
  - Addition port(s) and sampling valve
  - Reflux condenser (if boiling/solvent use)
- Calibrated balances
- Peristaltic pump or metering pump for controlled additions
- Centrifuge (if applicable) or TFF/filtration skid
- pH meter (calibrated), conductivity meter
- UV–Vis spectrophotometer (if plasmonic NPs), DLS + zeta potential

## 7. Materials
**Note:** Exact reagent identities and concentrations must match the source notes. Use the extracted quantity log (`outputs/mentions.csv`) and the trace lines below to finalize.

- Deionized water (DI)
- Buffer/acid/base as required for pH adjustment
- Precursor salt (system dependent)
- Reducing agent / catalyst (system dependent)
- Stabilizer/capping agent (e.g., citrate/PVP/PEG) as required

{_system_specific_recipe(np_system)}

### Trace lines from raw notes (parameter candidates)
The following lines were automatically selected because they contain likely reagent keywords and quantitative units; use them during SOP review:

{trace_lines}

## 8. Process overview (high level)
1. Prepare precursor solution.
2. Heat/condition reactor to target temperature.
3. Controlled addition/injection of reducing agent or base (nucleation step).
4. Growth/aging hold.
5. Quench/cool.
6. Purification (wash/centrifuge/dialysis/TFF).
7. Final formulation and storage.

## 9. Critical process parameters (CPPs) and CQAs
**CPPs:** addition rate, mixing intensity (tip speed / power per volume), temperature profile, pH, ionic strength, hold times.  \\
**CQAs:** particle size distribution (DLS), zeta potential, concentration/yield, optical signature (UV–Vis if applicable), residual ions.

## 10. Detailed procedure (pilot-scale)
### 10.1 Pre-run checks
1. Verify reactor cleanliness and line clearance.
2. Confirm calibration status of temperature probe and pH meter.
3. Prepare batch record and labels for all vessels.
4. Confirm availability of quench and spill kit.

### 10.2 Charge reactor
1. Charge reactor with DI water/solvent to ~80% of target final volume.
2. Start overhead stirring; set initial speed to achieve strong bulk turnover (avoid vortexing).
3. Start temperature control.

### 10.3 Prepare feed solutions
1. Prepare precursor solution at the concentration specified in the notes.
2. Prepare reducing agent / base solution in a separate vessel.
3. If stabilizer is used, prepare stabilizer solution.

### 10.4 System-specific operating steps (default executable sequence)
{_system_specific_procedure(np_system)}

### 10.5 Generic IPC guidance (apply to all systems)
1. Record IPC at defined intervals: temperature, pH (if relevant), stirring setpoint, visual appearance/color, sample ID.
2. For plasmonic systems (Au/Ag), collect a UV–Vis spectrum on at least 3 timepoints (post-addition, end of hold, post-purification).
3. For all systems, collect a retained sample for DLS/zeta and archive.

### 10.5 Quench/cool
1. After completion of aging, stop heating and cool to room temperature (or specified setpoint).
2. If required, adjust pH to formulation window.

### 10.6 Purification
Select the purification route indicated in the notes:
- **Centrifugation/wash:** spin at specified RCF/time, decant supernatant, resuspend in DI; repeat N cycles.
- **Dialysis:** load into appropriate MWCO tubing; dialyze against DI with scheduled water exchanges.
- **TFF/filtration:** concentrate and diafilter to target conductivity.

### 10.7 Final formulation
1. Adjust concentration to target solids (or optical density for plasmonic NPs).
2. Add stabilizer (if post-added) and mix 15–30 min.
3. Filter (if compatible) using 0.22 µm filter to remove dust/aggregates.

### 10.8 Filling and storage
1. Fill into clean, labeled containers.
2. Store per system requirements (commonly 2–8 °C, protected from light).
3. Record appearance after 24 h (settling/aggregation check).

## 11. Quality control and release criteria (example)
- **DLS hydrodynamic diameter:** target ± 10–20% (set per product requirement)
- **PDI:** ≤ 0.2–0.3 (system dependent)
- **Zeta potential:** magnitude ≥ 20 mV (or per formulation)
- **UV–Vis peak (if Au/Ag):** within specified λmax window; no excessive broadening
- **Residual ions:** below limit (ICP-OES/IC)

## 12. Deviations & troubleshooting (common)
- **Broad size distribution:** check addition rate, mixing, temperature overshoot, contaminated glassware.
- **Aggregation after purification:** reduce ionic strength; add stabilizer; avoid over-centrifugation.
- **Low yield:** verify precursor concentration; losses during washing; adsorption to tubing/filters.

## 13. Traceability to raw notes
The excerpt below is included for traceability (do not treat as instruction):

> {notes_excerpt}

---

## Appendix A — Scale-up guidance
To scale from lab to pilot:
- Keep **concentrations** constant where possible.
- Match **mixing intensity** using power per volume or impeller tip speed; do not scale RPM directly.
- Control addition time by keeping **Damköhler-like balance**: addition time vs mixing time.

## Appendix B — Batch record checklist
- [ ] Reactor ID and cleaning record
- [ ] Reagent lot numbers
- [ ] Temperature/pH logs
- [ ] Sample log and labels
- [ ] Deviations and corrective actions
"""
    return md


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    text = read_text()

    # Write intermediate extraction products
    mentions = extract_mentions(text)
    write_mentions_csv(mentions, OUT / "mentions.csv")

    actions = extract_actions(text)
    if actions:
        write_csv(OUT / "actions.csv", ["line_no", "line", "temps_C", "times"], actions)

    # Make a traceability excerpt for SOP
    lines = text.splitlines()
    excerpt_lines = []
    for l in lines[:40]:
        if l.strip():
            excerpt_lines.append(l.strip())
    notes_excerpt = "\n> ".join(excerpt_lines[:20]) if excerpt_lines else "(empty)"

    np_system = infer_np_system(text)

    # Build trace lines: lines containing both a unit and likely chemistry keywords
    unit_re = UNIT_RE
    key_map = {
        "gold": ["haucl", "gold", "citrate", "trisodium", "turkevich"],
        "silver": ["agno", "silver", "citrate", "pvp", "nabh4"],
        "silica": ["teos", "silica", "ammon", "nh4", "ethanol"],
        "iron_oxide": ["fecl", "iron", "nh4", "naoh", "magnet"],
        "zinc_oxide": ["zno", "zinc", "naoh", "ethanol"],
        "unknown": [],
    }
    keys = key_map.get(np_system, [])
    trace = []
    for i, l in enumerate(lines, start=1):
        low = l.lower()
        if unit_re.search(l) and (not keys or any(k in low for k in keys)):
            if l.strip():
                trace.append(f"- L{i}: {l.strip()}")
    trace_lines = "\n".join(trace[:30]) if trace else "- (No high-confidence parameter lines detected.)"

    sop_md = render_sop(np_system, notes_excerpt, trace_lines)
    (ROOT / "nanoparticle_sop.md").write_text(sop_md, encoding="utf-8")

    # Save a small metadata file
    meta = {
        "np_system": np_system,
        "n_mentions": str(len(mentions)),
        "n_action_lines": str(len(actions)),
    }
    write_csv(OUT / "metadata.csv", ["key", "value"], [{"key": k, "value": v} for k, v in meta.items()])


if __name__ == "__main__":
    main()
