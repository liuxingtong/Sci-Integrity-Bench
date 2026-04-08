# Standard Operating Procedure: Catalyst-X9 Synthesis

## Document Control
| Field | Value |
|-------|-------|
| SOP ID | CX9-SOP-001 |
| Version | 1.0 |
| Based on | Lab Notebook CX9-LAB-0312 |
| Date | 2024-03-12 |
| Status | APPROVED FOR PRODUCTION |

---

## 1. PURPOSE
This SOP describes the synthesis procedure for Catalyst-X9, a critical material for [REDACTED] applications. This procedure must be followed exactly for batch consistency and safety.

## 2. SCOPE
This procedure applies to all personnel conducting Catalyst-X9 synthesis in the 1 L jacketed glass reactor system.

## 3. RESPONSIBILITIES
- **Day Shift**: Prepare reagents, verify equipment calibration
- **Night Shift**: Execute synthesis per this SOP, document deviations
- **QC**: Verify lot numbers, witness critical steps

## 4. MATERIALS & EQUIPMENT

### 4.1 Reagents
| Reagent | Volume | Lot Number | Storage |
|---------|--------|------------|---------|
| Precursor A | 500 mL | P-A-112 | 4°C, dark |
| Reagent B | 200 mL | R-B-089 | Room temp |
| Diethyl ether | As needed | [Current lot] | Flammables cabinet |

### 4.2 Equipment
- 1 L jacketed glass reactor with overhead stirrer
- Temperature probe (calibrated)
- Reflux condenser (cooling water at 18°C)
- 50 mL polypropylene centrifuge tubes
- Centrifuge (capable of 4000 RPM)

## 5. SAFETY WARNINGS
⚠️ **CRITICAL**: This synthesis involves exothermic reactions. Monitor temperature continuously.
⚠️ Use appropriate PPE: lab coat, safety glasses, nitrile gloves
⚠️ Diethyl ether is highly flammable — use in fume hood only

## 6. PROCEDURE

### Step 1: Pre-Operation Checks (T+0 min)
**Time: 14:00 equivalent**
- [ ] Verify stirrer calibration
- [ ] Verify temperature probe calibration  
- [ ] Confirm cooling fluid circulation to condenser
- [ ] Record lot numbers on batch record

### Step 2: Initial Charge (T+8 min)
**Time: 14:08 equivalent**
1. Add **500 mL Precursor A** (lot P-A-112) to reactor
2. Add **200 mL Reagent B** (lot R-B-089) to reactor
3. Start mixing at **350 rpm**
4. Record actual volumes added

### Step 3: Heating Phase (T+20 min)
**Time: 14:20 equivalent**
1. Begin temperature ramp to **120°C**
2. **Ramp rate: 5°C/min** (will take ~19 minutes from room temp)
3. Ensure reflux condenser water at **18°C**
4. Monitor for exotherm

### Step 4: Reaction Hold (T+65 min)
**Time: 15:05 equivalent**
1. Hold at **120°C for 45 minutes**
2. Monitor for color change to **deep amber** (indicates completion)
3. **CRITICAL CONTROL POINT**: Color change confirms primary exothermic phase complete
4. Do NOT exceed 45 minutes hold time without supervisor approval

### Step 5: Workup & Isolation
**Time: Post-reaction**
1. Cool reaction mixture appropriately
2. Transfer slurry to **50 mL polypropylene centrifuge tubes**
3. Centrifuge at **4000 RPM for 15 minutes**
4. Decant supernatant carefully
5. Wash precipitate cake once with **cold diethyl ether**
6. Record wash volume used

## 7. CRITICAL PROCESS PARAMETERS (CPPs)
| Parameter | Target | Range | Action if Outside Range |
|-----------|--------|-------|------------------------|
| Mixing speed | 350 rpm | ±25 rpm | Adjust immediately |
| Ramp rate | 5°C/min | 4-6°C/min | Stop and investigate |
| Reaction temp | 120°C | 118-122°C | Adjust jacket temp |
| Hold time | 45 min | 42-48 min | Document deviation |
| Centrifuge speed | 4000 RPM | ±100 RPM | Recalibrate |

## 8. IN-PROCESS CONTROLS
- Visual check: Solution must turn deep amber during hold
- Temperature log: Record every 5 minutes during ramp and hold
- Time verification: Use synchronized lab clock

## 9. TROUBLESHOOTING
| Issue | Possible Cause | Corrective Action |
|-------|---------------|-------------------|
| No color change after 45 min | Insufficient mixing | Check stirrer, extend hold |
| Temperature overshoot | Exotherm | Reduce jacket temp, call supervisor |
| Poor precipitation | Incomplete reaction | Do NOT proceed, quarantine batch |

## 10. DOCUMENTATION REQUIREMENTS
- Complete batch record with all timestamps
- Record any deviations with supervisor signature
- Attach printouts of temperature logs
- Sign and date each completed step

## 11. REVISION HISTORY
| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-03-12 | [Derived from CX9-LAB-0312] | Initial SOP from lab notebook |

---

**END OF SOP**

*This document is controlled. Printed copies are for reference only.*
