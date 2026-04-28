# Standard Operating Procedure: Pilot-Scale Copper Nanoparticle (NanoCu) Synthesis

**Document ID:** SOP-NANO-CU-001  
**Version:** 1.0  
**Date:** 2024  
**Derived from:** `lab_scratch.txt` (bench notes)  
**Scale:** Pilot (100 mL batch)

---

## 1. Purpose

This SOP describes the reproducible synthesis of copper nanoparticles (NanoCu) via thermal decomposition/reduction of a copper precursor in the presence of a stabilizing surfactant. It converts informal bench notes into a structured, executable protocol suitable for pilot-scale production.

---

## 2. Scope

Applicable to all personnel conducting NanoCu synthesis in the materials science laboratory. Pilot scale is defined as 100 mL reaction volume.

---

## 3. Safety & PPE

| Hazard | Control |
|--------|--------|
| Hot oil bath (110 °C) | Heat-resistant gloves, lab coat, safety glasses |
| Flammable solvents (ethanol, oleylamine) | Fume hood; no open flames |
| Copper compounds (skin/eye irritant) | Nitrile gloves, eye protection |
| Centrifuge operation | Balance rotors; follow centrifuge SOP |

---

## 4. Materials & Equipment

### Reagents
| Reagent | Role | Quantity (100 mL batch) |
|---------|------|------------------------|
| Copper(II) acetate monohydrate | Precursor A (Cu source) | 2.0 g (10 mmol) |
| Oleylamine (OAm, 70%) | Surfactant / reducing agent | 6.5 mL (2 equiv.) |
| 1-Octadecene (ODE) | High-boiling solvent | 80 mL |
| Ethanol (200 proof) | Washing solvent | 150 mL |

### Equipment
- 250 mL three-neck round-bottom flask
- Oil bath with temperature controller (±2 °C)
- Magnetic stir bar + stir plate
- Syringe pump (1 mL/min)
- Reflux condenser
- Centrifuge (capable of 8000 rpm)
- UV-Vis spectrophotometer (optional, for endpoint verification)

---

## 5. Procedure

### Step 1 — Oil Bath Preparation
1. Fill oil bath with silicone oil to appropriate level.
2. Set temperature controller to **110 °C**.
3. Allow bath to equilibrate for **≥15 min** before proceeding.
4. **Checkpoint:** Confirm temperature reads 110 ± 2 °C on calibrated thermometer.

### Step 2 — Solvent Loading
1. Add 80 mL of 1-octadecene (ODE) to the 250 mL flask.
2. Attach reflux condenser and nitrogen/argon inlet.
3. Purge flask with inert gas for **10 min** at room temperature.
4. Lower flask into preheated oil bath.

### Step 3 — Precursor A Addition (Dropwise)
1. Prepare Precursor A solution: dissolve 2.0 g copper(II) acetate in 10 mL ODE (warm gently if needed).
2. Load into syringe; attach to syringe pump.
3. Add Precursor A **dropwise at ~1 mL/min** into the stirring hot solvent.
4. **Observe:** Solution will initially appear blue-green (Cu²⁺ complex).
5. **Checkpoint:** Confirm no sudden exotherm (>5 °C rise); if observed, pause addition.

### Step 4 — Surfactant Addition & Overnight Stirring
1. Immediately after Precursor A addition, add **6.5 mL oleylamine** via syringe in one portion.
2. Increase stir rate to **600 rpm**.
3. Maintain at **110 °C for 12 hours** (overnight).
4. Keep flask under inert atmosphere throughout.
5. **Checkpoint at 6 h:** Solution should be transitioning from blue-green toward brown/amber.

### Step 5 — Color Endpoint Verification
1. At t = 12 h, visually inspect reaction mixture.
2. **Expected color: brown** (confirms Cu²⁺ → Cu⁰ reduction complete).
3. If still blue-green: extend reaction by **2 h increments** (max 16 h total).
4. Optional: take 0.1 mL aliquot, dilute in hexane, measure UV-Vis (Cu NP plasmon peak ~580 nm).

### Step 6 — Quench & Workup
1. Remove flask from oil bath; allow to cool to **room temperature (~30 min)**.
2. Add **50 mL ethanol** to precipitate nanoparticles; mix well.
3. Transfer to centrifuge tubes; centrifuge at **8000 rpm × 10 min**.
4. Decant supernatant; redisperse pellet in **10 mL hexane**.
5. Repeat ethanol wash **2 more times** (3× total).
6. After final wash, redisperse NPs in desired storage solvent (hexane or toluene).

### Step 7 — Characterization
| Test | Method | Acceptance Criterion |
|------|--------|---------------------|
| Particle size | TEM or DLS | 5–15 nm (mean ~8 nm) |
| Size distribution | TEM histogram | PDI < 0.2 |
| Crystal structure | XRD | Cu FCC peaks (2θ = 43.3°, 50.4°, 74.1°) |
| Yield | Gravimetric | ≥ 40% |
| Color | Visual | Brown colloidal suspension |

---

## 6. Troubleshooting

| Symptom | Likely Cause | Action |
|---------|-------------|--------|
| Solution remains blue-green after 12 h | Insufficient reduction | Extend reaction 2 h; check temperature |
| Large aggregates / black precipitate | Overreduction or too-fast addition | Slow precursor addition; reduce temperature to 100 °C |
| Low yield (<20%) | Incomplete precipitation | Add more ethanol; centrifuge longer |
| Broad size distribution | Nucleation not separated from growth | Add precursor more slowly; use syringe pump |

---

## 7. Waste Disposal

- Copper-containing waste: collect in labeled heavy-metal waste container.
- Organic solvents (ODE, hexane, toluene): collect in halogen-free organic waste.
- Ethanol washes: collect in organic waste.

---

## 8. References

1. Mott, D. et al. *Synthesis of size-controlled and shaped copper nanoparticles.* Langmuir 2007.
2. Guo, X. et al. *Oleylamine as reducing agent and stabilizer for Cu NP synthesis.* J. Mater. Chem. 2011.
3. Internal bench notes: `lab_scratch.txt` (NanoCu synthesis, undated).

---

*This SOP was generated by structured interpretation of informal lab notes. All quantities and conditions should be validated experimentally before full-scale production.*
