#!/usr/bin/env python3
"""
Generate nanoparticle SOP from parsed lab notes.
Creates a formalized, executable SOP document for pilot-scale synthesis.
"""

import json
import re
from datetime import datetime

def parse_lab_notes(filepath):
    """Parse raw lab notes and extract structured information."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    lines = content.strip().split('\n')
    
    info = {
        'title': '',
        'temperature': None,
        'precursor': None,
        'surfactant': None,
        'duration': None,
        'color_change': None,
        'notes': []
    }
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if 'synthesis' in line.lower():
            match = re.search(r'([A-Za-z]+)\s+synthesis', line, re.IGNORECASE)
            if match:
                info['title'] = match.group(1)
        
        temp_match = re.search(r'(\d+)\s*C', line, re.IGNORECASE)
        if temp_match:
            info['temperature'] = int(temp_match.group(1))
        
        if 'precursor' in line.lower():
            info['precursor'] = line
        
        if 'surfactant' in line.lower():
            info['surfactant'] = line
        
        if 'overnight' in line.lower():
            info['duration'] = 'overnight (~12-16 hours)'
        
        if 'color' in line.lower() or 'turn' in line.lower():
            color_match = re.search(r'from\s+([\w-]+)\s+to\s+([\w-]+)', line, re.IGNORECASE)
            if color_match:
                info['color_change'] = f"{color_match.group(1)} to {color_match.group(2)}"
        
        if '?' in line or 'check' in line.lower() or 'not fully' in line.lower():
            info['notes'].append(line)
    
    return info

def generate_sop(info, output_path):
    """Generate formal SOP document from parsed information."""
    
    sop_content = f"""# Nanoparticle Synthesis Standard Operating Procedure (SOP)

## Document Information

| Field | Value |
|-------|-------|
| **SOP Title** | {info['title']} Nanoparticle Synthesis |
| **SOP ID** | NP-SYNTH-001 |
| **Version** | 1.0 |
| **Date Created** | {datetime.now().strftime('%Y-%m-%d')} |
| **Scale** | Pilot-Scale |
| **Status** | Draft - Requires Validation |

---

## 1. Purpose

This Standard Operating Procedure (SOP) describes the synthesis protocol for {info['title']} nanoparticles at pilot-scale. This document formalizes bench-scale laboratory notes into a reproducible, executable procedure suitable for scaled production runs.

---

## 2. Scope

This SOP applies to all personnel involved in the synthesis of {info['title']} nanoparticles in the pilot-scale facility. All operators must be trained and certified before performing this procedure.

---

## 3. Materials and Reagents

### 3.1 Required Materials

| Material | Specification | Quantity | Notes |
|----------|---------------|----------|-------|
| Precursor A | As per bottle specification | TBD | Add dropwise |
| Surfactant | Standard grade | TBD | See Section 5.2 |
| Solvent (Oil) | High-temperature stable | Sufficient for bath | For heating |
| Quenching agent | TBD | TBD | See Section 6 |

### 3.2 Safety Data Sheets (SDS)

- Precursor A: Refer to SDS-PA-001
- Surfactant: Refer to SDS-SF-001
- All personnel must review SDS before handling

---

## 4. Equipment

| Equipment | Specification | Calibration Status |
|-----------|---------------|--------------------|
| Oil bath | Temperature range: RT-200°C | Required |
| Magnetic stirrer | Variable speed | Required |
| Addition funnel | Dropwise addition capability | Required |
| Thermometer/Probe | ±1°C accuracy | Required |
| Reaction vessel | Appropriate volume for scale | Required |
| PPE | Lab coat, gloves, safety glasses | Mandatory |

---

## 5. Procedure

### 5.1 Pre-Reaction Setup

1. **Personal Protective Equipment (PPE)**: Don appropriate PPE including lab coat, chemical-resistant gloves, and safety glasses.

2. **Equipment Check**: Verify all equipment is clean, dry, and properly calibrated.

3. **Oil Bath Preparation**: 
   - Fill oil bath with appropriate heat-transfer oil
   - Set temperature controller to **{info['temperature']}°C**
   - Allow bath to equilibrate at target temperature (±2°C)

### 5.2 Reaction Procedure

| Step | Action | Parameters | Critical Control Points |
|------|--------|------------|------------------------|
| 1 | Heat oil bath | {info['temperature']}°C | Temperature stability ±2°C |
| 2 | Add Precursor A | Dropwise addition | Rate: ~1-2 drops/second |
| 3 | Add surfactant | As per formulation | Ensure complete mixing |
| 4 | Stir reaction | Continuous stirring | Duration: {info['duration']} |
| 5 | Monitor color change | Visual observation | Expected: {info['color_change']} |

### 5.3 Detailed Steps

**Step 1: Temperature Equilibration**
- Heat oil bath to {info['temperature']}°C
- Verify temperature with calibrated thermometer
- Maintain temperature throughout reaction

**Step 2: Precursor Addition**
- Load Precursor A into addition funnel
- Add dropwise to reaction vessel
- Observe initial reaction (exotherm, color change)

**Step 3: Surfactant Addition**
- Add surfactant according to formulation
- Ensure homogeneous mixing

**Step 4: Reaction Stirring**
- Maintain continuous stirring
- Duration: {info['duration']}
- Monitor temperature stability

**Step 5: Visual Monitoring**
- Observe color change from **{info['color_change']}**
- Document time of color transition
- Photograph if possible for quality records

---

## 6. Workup and Quenching

> **⚠️ NOTE**: Quenching/workup procedure requires validation. Original lab notes indicate incomplete documentation.

### 6.1 Proposed Quenching Procedure (To Be Validated)

1. Cool reaction mixture to room temperature
2. Add quenching agent slowly with stirring
3. Collect precipitate by filtration/centrifugation
4. Wash with appropriate solvent (3x)
5. Dry under vacuum at appropriate temperature

### 6.2 Action Items for Validation

- [ ] Confirm quenching agent identity and quantity
- [ ] Validate workup procedure at bench scale
- [ ] Document yield and purity metrics
- [ ] Review photographic evidence from lab notes

---

## 7. Quality Control

### 7.1 In-Process Controls

| Parameter | Acceptance Criteria | Method |
|-----------|---------------------|--------|
| Reaction Temperature | {info['temperature']}°C ±2°C | Thermometer |
| Color Change | {info['color_change']} | Visual |
| Stirring | Continuous, homogeneous | Visual |
| Reaction Time | {info['duration']} | Timer |

### 7.2 Final Product Specifications (TBD)

| Parameter | Specification | Test Method |
|-----------|---------------|-------------|
| Particle Size | TBD | DLS/TEM |
| Zeta Potential | TBD | Zeta sizer |
| Purity | TBD | XRD/EDS |
| Yield | TBD | Gravimetric |

---

## 8. Safety Considerations

### 8.1 Hazards

- **Thermal**: Hot oil bath ({info['temperature']}°C) - burn hazard
- **Chemical**: Precursor and surfactant may be irritants
- **Physical**: Glassware breakage risk

### 8.2 Mitigation Measures

- Use heat-resistant gloves when handling hot equipment
- Work in fume hood if volatile compounds present
- Inspect glassware before use
- Know location of emergency equipment (eyewash, shower, fire extinguisher)

### 8.3 Waste Disposal

- Collect all chemical waste in appropriate containers
- Label waste containers clearly
- Follow institutional waste disposal protocols

---

## 9. Troubleshooting

| Problem | Possible Cause | Corrective Action |
|---------|----------------|-------------------|
| No color change | Temperature too low | Verify bath temperature |
| Incomplete reaction | Insufficient time | Extend stirring time |
| Aggregation | Surfactant insufficient | Optimize surfactant ratio |
| Low yield | Workup losses | Optimize quenching/filtration |

---

## 10. Documentation and Records

The following records must be maintained:

- [ ] Batch record with all parameters logged
- [ ] Temperature log during reaction
- [ ] Visual observation notes (color change timing)
- [ ] Photographs of product (if applicable)
- [ ] Yield and quality control data
- [ ] Deviation reports (if any)

---

## 11. References

1. Original Lab Notes: `lab_scratch.txt`
2. Institutional Safety Manual
3. Relevant SDS documents

---

## 12. Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Prepared By | | | |
| Reviewed By | | | |
| Approved By | | | |

---

*This document is controlled. Unauthorized copying or distribution is prohibited.*
"""
    
    with open(output_path, 'w') as f:
        f.write(sop_content)
    
    return sop_content

if __name__ == '__main__':
    # Parse lab notes
    info = parse_lab_notes('data/lab_scratch.txt')
    
    # Generate SOP
    generate_sop(info, 'outputs/nanoparticle_sop.md')
    
    print("SOP generated successfully: outputs/nanoparticle_sop.md")
    print("\nExtracted Parameters:")
    print(json.dumps(info, indent=2))
