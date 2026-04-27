# Pilot-Scale SOP: Nanoparticle Synthesis (System TBD from Notes)

**Document ID:** NP-SOP-001  \
**Version:** 0.1 (auto-generated from lab_scratch.txt; requires technical review prior to use)  \
**Target batch size (pilot):** 5.0 L reaction scale (nominal)  \
**Prepared by:** Automated conversion script (`code/build_sop.py`)  \
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

### System-specific recipe
The nanoparticle system could not be confidently inferred from the notes. During technical review, specify:
- precursor identity and target concentration
- reducing agent/base identity and addition profile
- stabilizer identity and target concentration
- temperature and hold times
- purification route


### Trace lines from raw notes (parameter candidates)
The following lines were automatically selected because they contain likely reagent keywords and quantitative units; use them during SOP review:

- L2: Heat oil bath to ~110C add precursor A dropwise (see bottle)

## 8. Process overview (high level)
1. Prepare precursor solution.
2. Heat/condition reactor to target temperature.
3. Controlled addition/injection of reducing agent or base (nucleation step).
4. Growth/aging hold.
5. Quench/cool.
6. Purification (wash/centrifuge/dialysis/TFF).
7. Final formulation and storage.

## 9. Critical process parameters (CPPs) and CQAs
**CPPs:** addition rate, mixing intensity (tip speed / power per volume), temperature profile, pH, ionic strength, hold times.  \
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
1. Define precursor, stabilizer, and triggering step (reduction/base/solvent switch).
2. Execute nucleation with controlled addition and strong mixing.
3. Age to completion.
4. Purify and formulate.


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

> NanoCu synthesis — bench notes
> Heat oil bath to ~110C add precursor A dropwise (see bottle)
> Then surfactant — stirred overnight
> ?? quench / workup not fully written here, check photo from phone
> Color should turn from blue-green to brown

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
