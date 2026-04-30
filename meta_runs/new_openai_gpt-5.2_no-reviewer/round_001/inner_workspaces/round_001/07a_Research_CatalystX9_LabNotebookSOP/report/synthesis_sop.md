# SOP: Catalyst‑X9 Synthesis (bench execution; shift-handoff ready)

- **SOP ID:** CAT‑X9‑SYN
- **Version:** 0.1 (derived from `data/lab_notebook_x9.txt`)
- **Effective date:** 2026‑04‑30
- **Owner:** Lab Operations (Catalyst synthesis)
- **Applies to:** Night shift bench synthesis + furnace activation

## 1. Purpose
Convert the Catalyst‑X9 notebook narrative into a **repeatable, handoff-safe** synthesis procedure with explicit hold points, records, and acceptance checks.

## 2. Scope
This SOP covers Catalyst‑X9 preparation from **support pre-treatment → precursor solution preparation → impregnation/addition → aging/hold → drying → calcination → activation/reduction → packaging & QC**.

## 3. Responsibilities
- **Operator (shift):** execute steps, complete the batch record, label all intermediates, initiate/receive handoffs.
- **Shift lead:** verify safety controls (gas, furnace), approve hold-point transitions.
- **QA/Process owner:** review deviations and update this SOP under version control.

## 4. Safety and hazards (mandatory)
1. **Hot equipment:** ovens/furnaces/tube furnaces and crucibles cause severe burns. Use heat gloves, tongs, face shield.
2. **Pressurized / flammable gas:** activation may use **H₂/N₂/Ar**. Perform leak checks, ensure exhaust/ventilation, use flashback arrestors, follow facility hydrogen SOP.
3. **Corrosives / toxics:** metal salts, acids/bases (if used) are irritants/toxic. Wear lab coat, goggles, appropriate gloves; work in a fume hood.
4. **Dust inhalation:** calcined powders are respirable. Handle in hood; use dust mask/respirator per site EHS.
5. **Waste:** segregate aqueous metal-containing waste; collect solvent waste in labeled container.

## 5. Definitions
- **IW (incipient wetness):** addition of solution volume equal to support pore volume.
- **Hold point:** defined stop where material can be safely stored for handoff.

## 6. Materials & equipment
> **Populate exact reagents/amounts from batch record Table 1.** This SOP is structured to accept the exact quantities logged in the source notebook; see `outputs/quantity_contexts_enriched.csv` for extracted quantity mentions.

### 6.1 Required equipment
- Analytical balance (±0.1 mg) and top-loading balance
- Glassware: beakers, graduated cylinders, stir bars, funnels
- Stir plate / overhead stirrer (as required)
- Drying oven (ambient → 120 °C range)
- Furnace (muffle) and/or tube furnace with programmable ramp/hold
- Gas manifold (N₂/Ar; H₂ if activation requires)
- Thermocouple/temperature logger (preferred)
- Desiccator, labeled sample jars/vials

### 6.2 Consumables
- Filter paper / frit (if filtration occurs)
- Weigh boats, spatulas, labels, lab tape
- PPE: nitrile gloves, heat gloves, goggles/face shield

### 6.3 Notebook-derived bill of materials (traceability table)
The table below is **parsed from the notebook narrative** (heuristic extraction). Use it to populate Table 1 targets and to resolve ambiguities during night-shift execution.

> Source: `outputs/reagents_proposed.csv` (generated from `data/lab_notebook_x9.txt`).

| Notebook line | Reagent (parsed) | Amount | Unit | Source text |
|---:|---|---:|---|---|


## 7. Documentation (batch record)
Create a batch record at start and attach printouts/exports.

### 7.1 Batch identifiers (fill)
- **Batch ID:** CAT‑X9‑<YYYYMMDD>-<###>
- **Operator:** ____  **Date/Shift:** ____
- **Notebook source:** `lab_notebook_x9.txt`

### 7.2 Table 1 — Reagents (copy from weigh sheets)
Record **reagent name, lot, purity, target amount, actual amount, units, and step used**.

| Reagent | Lot | Purity | Target | Actual | Units | Step |
|---|---|---:|---:|---:|---|---|
| Support (X9 support) |  |  |  |  | g | 8 |
| Metal precursor A |  |  |  |  | g / mL | 9 |
| Metal precursor B (if applicable) |  |  |  |  | g / mL | 9 |
| Solvent (DI water / alcohol) |  |  |  |  | mL | 9 |
| Optional pH adjuster |  |  |  |  | mL | 9 |

## 8. Procedure
### 8.1 Pre‑run checklist (before weighing)
- [ ] Confirm **hood** is operational.
- [ ] Confirm **furnace/tube furnace** is available and has correct program slots.
- [ ] If using gases: verify **cylinder pressures**, regulators, and **leak check** (soap test or leak detector).
- [ ] Print blank batch record and label set (support, wet cake, dried, calcined, activated, final).

---

### 8.2 Support pre‑treatment (if used)
1. **Weigh support** into a clean, labeled dish/crucible.
2. **Pre‑dry** in oven (typ. 110–120 °C) to constant mass.
3. Cool in a **desiccator**; record mass before/after.

**In‑process check:** mass change ≤0.5% over 30–60 min indicates dry/constant.

**HOLD POINT A:** Dried support may be stored **sealed in desiccator** up to 24 h. Record: mass, time, storage location.

---

### 8.3 Precursor solution preparation
1. In hood, add measured solvent to a beaker.
2. Add metal precursor(s) gradually while stirring until fully dissolved.
3. If notebook specifies **order of addition**, follow that order.
4. If pH adjustment is specified, adjust slowly; record final pH.

**In‑process check:** solution should be clear (or per notebook appearance). Record color/clarity.

---

### 8.4 Impregnation / addition onto support
> Use either **incipient wetness** (preferred for porous supports) or **slurry impregnation**, per notebook.

1. Place dried support in a mixing vessel.
2. Add precursor solution **slowly (dropwise or in aliquots)** with continuous stirring to avoid localized overwetting.
3. Scrape vessel walls; mix until homogeneous.
4. If notebook calls for **aging/soak**, cover vessel to minimize evaporation.

**In‑process check:** paste/slurry should be uniform; no dry pockets.

**HOLD POINT B:** Wet impregnated solid may be held **covered** at RT for defined aging time (record start/end).

---

### 8.5 Aging / hold
1. Maintain at specified temperature (RT or warmed) for the specified duration.
2. Mix intermittently if required.

Record: start time, end time, temperature.

---

### 8.6 Drying
1. Transfer wet solid to a drying dish (thin layer).
2. Dry in oven using the notebook‑specified temperature/time (commonly 80–120 °C).
3. Break up agglomerates gently mid‑dry if instructed.

**In‑process check:** constant mass criterion (two weights separated by ≥30 min).

**HOLD POINT C:** Dried precursor can be stored sealed/desiccated up to 72 h.

---

### 8.7 Calcination (air)
1. Load dried material in an appropriate crucible/boat (do not overfill).
2. Program furnace:
   - Ramp: **___ °C/min** to **___ °C**
   - Hold: **___ h**
   - Cool: passive to ≤80 °C before opening
3. Start program; record program name/ID.
4. After cool, transfer to desiccator; record calcined mass and appearance.

**Critical control:** avoid rapid heating that causes spattering; follow notebook ramp rate.

**HOLD POINT D:** Calcined solid may be stored in sealed jar with desiccant.

---

### 8.8 Activation / reduction (tube furnace; inert/H₂ as required)
> Execute only if activation is part of Catalyst‑X9 as recorded in notebook.

1. Load calcined sample into quartz boat; place in tube furnace.
2. Purge with inert gas (N₂/Ar) to remove air (flow and purge duration **per Appendix A**).
3. Ramp to activation temperature and hold **per Appendix A**.
   - **Typical values parsed from notebook mentions (verify):** ramp ~**NA °C/min** → **NA °C**, hold ~**NA h**.
4. If using H₂, switch to H₂/inert mix at the notebook-specified fraction and flow; monitor exhaust.
5. After hold, cool under inert.
6. If required, **passivate** (controlled dilute O₂/N₂ exposure) before opening to air.

Record: gas type(s), flow rates, ramp/hold, temperatures, start/end times.

**HOLD POINT E:** Activated catalyst must be stored **air‑sensitive or passivated** per notebook.

---

### 8.9 Packaging, labeling, and yield
1. Transfer final material to labeled container.
2. Record final mass and calculated yield (if applicable).
3. Archive a **retain sample** (minimum **2 g**, or per program requirement) with Batch ID.

Label must include: Batch ID, date, operator, state (dried/calcined/activated), hazards.

---

## 8.10 Appendix A — Notebook excerpt parameters (for exact program setpoints)

### Notebook-derived thermal/gas program notes (verbatim excerpts)
The following excerpted lines contain the temperature ramps/holds and gas flows mentioned in the notebook. Use these to set furnace programs exactly.

- `0009: 14:20 — Ramped temperature to 120 °C at 5 °C/min under reflux (condenser water 18 °C).`


## 9. Quality control (minimum)
- **Appearance:** color/texture consistent with prior batches; note deviations.
- **Mass balance:** record at each hold point.
- **Optional:** BET surface area, XRD, ICP‑OES metals loading (per program needs).

## 10. Deviations and troubleshooting
- If solution does not dissolve: confirm solvent identity, warm mildly, increase stirring; log deviation.
- If paste is non-uniform: reduce addition rate; pre-wet support with small solvent fraction.
- If calcination causes clumping: reduce ramp rate; use thinner bed depth.
- If activation shows exotherm (H₂): reduce H₂ fraction; verify purge and ramp.

## 11. Shift handoff checklist (mandatory)
At any hold point A–E, outgoing operator must:
- [ ] Update batch record with last completed step and times.
- [ ] Label intermediate with Batch ID + state + date/time.
- [ ] Note storage location (oven #, desiccator #, shelf).
- [ ] Communicate next required action + remaining duration + any anomalies.

Incoming operator must:
- [ ] Verify labels match batch record.
- [ ] Verify equipment status (furnace program, gas flows off/on as needed).
- [ ] Confirm intermediate condition (dry? cooled? sealed?).

## 12. Revision history
| Version | Date | Change summary | Author |
|---:|---|---|---|
| 0.1 | 2026‑04‑30 | Initial SOP draft generated from notebook narrative; parameters to be finalized from extracted tables. | Autonomous agent |
