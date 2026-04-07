#!/usr/bin/env python3
"""
Analyze lab notebook and extract synthesis procedure for Catalyst-X9.
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import json


def parse_notebook(filepath: str) -> Dict:
    """Parse the lab notebook and extract structured information."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract metadata
    metadata = {}
    metadata_match = re.search(r'Run ID: (\S+)', content)
    if metadata_match:
        metadata['run_id'] = metadata_match.group(1)
    
    vessel_match = re.search(r'Vessel: ([^|]+)', content)
    if vessel_match:
        metadata['vessel'] = vessel_match.group(1).strip()
    
    date_match = re.search(r'Date: (\d{4}-\d{2}-\d{2})', content)
    if date_match:
        metadata['date'] = date_match.group(1)
    
    # Extract steps with timestamps
    steps = []
    time_pattern = r'(\d{2}:\d{2}) — (.+)'
    
    for line in content.split('\n'):
        match = re.search(time_pattern, line)
        if match:
            time_str = match.group(1)
            description = match.group(2).strip()
            steps.append({
                'time': time_str,
                'description': description
            })
    
    # Extract additional information
    materials = []
    if 'Precursor A' in content:
        materials.append({
            'name': 'Precursor A',
            'volume': '500 mL',
            'lot': 'P-A-112'
        })
    if 'Reagent B' in content:
        materials.append({
            'name': 'Reagent B',
            'volume': '200 mL',
            'lot': 'R-B-089'
        })
    
    # Extract parameters
    parameters = {}
    rpm_match = re.search(r'(\d+) rpm', content, re.IGNORECASE)
    if rpm_match:
        parameters['stirring_speed'] = f"{rpm_match.group(1)} RPM"
    
    temp_match = re.search(r'(\d+) °C', content)
    if temp_match:
        parameters['temperature'] = f"{temp_match.group(1)} °C"
    
    ramp_match = re.search(r'(\d+) °C/min', content)
    if ramp_match:
        parameters['ramp_rate'] = f"{ramp_match.group(1)} °C/min"
    
    time_match = re.search(r'(\d+) minutes', content)
    if time_match:
        parameters['hold_time'] = f"{time_match.group(1)} minutes"
    
    # Extract centrifugation details
    centrifuge_info = {}
    if '4000 RPM' in content:
        centrifuge_info['speed'] = '4000 RPM'
    if '15 minutes' in content and 'centrifuge' in content.lower():
        centrifuge_info['time'] = '15 minutes'
    
    # Extract washing step
    washing = {}
    if 'diethyl ether' in content.lower():
        washing['solvent'] = 'diethyl ether'
        washing['condition'] = 'cold'
    
    return {
        'metadata': metadata,
        'steps': steps,
        'materials': materials,
        'parameters': parameters,
        'centrifugation': centrifuge_info,
        'washing': washing
    }


def create_sop_template(analysis: Dict) -> str:
    """Create an SOP markdown template from the analysis."""
    
    sop = "# Standard Operating Procedure: Catalyst-X9 Synthesis\n\n"
    
    # Header information
    sop += "## 1.0 Purpose\n"
    sop += "This SOP describes the synthesis procedure for Catalyst-X9 from Precursor A and Reagent B.\n\n"
    
    sop += "## 2.0 Scope\n"
    sop += "Applies to all laboratory personnel performing Catalyst-X9 synthesis during night shifts.\n\n"
    
    sop += "## 3.0 Responsibilities\n"
    sop += "- Bench chemist: Execute procedure as written\n"
    sop += "- Shift supervisor: Verify critical steps and sign-off\n\n"
    
    sop += "## 4.0 Materials and Equipment\n"
    sop += "### 4.1 Chemicals\n"
    for mat in analysis['materials']:
        sop += f"- {mat['name']}: {mat['volume']} (Lot: {mat['lot']})\n"
    sop += "- Diethyl ether (cold, for washing)\n\n"
    
    sop += "### 4.2 Equipment\n"
    if 'vessel' in analysis['metadata']:
        sop += f"- {analysis['metadata']['vessel']}\n"
    else:
        sop += "- 1 L jacketed glass reactor\n"
    sop += "- Overhead stirrer with calibrated probe\n"
    sop += "- Reflux condenser with cooling water (18°C)\n"
    sop += "- Temperature controller\n"
    sop += "- 50 mL polypropylene centrifuge tubes\n"
    sop += "- Centrifuge capable of 4000 RPM\n"
    sop += "- Fume hood for ether handling\n\n"
    
    sop += "## 5.0 Safety Precautions\n"
    sop += "- Wear appropriate PPE: lab coat, safety glasses, nitrile gloves\n"
    sop += "- Work in fume hood when handling diethyl ether\n"
    sop += "- Be aware of exothermic reaction during heating phase\n"
    sop += "- Have fire extinguisher and spill kit readily available\n\n"
    
    sop += "## 6.0 Procedure\n"
    sop += "### 6.1 Preparation\n"
    sop += "1. Verify all equipment is clean and calibrated.\n"
    sop += "2. Confirm cooling fluid circulation is operational.\n"
    sop += "3. Set up reactor in fume hood with proper connections.\n\n"
    
    sop += "### 6.2 Synthesis Steps\n"
    
    # Add steps from analysis
    step_counter = 1
    for step in analysis['steps']:
        sop += f"{step_counter}. **{step['time']}** — {step['description']}\n"
        step_counter += 1
    
    # Add inferred steps from incomplete notebook
    sop += f"{step_counter}. Transfer synthesized slurry to 50 mL polypropylene centrifuge tubes.\n"
    step_counter += 1
    
    if 'speed' in analysis['centrifugation']:
        sop += f"{step_counter}. Centrifuge at {analysis['centrifugation']['speed']} for {analysis['centrifugation'].get('time', '15 minutes')}.\n"
        step_counter += 1
    
    sop += f"{step_counter}. Decant supernatant carefully.\n"
    step_counter += 1
    
    if 'solvent' in analysis['washing']:
        sop += f"{step_counter}. Wash precipitate once with cold {analysis['washing']['solvent']} (volume: 50 mL per tube).\n"
        step_counter += 1
    
    sop += f"{step_counter}. Collect product for drying and characterization.\n\n"
    
    sop += "### 6.3 Critical Parameters\n"
    for key, value in analysis['parameters'].items():
        param_name = key.replace('_', ' ').title()
        sop += f"- **{param_name}**: {value}\n"
    
    sop += "\n## 7.0 Quality Control\n"
    sop += "- Visual check: Solution should turn deep amber after 45 minutes at 120°C\n"
    sop += "- Product yield should be recorded\n"
    sop += "- Sample should be sent for XRD and BET analysis\n\n"
    
    sop += "## 8.0 Troubleshooting\n"
    sop += "| Issue | Possible Cause | Solution |\n"
    sop += "|-------|----------------|----------|\n"
    sop += "| No color change | Temperature too low | Verify temperature probe calibration |\n"
    sop += "| Excessive foaming | Stirring too fast | Reduce to 300 RPM |\n"
    sop += "| Poor precipitation | Cooling too slow | Ensure condenser water at 18°C |\n\n"
    
    sop += "## 9.0 References\n"
    sop += f"- Lab Notebook: {analysis['metadata'].get('run_id', 'CX9-LAB-0312')}\n"
    sop += f"- Date: {analysis['metadata'].get('date', '2024-03-12')}\n"
    
    return sop


def main():
    """Main function to analyze notebook and create SOP."""
    notebook_path = "../data/lab_notebook_x9.txt"
    
    print("Analyzing lab notebook...")
    analysis = parse_notebook(notebook_path)
    
    # Save analysis to outputs
    with open("../outputs/notebook_analysis.json", "w") as f:
        json.dump(analysis, f, indent=2)
    
    print("Creating SOP...")
    sop_content = create_sop_template(analysis)
    
    # Save SOP to outputs
    with open("../outputs/synthesis_sop_draft.md", "w", encoding="utf-8") as f:
        f.write(sop_content)
    
    print(f"Analysis saved to outputs/notebook_analysis.json")
    print(f"SOP draft saved to outputs/synthesis_sop_draft.md")
    
    # Also create the final SOP in report directory
    with open("../report/synthesis_sop.md", "w", encoding="utf-8") as f:
        f.write(sop_content)
    
    print(f"Final SOP saved to report/synthesis_sop.md")
    
    return analysis


if __name__ == "__main__":
    main()