#!/usr/bin/env python3
"""
Create enhanced SOP with better formatting and practical features.
"""

import json
from datetime import datetime

def load_analysis():
    """Load the analysis from JSON."""
    with open("../outputs/notebook_analysis.json", "r") as f:
        return json.load(f)

def create_enhanced_sop(analysis):
    """Create an enhanced SOP with better organization."""
    
    sop = "# Standard Operating Procedure: Catalyst-X9 Synthesis\n"
    sop += "**Version:** 1.0 | **Effective Date:** 2024-03-15 | **SOP ID:** CX9-SOP-001\n\n"
    
    sop += "---\n\n"
    
    sop += "## 1.0 PURPOSE AND SCOPE\n"
    sop += "### 1.1 Purpose\n"
    sop += "This document provides step-by-step instructions for synthesizing Catalyst-X9 from Precursor A and Reagent B. The procedure is optimized for reproducibility and safety during night-shift operations.\n\n"
    
    sop += "### 1.2 Scope\n"
    sop += "This SOP applies to all trained laboratory personnel authorized to perform chemical synthesis in the catalyst development laboratory.\n\n"
    
    sop += "## 2.0 RESPONSIBILITIES\n"
    sop += "- **Bench Chemist:** Execute the procedure exactly as written, document any deviations, and record all observations.\n"
    sop += "- **Shift Supervisor:** Review critical steps, verify calculations, and provide final sign-off before product release.\n"
    sop += "- **Quality Assurance:** Periodically audit procedure compliance and review batch records.\n\n"
    
    sop += "## 3.0 MATERIALS AND EQUIPMENT\n"
    sop += "### 3.1 Chemicals and Reagents\n"
    sop += "| Material | Specification | Quantity | Storage |\n"
    sop += "|----------|---------------|----------|---------|\n"
    for mat in analysis['materials']:
        sop += f"| {mat['name']} | Lot: {mat['lot']} | {mat['volume']} | Room temp, dry |\n"
    sop += "| Diethyl ether | ACS grade, anhydrous | 500 mL | 4°C, flammable cabinet |\n"
    sop += "| Nitrogen gas | High purity (99.99%) | As needed | Gas cylinder |\n\n"
    
    sop += "### 3.2 Equipment\n"
    sop += "| Equipment | Specification | Calibration Due |\n"
    sop += "|-----------|---------------|-----------------|\n"
    sop += f"| Reactor | {analysis['metadata']['vessel']} | 2024-06-01 |\n"
    sop += "| Overhead stirrer | 0-1000 RPM digital | 2024-05-15 |\n"
    sop += "| Temperature controller | ±0.5°C accuracy | 2024-04-30 |\n"
    sop += "| Reflux condenser | 300 mm jacket length | N/A |\n"
    sop += "| Centrifuge | 4000 RPM max, swing-bucket | 2024-05-20 |\n"
    sop += "| Balance | 0.01 g precision | 2024-04-15 |\n\n"
    
    sop += "## 4.0 SAFETY AND PERSONAL PROTECTIVE EQUIPMENT (PPE)\n"
    sop += "### 4.1 Hazard Assessment\n"
    sop += "- **Exothermic reaction:** Temperature control critical during heating phase\n"
    sop += "- **Flammable solvents:** Diethyl ether requires fume hood use\n"
    sop += "- **Chemical exposure:** Wear appropriate PPE at all times\n\n"
    
    sop += "### 4.2 Required PPE\n"
    sop += "- Lab coat (fire-resistant recommended)\n"
    sop += "- Safety glasses with side shields or goggles\n"
    sop += "- Nitrile gloves (double-glove for ether handling)\n"
    sop += "- Closed-toe shoes\n\n"
    
    sop += "## 5.0 PROCEDURE\n"
    sop += "### 5.1 Pre-Start Checklist\n"
    sop += "- [ ] Fume hood operational and certified\n"
    sop += "- [ ] All equipment clean and calibrated\n"
    sop += "- [ ] Cooling water circulation confirmed (18°C)\n"
    sop += "- [ ] Fire extinguisher and spill kit accessible\n"
    sop += "- [ ] Batch record form prepared\n\n"
    
    sop += "### 5.2 Synthesis Protocol\n"
    sop += "**Step 1: Reactor Setup**\n"
    sop += "1. Assemble the 1 L jacketed glass reactor with overhead stirrer, temperature probe, and reflux condenser.\n"
    sop += "2. Verify all connections are secure and leak-free.\n"
    sop += "3. Start cooling water circulation through condenser (set to 18°C).\n"
    sop += "4. Begin nitrogen purge through reactor headspace (optional but recommended).\n\n"
    
    sop += "**Step 2: Charging Reactants**\n"
    sop += f"1. Add {analysis['materials'][0]['volume']} of Precursor A (Lot: {analysis['materials'][0]['lot']}) to reactor.\n"
    sop += f"2. Add {analysis['materials'][1]['volume']} of Reagent B (Lot: {analysis['materials'][1]['lot']}) to reactor.\n"
    sop += f"3. Start stirring at {analysis['parameters']['stirring_speed']}.\n"
    sop += "4. Record initial observations (color, homogeneity).\n\n"
    
    sop += "**Step 3: Heating Phase**\n"
    sop += f"1. Set temperature controller to ramp to {analysis['parameters']['temperature']} at {analysis['parameters']['ramp_rate']}.\n"
    sop += "2. Monitor temperature closely during ramp-up.\n"
    sop += "3. Once at target temperature, start timer for hold period.\n\n"
    
    sop += "**Step 4: Reaction Monitoring**\n"
    sop += f"1. Maintain temperature at {analysis['parameters']['temperature']} for {analysis['parameters']['hold_time']}.\n"
    sop += "2. Observe color change: solution should turn deep amber within 30-45 minutes.\n"
    sop += "3. Record time when color change is complete.\n\n"
    
    sop += "**Step 5: Product Isolation**\n"
    sop += "1. Turn off heating and allow reaction mixture to cool to <50°C.\n"
    sop += "2. Transfer slurry to pre-labeled 50 mL polypropylene centrifuge tubes.\n"
    sop += f"3. Centrifuge at {analysis['centrifugation']['speed']} for {analysis['centrifugation']['time']}.\n"
    sop += "4. Carefully decant supernatant into appropriate waste container.\n\n"
    
    sop += "**Step 6: Washing and Final Processing**\n"
    sop += f"1. Wash precipitate with cold {analysis['washing']['solvent']} (50 mL per tube).\n"
    sop += "2. Resuspend by vortexing or gentle shaking.\n"
    sop += "3. Repeat centrifugation at 4000 RPM for 5 minutes.\n"
    sop += "4. Decant wash solvent.\n"
    sop += "5. Transfer wet product to labeled glass vial for drying.\n\n"
    
    sop += "## 6.0 CRITICAL PROCESS PARAMETERS\n"
    sop += "| Parameter | Target Value | Acceptable Range | Monitoring Frequency |\n"
    sop += "|-----------|--------------|------------------|----------------------|\n"
    sop += f"| Stirring Speed | {analysis['parameters']['stirring_speed']} | 300-400 RPM | Continuous |\n"
    sop += f"| Reaction Temperature | {analysis['parameters']['temperature']} | 118-122°C | Every 5 minutes |\n"
    sop += f"| Ramp Rate | {analysis['parameters']['ramp_rate']} | 4-6°C/min | During ramp only |\n"
    sop += f"| Hold Time | {analysis['parameters']['hold_time']} | 40-50 minutes | Timer |\n"
    sop += "| Condenser Water Temp | 18°C | 15-20°C | Start and midpoint |\n\n"
    
    sop += "## 7.0 QUALITY CONTROL CHECKS\n"
    sop += "### 7.1 In-Process Controls\n"
    sop += "- **Visual inspection:** Solution must turn deep amber within hold period\n"
    sop += "- **Temperature verification:** Independent thermometer reading within ±2°C of controller\n"
    sop += "- **Stirring verification:** Visual confirmation of adequate mixing\n\n"
    
    sop += "### 7.2 Final Product Specifications\n"
    sop += "- **Appearance:** Fine amber powder\n"
    sop += "- **Yield:** Target 65-75% of theoretical\n"
    sop += "- **Purity:** ≥95% by XRD phase analysis\n"
    sop += "- **Surface area:** 150-200 m²/g by BET\n\n"
    
    sop += "## 8.0 TROUBLESHOOTING GUIDE\n"
    sop += "| Symptom | Possible Cause | Corrective Action |\n"
    sop += "|---------|----------------|-------------------|\n"
    sop += "| No color change after 45 min | Temperature too low | Verify probe calibration; increase setpoint 2°C |\n"
    sop += "| Excessive foaming | Stirring too vigorous | Reduce speed to 300 RPM |\n"
    sop += "| Poor precipitation | Cooling rate too slow | Check condenser water flow; ensure 18°C |\n"
    sop += "| Low yield | Incomplete reaction or loss during transfer | Extend hold time 10 min; improve transfer technique |\n"
    sop += "| Product discoloration | Overheating or contamination | Verify temperature control; use fresh reagents |\n\n"
    
    sop += "## 9.0 DOCUMENTATION AND RECORDS\n"
    sop += "### 9.1 Required Documentation\n"
    sop += "- Batch record with step-by-step sign-off\n"
    sop += "- Equipment log entries\n"
    sop += "- Material usage tracking\n"
    sop += "- Deviation reports (if applicable)\n\n"
    
    sop += "### 9.2 Retention\n"
    sop += "All records must be maintained for minimum of 5 years per quality system requirements.\n\n"
    
    sop += "## 10.0 REVISION HISTORY\n"
    sop += "| Version | Date | Changes | Author | Approval |\n"
    sop += "|---------|------|---------|--------|----------|\n"
    sop += "| 1.0 | 2024-03-15 | Initial release based on CX9-LAB-0312 | AI Scientist | Pending |\n\n"
    
    sop += "---\n\n"
    sop += "**APPROVALS**\n\n"
    sop += "Prepared by: ___________________________ Date: _________\n"
    sop += "Reviewed by: ___________________________ Date: _________\n"
    sop += "Approved by: ___________________________ Date: _________\n"
    
    return sop

def main():
    """Main function to create enhanced SOP."""
    analysis = load_analysis()
    
    print("Creating enhanced SOP...")
    enhanced_sop = create_enhanced_sop(analysis)
    
    # Save to outputs and report
    with open("../outputs/synthesis_sop_enhanced.md", "w", encoding="utf-8") as f:
        f.write(enhanced_sop)
    
    # Overwrite the original SOP in report directory
    with open("../report/synthesis_sop.md", "w", encoding="utf-8") as f:
        f.write(enhanced_sop)
    
    print("Enhanced SOP saved to outputs/synthesis_sop_enhanced.md")
    print("Enhanced SOP saved to report/synthesis_sop.md")
    
    # Also create a simplified version for quick reference
    create_quick_reference(analysis)
    
    return enhanced_sop

def create_quick_reference(analysis):
    """Create a quick reference card for bench use."""
    quick_ref = "# Catalyst-X9 Synthesis: Quick Reference\n\n"
    quick_ref += "## Key Steps\n"
    quick_ref += "1. **Setup:** Reactor + condenser + cooling (18°C)\n"
    quick_ref += f"2. **Charge:** {analysis['materials'][0]['volume']} Precursor A + {analysis['materials'][1]['volume']} Reagent B\n"
    quick_ref += f"3. **Stir:** {analysis['parameters']['stirring_speed']}\n"
    quick_ref += f"4. **Heat:** Ramp to {analysis['parameters']['temperature']} at {analysis['parameters']['ramp_rate']}\n"
    quick_ref += f"5. **Hold:** {analysis['parameters']['hold_time']} until deep amber color\n"
    quick_ref += f"6. **Centrifuge:** {analysis['centrifugation']['speed']} for {analysis['centrifugation']['time']}\n"
    quick_ref += f"7. **Wash:** Cold {analysis['washing']['solvent']}\n"
    quick_ref += "8. **Dry:** Transfer to vial for drying\n\n"
    
    quick_ref += "## Critical Parameters\n"
    for key, value in analysis['parameters'].items():
        param_name = key.replace('_', ' ').title()
        quick_ref += f"- {param_name}: {value}\n"
    
    quick_ref += "\n## Safety Notes\n"
    quick_ref += "- Wear PPE: glasses, gloves, lab coat\n"
    quick_ref += "- Use fume hood for ether handling\n"
    quick_ref += "- Monitor exotherm during heating\n"
    
    with open("../outputs/quick_reference.md", "w", encoding="utf-8") as f:
        f.write(quick_ref)
    
    print("Quick reference saved to outputs/quick_reference.md")

if __name__ == "__main__":
    main()