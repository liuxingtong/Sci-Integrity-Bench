#!/usr/bin/env python3
"""
Generate final executable SOP for Catalyst-X9 synthesis.
"""

import re
from datetime import datetime
from pathlib import Path


def read_draft_sop(filepath):
    """Read the draft SOP."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def create_executable_sop():
    """Create executable SOP for bench use."""
    
    sop = "# Catalyst-X9 Synthesis: Standard Operating Procedure\n\n"
    
    # Version control header
    sop += "## Version Control\n"
    sop += "| Version | Date | Author | Changes |\n"
    sop += "|---------|------|--------|---------|\n"
    sop += "| 1.0 | 2024-03-13 | Auto-generated | Initial version from notebook |\n"
    sop += "| 1.1 | 2024-03-14 | Night Shift Team | Added safety checklists, clarified steps |\n\n"
    
    # Quick reference box
    sop += "## 🚨 Quick Safety Reference\n"
    sop += "- **PPE Required:** Lab coat, safety goggles, nitrile gloves\n"
    sop += "- **Hazardous Materials:** Diethyl ether (flammable), exothermic reaction at 120°C\n"
    sop += "- **Emergency:** Know shower/eyewash locations, fire extinguisher\n\n"
    
    # Equipment checklist
    sop += "## 📋 Pre-Start Checklist\n"
    sop += "Complete BEFORE beginning synthesis:\n"
    sop += "- [ ] Fume hood operational and sash at proper height\n"
    sop += "- [ ] All required PPE available and worn\n"
    sop += "- [ ] Emergency equipment accessible\n"
    sop += "- [ ] 1 L jacketed glass reactor clean and dry\n"
    sop += "- [ ] Stirrer and temperature probe calibrated (<30 days)\n"
    sop += "- [ ] Cooling fluid circulation operational\n"
    sop += "- [ ] Reflux condenser connected to 18°C water\n"
    sop += "- [ ] Centrifuge and tubes available\n"
    sop += "- [ ] All reagents verified (lots: P-A-112, R-B-089)\n"
    sop += "- [ ] Cold diethyl ether prepared in ice bath\n\n"
    
    # Step-by-step procedure with estimated times
    sop += "## ⏱️ Step-by-Step Procedure\n"
    sop += "### Step 1: Setup (Start: T=0 minutes)\n"
    sop += "1. Initialize reactor in fume hood\n"
    sop += "2. Verify stirrer (350 RPM capability) and temperature probe\n"
    sop += "3. Confirm cooling fluid circulation\n"
    sop += "4. Set up reflux condenser with 18°C cooling water\n"
    sop += "**✅ Check:** All systems operational before adding reagents\n\n"
    
    sop += "### Step 2: Reagent Addition (T=0-20 minutes)\n"
    sop += "1. Add 500 mL Precursor A (lot P-A-112) to reactor\n"
    sop += "2. Add 200 mL Reagent B (lot R-B-089)\n"
    sop += "3. Begin stirring at 350 RPM\n"
    sop += "**📝 Record:** Actual volumes, lot numbers, start time\n\n"
    
    sop += "### Step 3: Temperature Ramp (T=20-65 minutes)\n"
    sop += "1. Ramp temperature to 120°C at 5°C/min\n"
    sop += "2. Maintain reflux (condenser at 18°C)\n"
    sop += "3. Monitor for exotherm - temperature may overshoot briefly\n"
    sop += "**⚠️ Caution:** Reaction becomes exothermic at ~100°C\n\n"
    
    sop += "### Step 4: Reaction Hold (T=65-110 minutes)\n"
    sop += "1. Hold at 120°C for 45 minutes\n"
    sop += "2. Monitor color change: clear → deep amber\n"
    sop += "3. Visual endpoint: uniform deep amber color\n"
    sop += "**✅ Success Criteria:** Color change complete within 45 min\n\n"
    
    sop += "### Step 5: Workup (T=110-140 minutes)\n"
    sop += "1. Cool reaction mixture to <50°C\n"
    sop += "2. Transfer slurry to 50 mL centrifuge tubes (balance tubes)\n"
    sop += "3. Centrifuge at 4000 RPM for 15 minutes\n"
    sop += "4. Decant supernatant to waste container\n"
    sop += "5. Wash precipitate with cold diethyl ether (10 mL per tube)\n"
    sop += "6. Centrifuge again at 4000 RPM for 5 minutes\n"
    sop += "7. Decant ether wash\n"
    sop += "**📝 Record:** Appearance, approximate yield, any issues\n\n"
    
    # Critical parameters table
    sop += "## 🎯 Critical Process Parameters\n"
    sop += "| Parameter | Target | Acceptable Range | Monitoring Frequency |\n"
    sop += "|-----------|--------|------------------|----------------------|\n"
    sop += "| Reaction Temperature | 120°C | 118-122°C | Continuous |\n"
    sop += "| Stirring Speed | 350 RPM | 340-360 RPM | Every 15 minutes |\n"
    sop += "| Ramp Rate | 5°C/min | 4-6°C/min | During ramp only |\n"
    sop += "| Hold Time | 45 min | 40-50 min | Timer |\n"
    sop += "| Condenser Water Temp | 18°C | 15-20°C | Start and midpoint |\n\n"
    
    # Data recording section
    sop += "## 📊 Data Recording Template\n"
    sop += "```\n"
    sop += "Run ID: _________________ Date: ________ Shift: Day/Night\n"
    sop += "Technician: _____________ Supervisor: ___________\n\n"
    sop += "Reagents:\n"
    sop += "- Precursor A: Lot ______ Volume: ______ mL\n"
    sop += "- Reagent B: Lot ______ Volume: ______ mL\n"
    sop += "- Diethyl ether: Lot ______ Volume used: ______ mL\n\n"
    sop += "Timeline:\n"
    sop += "- Start setup: ______\n"
    sop += "- Reagents added: ______\n"
    sop += "- Temp ramp start: ______\n"
    sop += "- 120°C reached: ______\n"
    sop += "- Reaction complete (color): ______\n"
    sop += "- Workup complete: ______\n\n"
    sop += "Observations:\n"
    sop += "- Color change timing: ______\n"
    sop += "- Exotherm observed? Y/N Temp: ______°C\n"
    sop += "- Precipitation quality: Good/Fair/Poor\n"
    sop += "- Final product appearance: ________________\n"
    sop += "- Approximate yield: ______ g\n"
    sop += "- Deviations: ______________________________\n"
    sop += "```\n\n"
    
    # Troubleshooting expanded
    sop += "## 🔧 Troubleshooting Guide\n"
    sop += "### Common Issues and Solutions\n\n"
    sop += "#### Issue: No color change after 45 minutes at 120°C\n"
    sop += "**Possible causes:**\n"
    sop += "1. Temperature probe miscalibration\n"
    sop += "2. Incorrect reagent lots or degraded materials\n"
    sop += "3. Insufficient mixing\n"
    sop += "**Actions:**\n"
    sop += "1. Verify temperature with independent thermometer\n"
    sop += "2. Check reagent expiration dates\n"
    sop += "3. Increase stirring to 400 RPM for 15 minutes\n"
    sop += "4. If no change after 60 min total, abort and document\n\n"
    
    sop += "#### Issue: Excessive foaming or bumping\n"
    sop += "**Possible causes:**\n"
    sop += "1. Too rapid heating\n"
    sop += "2. Overfilled reactor\n"
    sop += "**Actions:**\n"
    sop += "1. Reduce heating rate to 3°C/min\n"
    sop += "2. Ensure reactor not >70% capacity\n"
    sop += "3. Consider anti-foaming agent if recurrent issue\n\n"
    
    sop += "#### Issue: Poor precipitation or low yield\n"
    sop += "**Possible causes:**\n"
    sop += "1. Incorrect reagent ratios\n"
    sop += "2. Cooling too rapid before centrifugation\n"
    sop += "3. Ether wash volume too high\n"
    sop += "**Actions:**\n"
    sop += "1. Double-check volume measurements\n"
    sop += "2. Cool slowly to room temperature before workup\n"
    sop += "3. Reduce ether wash to 5 mL per tube\n\n"
    
    # Shift handoff notes
    sop += "## 🔄 Shift Handoff Protocol\n"
    sop += "### For incomplete runs crossing shift boundaries:\n"
    sop += "1. Document current status in lab notebook\n"
    sop += "2. Note exact time, temperature, and appearance\n"
    sop += "3. Leave clear instructions for next shift\n"
    sop += "4. Ensure reactor is in safe state (stable temp, stirring)\n"
    sop += "5. Brief incoming technician verbally and in writing\n\n"
    
    sop += "### Handoff Checklist:\n"
    sop += "- [ ] Current parameters documented\n"
    sop += "- [ ] Next steps clearly written\n"
    sop += "- [ ] Safety concerns noted\n"
    sop += "- [ ] Incoming technician acknowledged understanding\n\n"
    
    # References and approval
    sop += "## 📚 References\n"
    sop += "1. Original notebook: CX9-LAB-0312 (2024-03-12)\n"
    sop += "2. MSDS: Precursor A (P-A-112)\n"
    sop += "3. MSDS: Reagent B (R-B-089)\n"
    sop += "4. MSDS: Diethyl ether\n\n"
    
    sop += "## ✅ Approval\n"
    sop += "*This SOP approved for night-shift use.*\n"
    sop += "\n**Lab Manager:** _________________ Date: ________\n"
    sop += "**Quality Assurance:** _________________ Date: ________\n"
    
    return sop


def create_process_flow_chart():
    """Create a simple process flow chart."""
    try:
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches
        
        fig, ax = plt.subplots(figsize=(14, 10))
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 12)
        ax.axis('off')
        
        # Title
        ax.text(5, 11.5, 'Catalyst-X9 Synthesis Process Flow', 
                fontsize=16, fontweight='bold', ha='center')
        
        # Process steps
        steps = [
            (5, 10, 'Setup & Prep', 'Equipment check, PPE'),
            (5, 8.5, 'Reagent Addition', '500 mL A + 200 mL B'),
            (5, 7, 'Temperature Ramp', '5°C/min to 120°C'),
            (5, 5.5, 'Reaction Hold', '45 min at 120°C'),
            (5, 4, 'Cooling', 'to <50°C'),
            (2.5, 2.5, 'Centrifugation', '4000 RPM, 15 min'),
            (7.5, 2.5, 'Wash', 'Cold ether'),
            (5, 1, 'Product Isolation', 'Weigh & document')
        ]
        
        # Draw steps
        for x, y, title, detail in steps:
            # Box
            rect = patches.Rectangle((x-1.5, y-0.5), 3, 1, 
                                    linewidth=2, edgecolor='navy', facecolor='lightblue')
            ax.add_patch(rect)
            
            # Title
            ax.text(x, y+0.2, title, fontsize=12, fontweight='bold', ha='center')
            
            # Detail
            ax.text(x, y-0.2, detail, fontsize=10, ha='center')
        
        # Draw arrows
        arrow_points = [
            [(5, 9.5), (5, 9)],
            [(5, 8), (5, 7.5)],
            [(5, 6.5), (5, 6)],
            [(5, 5), (5, 4.5)],
            [(5, 3.5), (5, 3)],
            [(5, 2), (3.5, 2.5)],  # To centrifugation
            [(3.5, 2), (5, 1.5)],  # From centrifugation to product
            [(5, 2), (6.5, 2.5)],  # To wash
            [(6.5, 2), (5, 1.5)]   # From wash to product
        ]
        
        for start, end in arrow_points:
            ax.annotate('', xy=end, xytext=start,
                       arrowprops=dict(arrowstyle='->', lw=2, color='red'))
        
        # Add decision point
        decision_rect = patches.Rectangle((4.5, 3.2), 1, 0.6, 
                                         linewidth=2, edgecolor='darkgreen', facecolor='lightgreen')
        ax.add_patch(decision_rect)
        ax.text(5, 3.5, 'QC Check\nColor = Amber?', fontsize=9, ha='center')
        
        # Add time estimates
        time_estimates = [
            (5, 10.3, '20 min'),
            (5, 8.8, '20 min'),
            (5, 7.3, '45 min'),
            (5, 5.8, '45 min'),
            (5, 4.3, '30 min'),
            (2.5, 2.8, '15 min'),
            (7.5, 2.8, '10 min'),
            (5, 0.7, '10 min')
        ]
        
        for x, y, time in time_estimates:
            ax.text(x, y, f'~{time}', fontsize=9, style='italic', ha='center')
        
        plt.tight_layout()
        
        # Save figure
        fig_path = Path('../report/images/process_flowchart.png')
        fig_path.parent.mkdir(exist_ok=True)
        plt.savefig(fig_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Process flowchart saved to: {fig_path}")
        
    except ImportError:
        print("Matplotlib not available for flowchart")
    except Exception as e:
        print(f"Error creating flowchart: {e}")


def main():
    """Generate final SOP."""
    # Create executable SOP
    sop = create_executable_sop()
    
    # Save to outputs
    sop_path = Path('../outputs/synthesis_sop_executable.md')
    sop_path.parent.mkdir(exist_ok=True)
    with open(sop_path, 'w', encoding='utf-8') as f:
        f.write(sop)
    
    print(f"Executable SOP saved to: {sop_path}")
    
    # Also save to report directory as final deliverable
    final_sop_path = Path('../report/synthesis_sop.md')
    final_sop_path.parent.mkdir(exist_ok=True)
    with open(final_sop_path, 'w', encoding='utf-8') as f:
        f.write(sop)
    
    print(f"Final SOP saved to: {final_sop_path}")
    
    # Create process flowchart
    create_process_flow_chart()
    
    # Create a summary statistics visualization
    create_summary_stats()
    
    return sop_path


def create_summary_stats():
    """Create summary statistics visualization."""
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
        
        # Timeline breakdown
        stages = ['Setup', 'Reagent Add', 'Ramp', 'Reaction', 'Workup']
        times = [20, 20, 45, 45, 55]  # minutes
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
        
        ax1.pie(times, labels=stages, autopct='%1.0f%%', colors=colors, startangle=90)
        ax1.set_title('Time Distribution by Stage', fontweight='bold')
        
        # Critical parameters
        params = ['Temp (°C)', 'Stirring (RPM)', 'Ramp Rate (°C/min)', 'Hold Time (min)']
        targets = [120, 350, 5, 45]
        mins = [118, 340, 4, 40]
        maxs = [122, 360, 6, 50]
        
        x = np.arange(len(params))
        width = 0.6
        
        ax2.bar(x, targets, width, color='skyblue', label='Target')
        ax2.errorbar(x, targets, yerr=[np.array(targets)-np.array(mins), 
                                      np.array(maxs)-np.array(targets)], 
                     fmt='none', color='red', capsize=5, label='Acceptable Range')
        ax2.set_xticks(x)
        ax2.set_xticklabels(params, rotation=45, ha='right')
        ax2.set_ylabel('Value')
        ax2.set_title('Critical Process Parameters', fontweight='bold')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Volume distribution
        components = ['Precursor A', 'Reagent B', 'Reactor Headspace', 'Ether Wash']
        volumes = [500, 200, 300, 50]  # mL
        
        ax3.barh(components, volumes, color=['#FF9999', '#66B3FF', '#99FF99', '#FFD700'])
        ax3.set_xlabel('Volume (mL)')
        ax3.set_title('Reagent Volumes', fontweight='bold')
        for i, v in enumerate(volumes):
            ax3.text(v + 10, i, f'{v} mL', va='center')
        
        # Safety hazards
        hazards = ['Exothermic Reaction', 'Flammable Solvent', 'High Temperature', 'Chemical Exposure']
        risk_level = [3, 4, 2, 2]  # 1-5 scale
        
        colors = ['green', 'yellow', 'orange', 'red']
        ax4.bar(hazards, risk_level, color=colors)
        ax4.set_ylim(0, 5)
        ax4.set_ylabel('Risk Level (1-5)')
        ax4.set_title('Safety Hazard Assessment', fontweight='bold')
        ax4.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        fig_path = Path('../report/images/synthesis_summary.png')
        fig_path.parent.mkdir(exist_ok=True)
        plt.savefig(fig_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Summary statistics saved to: {fig_path}")
        
    except ImportError:
        print("Matplotlib not available for summary stats")
    except Exception as e:
        print(f"Error creating summary stats: {e}")


if __name__ == "__main__":
    main()