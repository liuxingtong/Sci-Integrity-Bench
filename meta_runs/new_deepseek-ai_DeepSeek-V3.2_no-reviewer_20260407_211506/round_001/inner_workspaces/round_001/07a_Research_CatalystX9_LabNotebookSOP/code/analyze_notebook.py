#!/usr/bin/env python3
"""
Analyze lab notebook text and extract synthesis procedure for SOP creation.
"""

import re
from datetime import datetime
from pathlib import Path


def read_notebook(filepath):
    """Read and return notebook content."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def extract_synthesis_steps(text):
    """Extract synthesis steps from notebook text."""
    steps = []
    
    # Pattern for time-stamped steps
    time_pattern = r'(\d{2}:\d{2}) — (.+)'
    matches = re.findall(time_pattern, text)
    
    for time, action in matches:
        steps.append({
            'time': time,
            'action': action.strip(),
            'duration': None  # Will calculate later
        })
    
    # Also look for temperature information
    temp_pattern = r'(\d+) °C'
    temps = re.findall(temp_pattern, text)
    
    # Look for volumes and concentrations
    volume_pattern = r'(\d+) mL'
    volumes = re.findall(volume_pattern, text)
    
    # Look for RPM/stirring info
    rpm_pattern = r'(\d+) rpm'
    rpms = re.findall(rpm_pattern, text, re.IGNORECASE)
    
    return {
        'steps': steps,
        'temperatures': temps,
        'volumes': volumes,
        'rpms': rpms
    }


def calculate_durations(steps):
    """Calculate duration between steps."""
    if len(steps) < 2:
        return steps
    
    for i in range(len(steps) - 1):
        time1 = datetime.strptime(steps[i]['time'], '%H:%M')
        time2 = datetime.strptime(steps[i+1]['time'], '%H:%M')
        
        # Handle overnight case (though unlikely in this data)
        if time2 < time1:
            time2 = datetime.strptime(steps[i+1]['time'] + ' next day', '%H:%M next day')
        
        duration = (time2 - time1).seconds // 60  # minutes
        steps[i]['duration_min'] = duration
    
    return steps


def generate_sop_template(data):
    """Generate SOP markdown template from extracted data."""
    steps = data['steps']
    
    sop = "# Standard Operating Procedure: Catalyst-X9 Synthesis\n\n"
    sop += "## Version: 1.0\n"
    sop += "## Effective Date: 2024-03-13\n"
    sop += "## Author: Automated from Lab Notebook CX9-LAB-0312\n\n"
    
    sop += "## 1.0 Purpose\n"
    sop += "This SOP describes the synthesis procedure for Catalyst-X9 as recorded in lab notebook CX9-LAB-0312.\n\n"
    
    sop += "## 2.0 Scope\n"
    sop += "Applies to all laboratory personnel performing Catalyst-X9 synthesis during night shifts.\n\n"
    
    sop += "## 3.0 Equipment and Materials\n"
    sop += "### 3.1 Equipment\n"
    sop += "- 1 L jacketed glass reactor\n"
    sop += "- Temperature probe (calibrated)\n"
    sop += "- Stirrer (calibrated)\n"
    sop += "- Cooling fluid circulation system\n"
    sop += "- Reflux condenser (water at 18°C)\n"
    sop += "- Centrifuge (capable of 4000 RPM)\n"
    sop += "- 50 mL polypropylene centrifuge tubes\n"
    sop += "- Laboratory balance\n"
    sop += "- Safety equipment (gloves, goggles, lab coat)\n\n"
    
    sop += "### 3.2 Materials\n"
    if data['volumes']:
        sop += f"- Precursor A: {data['volumes'][0]} mL (lot P-A-112)\n"
        if len(data['volumes']) > 1:
            sop += f"- Reagent B: {data['volumes'][1]} mL (lot R-B-089)\n"
    else:
        sop += "- Precursor A: 500 mL (lot P-A-112)\n"
        sop += "- Reagent B: 200 mL (lot R-B-089)\n"
    sop += "- Diethyl ether (cold, for washing)\n"
    sop += "- Cooling water (18°C)\n\n"
    
    sop += "## 4.0 Safety Precautions\n"
    sop += "1. Wear appropriate PPE: lab coat, safety goggles, nitrile gloves.\n"
    sop += "2. Work in a fume hood when handling volatile reagents.\n"
    sop += "3. Be aware of exothermic reaction at 120°C.\n"
    sop += "4. Diethyl ether is highly flammable - keep away from ignition sources.\n"
    sop += "5. Know location of emergency shower, eyewash, and fire extinguisher.\n\n"
    
    sop += "## 5.0 Procedure\n"
    sop += "### 5.1 Preparation\n"
    sop += "1. Verify all equipment is clean and dry.\n"
    sop += "2. Calibrate stirrer and temperature probe if not done within last 30 days.\n"
    sop += "3. Ensure cooling fluid circulation is operational.\n"
    sop += "4. Set up reflux condenser with 18°C cooling water.\n\n"
    
    sop += "### 5.2 Synthesis Steps\n"
    for i, step in enumerate(steps, 1):
        duration = step.get('duration_min', 'N/A')
        sop += f"{i}. **{step['time']}** - {step['action']}"
        if duration != 'N/A':
            sop += f" (Duration: ~{duration} minutes)"
        sop += "\n"
    
    # Add inferred steps from incomplete notebook
    sop += "\n**Note:** Based on incomplete notebook, additional steps include:\n"
    sop += "1. Transfer slurry to 50 mL centrifuge tubes\n"
    sop += "2. Centrifuge at 4000 RPM for 15 minutes\n"
    sop += "3. Decant supernatant\n"
    sop += "4. Wash precipitate once with cold diethyl ether\n\n"
    
    sop += "### 5.3 Critical Parameters\n"
    if data['temperatures']:
        sop += f"- Reaction temperature: {data['temperatures'][0]}°C\n"
    if data['rpms']:
        sop += f"- Stirring speed: {data['rpms'][0]} RPM\n"
    sop += "- Ramp rate: 5°C/min (to 120°C)\n"
    sop += "- Hold time at temperature: 45 minutes\n"
    sop += "- Visual endpoint: Solution turns deep amber\n\n"
    
    sop += "## 6.0 Quality Control\n"
    sop += "1. Record lot numbers of all reagents.\n"
    sop += "2. Document actual volumes, temperatures, and times.\n"
    sop += "3. Note color changes and any deviations.\n"
    sop += "4. Weigh final product and calculate yield.\n\n"
    
    sop += "## 7.0 Troubleshooting\n"
    sop += "| Issue | Possible Cause | Solution |\n"
    sop += "|-------|---------------|----------|\n"
    sop += "| No color change after 45 min | Temperature too low | Verify temperature probe calibration |\n"
    sop += "| Excessive foaming | Reaction too vigorous | Reduce stirring speed slightly |\n"
    sop += "| Poor precipitation | Incorrect volumes | Verify measurements before starting |\n\n"
    
    sop += "## 8.0 References\n"
    sop += "- Lab Notebook CX9-LAB-0312 (2024-03-12)\n"
    sop += "- Material Safety Data Sheets for all reagents\n"
    
    return sop


def main():
    """Main analysis function."""
    notebook_path = Path('../data/lab_notebook_x9.txt')
    
    if not notebook_path.exists():
        notebook_path = Path('data/lab_notebook_x9.txt')
    
    text = read_notebook(notebook_path)
    print(f"Read {len(text)} characters from notebook\n")
    
    # Extract data
    data = extract_synthesis_steps(text)
    
    # Calculate durations
    data['steps'] = calculate_durations(data['steps'])
    
    print(f"Found {len(data['steps'])} time-stamped steps")
    print(f"Temperatures mentioned: {data['temperatures']}")
    print(f"Volumes mentioned: {data['volumes']}")
    print(f"RPM values: {data['rpms']}\n")
    
    # Display steps
    print("Extracted Steps:")
    for i, step in enumerate(data['steps'], 1):
        duration = step.get('duration_min', 'N/A')
        print(f"{i}. {step['time']}: {step['action']} (Duration: {duration} min)")
    
    # Generate SOP
    sop = generate_sop_template(data)
    
    # Save SOP
    sop_path = Path('../outputs/synthesis_sop_draft.md')
    if not sop_path.parent.exists():
        sop_path = Path('outputs/synthesis_sop_draft.md')
    
    with open(sop_path, 'w', encoding='utf-8') as f:
        f.write(sop)
    
    print(f"\nGenerated SOP draft saved to: {sop_path}")
    
    # Also create visualization
    create_visualization(data)
    
    return data, sop


def create_visualization(data):
    """Create visualization of synthesis timeline."""
    try:
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        from datetime import datetime, timedelta
        
        steps = data['steps']
        if len(steps) < 2:
            print("Not enough steps for visualization")
            return
        
        # Create timeline
        times = []
        actions = []
        
        # Use a reference date for plotting
        base_date = datetime(2024, 3, 12, 14, 0)  # Start at 14:00
        
        for step in steps:
            time_str = step['time']
            time_obj = datetime.strptime(time_str, '%H:%M')
            
            # Adjust to same day
            plot_time = base_date.replace(hour=time_obj.hour, minute=time_obj.minute)
            if plot_time < base_date:
                plot_time += timedelta(days=1)
            
            times.append(plot_time)
            actions.append(step['action'][:50] + '...' if len(step['action']) > 50 else step['action'])
        
        # Create figure
        plt.figure(figsize=(12, 6))
        
        # Plot timeline
        plt.plot(times, [1] * len(times), 'o-', markersize=10, linewidth=2)
        
        # Add labels
        for i, (time, action) in enumerate(zip(times, actions)):
            plt.annotate(f"{time.strftime('%H:%M')}\n{action}", 
                        (time, 1), 
                        xytext=(0, 20 if i % 2 == 0 else -30),
                        textcoords='offset points',
                        ha='center',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='lightblue', alpha=0.7),
                        arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.5'))
        
        plt.title('Catalyst-X9 Synthesis Timeline', fontsize=16, fontweight='bold')
        plt.yticks([])
        plt.xlabel('Time', fontsize=12)
        
        # Format x-axis
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=1))
        plt.gcf().autofmt_xdate()
        
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Save figure
        fig_path = Path('../report/images/synthesis_timeline.png')
        if not fig_path.parent.exists():
            fig_path = Path('report/images/synthesis_timeline.png')
        
        plt.savefig(fig_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Timeline visualization saved to: {fig_path}")
        
    except ImportError:
        print("Matplotlib not available for visualization")
    except Exception as e:
        print(f"Error creating visualization: {e}")


if __name__ == "__main__":
    main()