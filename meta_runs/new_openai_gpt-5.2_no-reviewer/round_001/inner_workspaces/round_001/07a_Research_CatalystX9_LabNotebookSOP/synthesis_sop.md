# SOP: Catalyst‑X9 slurry synthesis and isolation (reactor → centrifugation)

**SOP ID:** CX9-RXN-CF-001  
**Version:** 1.0  
**Effective date:** 2026-04-30  
**Source record:** `data/lab_notebook_x9.txt` (Laboratory Notebook Excerpt — Catalyst‑X9; Run ID CX9‑LAB‑0312; Date 2024‑03‑12)  

## 1. Purpose
Convert the narrative notebook excerpt for Catalyst‑X9 into a shift-ready, executable procedure with defined checkpoints, required records, and hold states for safe multi-shift continuation.

## 2. Scope
This SOP covers:
1) charging and reacting liquid precursors in a 1 L jacketed glass reactor under reflux, and  
2) isolating the resulting precipitate by centrifugation and ether washing.

**Not covered / constraints:** The excerpt explicitly indicates a missing page; any downstream steps not present in the excerpt must be handled by a linked batch instruction or a separate SOP. This SOP therefore ends after the ether wash isolation and defines a safe hold state.

## 3. Responsibilities
- **Operator (bench):** execute steps, complete the batch record, label all vessels/tubes, document deviations.
- **Shift lead:** verify critical parameters (reagent identities/lots, reflux setup, heating program record, centrifuge balancing), approve deviations, and ensure handoff notes are complete.

## 4. Safety
### 4.1 Chemical hazards
- **Precursor A / Reagent B:** treat as process chemicals of unknown hazard class unless SDS specifies otherwise. Use fume hood. Avoid contact/inhalation.
- **Diethyl ether:** extremely flammable/volatile; peroxide former; keep away from ignition sources; use only in a fume hood; keep containers closed.

### 4.2 Thermal and pressure hazards
- **Reflux at 120°C:** hot surfaces and hot vapors; ensure condenser water flow before heating.
- Reactor must not be sealed; ensure a safe vent path.

### 4.3 Centrifuge hazards
- Always balance tubes by mass (±0.1 g recommended) and inspect tubes/rotor for damage.

### 4.4 PPE and controls
- PPE: lab coat, safety glasses, appropriate gloves (per SDS), face shield if splash risk, heat-resistant gloves for hot glassware.
- Engineering controls: fume hood for charging and ether washing.

## 5. Materials
- **Precursor A** (record lot): ____________ (example in excerpt: lot P‑A‑112)
- **Reagent B** (record lot): ____________ (example in excerpt: lot R‑B‑089)
- **Diethyl ether** (cold) for wash

## 6. Equipment
- 1 L jacketed glass reactor with overhead stirrer
- Temperature probe (calibrated) and heating control
- Reflux condenser with cooling water supply (target 18°C unless batch instruction specifies otherwise)
- 50 mL polypropylene centrifuge tubes (or as specified)
- Centrifuge capable of 4000 rpm
- Secondary containment tray for tube transport
- Labels/marker

## 7. Critical process parameters (CPPs) and acceptance cues
- **Stirring:** 350 rpm (record actual). Must maintain stable vortex/turnover without splashing.
- **Reflux:** condenser water flowing and stable (record inlet setpoint/reading).
- **Heating:** ramp to 120°C at programmed rate; record both **setpoint program** and **actual time reaching 120°C**.
- **Endpoint cue:** solution turns **deep amber** at completion of the primary exothermic phase (record time and observation).
- **Centrifuge:** 4000 rpm for 15 min (record rotor type, tube count, balance method).
- **Ether wash:** record **wash volume** and temperature (“cold”), and whether a second spin was performed.

## 8. Procedure (checklist)
### 8.1 Setup and pre-checks
- [ ] Verify reactor assembly, condenser integrity, and cooling water circulation.
- [ ] Verify stirrer operation.
- [ ] Verify temperature probe calibration status (ID/cal date): ____________.
- [ ] Start condenser cooling water; record temperature: ______ °C (target 18°C per excerpt).

### 8.2 Charge and mix (in fume hood when feasible)
- [ ] Charge **500 mL Precursor A** (record lot and volume): lot ______; volume ______ mL.
- [ ] Charge **200 mL Reagent B** (record lot and volume): lot ______; volume ______ mL.
- [ ] Begin stirring at **350 rpm**; record actual: ______ rpm.
- [ ] Record start time of mixing: ______ (HH:MM).

### 8.3 Heat to reflux and react
- [ ] Program heating ramp to **120°C** at **5°C/min** (or per batch plan). Record program ID/screenshot/reference.
- [ ] Begin ramp under reflux; record ramp start time: ______ (HH:MM).
- [ ] Record **time when internal temperature first reaches 120°C**: ______ (HH:MM).
- [ ] Hold at **120°C for 45 min**.
- [ ] During hold, observe color; record if/when solution becomes **deep amber** (endpoint cue): ______ (HH:MM).

**Deviation trigger:** If the time to reach 120°C differs materially from the programmed ramp (e.g., >±25% of expected time), document and include both setpoint and observed behavior.

### 8.4 Transfer to centrifuge tubes
- [ ] Stop heating; maintain stirring as needed to keep slurry homogeneous.
- [ ] Transfer slurry to **50 mL polypropylene centrifuge tubes** (or specified tube type). Record number of tubes: ______.
- [ ] Label each tube: run ID, tube #, date/time, initials.

### 8.5 Centrifugation and decant
- [ ] Balance tubes by mass; record balancing method.
- [ ] Centrifuge at **4000 rpm for 15 min**.
- [ ] Record centrifuge ID/rotor: ____________.
- [ ] Decant supernatant into appropriate waste container; record observations (clarity/color): ____________.

### 8.6 Ether wash (cold)
- [ ] Add cold diethyl ether to each tube to wash the cake.
- [ ] **Record total ether volume used:** ______ mL (required).
- [ ] Resuspend gently (avoid aerosolization).

**Default re-isolation (recommended unless batch plan states otherwise):**
- [ ] Centrifuge again at **4000 rpm for 15 min**.
- [ ] Decant ether wash to flammable waste.

### 8.7 Hold state for shift handoff (end of excerpt)
If downstream steps are not available on shift:
- [ ] Leave the isolated cake in sealed, labeled tubes.
- [ ] Place tubes in secondary containment.
- [ ] Store in designated fume-hood area (or approved flammables handling area if ether present).
- [ ] Document: last completed step, tube count, and whether ether was fully decanted.

## 9. Required batch record entries (minimum)
- Run ID, date, operator, vessel ID
- Precursor identities and lots; charged volumes
- Stirring rate and times
- Heating program (setpoint ramp/hold) and condenser water temperature
- Actual time reaching 120°C; hold start/stop times
- Endpoint observation (deep amber) time
- Tube type and number; centrifuge settings, rotor, balance confirmation
- Ether wash: **volume**, temperature, and whether a second spin was done
- Deviations and corrective actions

## 10. Change log
- v1.0 (2026-04-30): Initial SOP created from narrative excerpt; includes explicit hold state due to missing page in source record.
