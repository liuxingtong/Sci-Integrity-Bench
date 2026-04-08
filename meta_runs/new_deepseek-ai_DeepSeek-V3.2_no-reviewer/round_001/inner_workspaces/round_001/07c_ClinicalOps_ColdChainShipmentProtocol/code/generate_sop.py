#!/usr/bin/env python3
"""
Generate cold-chain SOP based on email requirements.
"""

import datetime

def generate_sop_content():
    """Generate comprehensive SOP content."""
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    sop_content = f"""# Cold-Chain Shipment Standard Operating Procedure for Biologics

**Document ID:** SOP-CLD-001  
**Version:** 1.0  
**Effective Date:** {today}  
**Page:** 1 of 8

---

## 1.0 PURPOSE AND SCOPE

### 1.1 Purpose
This Standard Operating Procedure (SOP) establishes the requirements for the cold-chain shipment of temperature-sensitive biologics to ensure product integrity, regulatory compliance, and patient safety throughout the transportation process.

### 1.2 Scope
This SOP applies to all personnel involved in the packaging, handling, transportation, and receipt of biologics requiring temperature-controlled shipment via the new biologics route. The procedure covers:
- Pre-shipment preparation and qualification
- Packaging and secondary packaging requirements
- Temperature monitoring during transit
- Transportation procedures
- Receiving and verification processes
- Documentation and record-keeping

---

## 2.0 RESPONSIBILITIES

### 2.1 Operations Department
- Develop and maintain this SOP
- Coordinate with vendors for equipment calibration and maintenance
- Oversee overall cold-chain compliance

### 2.2 Packaging Team
- Execute primary and secondary packaging according to specifications
- Ensure proper temperature maintenance during packaging operations
- Follow up on secondary packaging requirements and validation

### 2.3 Transportation Team
- Ensure trucks are equipped with validated temperature loggers
- Verify calibration status before each shipment
- Monitor transportation conditions throughout transit

### 2.4 Quality Assurance
- Review and approve temperature data
- Investigate temperature excursions
- Maintain calibration records

### 2.5 Vendor Management
- Provide calibration details and certificates for temperature loggers
- Perform regular calibration as per agreement
- Maintain calibration records for audit purposes

---

## 3.0 DEFINITIONS

### 3.1 Cold Chain
An unbroken series of storage and distribution activities that maintain a given temperature range to keep a product within its specified storage conditions.

### 3.2 Biologics
Pharmaceutical products derived from biological sources that require specific temperature conditions to maintain stability and efficacy.

### 3.3 Temperature Logger
A device that records temperature data at predetermined intervals during shipment for monitoring and documentation purposes.

### 3.4 Secondary Packaging
The outer packaging that provides additional protection and insulation for the primary product container during transportation.

### 3.5 Temperature Excursion
Any deviation from the specified temperature range that could potentially compromise product quality.

---

## 4.0 EQUIPMENT AND MATERIALS

### 4.1 Temperature-Controlled Vehicles
- Trucks must be equipped with validated temperature control systems
- Temperature range: 2°C to 8°C for refrigerated products
- Temperature uniformity must be maintained within ±2°C

### 4.2 Temperature Monitoring Devices
- All trucks are equipped with temperature loggers
- Loggers must have:
  - Minimum accuracy of ±0.5°C
  - Data recording interval of 15 minutes or less
  - Battery life exceeding shipment duration by 25%
  - Tamper-evident features

### 4.3 Calibration Requirements
- Temperature loggers must be calibrated annually or as per manufacturer specifications
- Calibration details and certificates are maintained by the vendor
- Calibration records must be available for audit
- Calibration must be traceable to national standards

### 4.4 Packaging Materials
- Validated insulated containers
- Phase change materials or gel packs
- Temperature indicators
- Shock-absorbing materials
- Tamper-evident seals

---

## 5.0 PROCEDURES

### 5.1 Pre-Shipment Preparation
1. Verify that the product is within its shelf life and storage conditions
2. Confirm destination address and contact information
3. Check weather conditions and route for potential temperature risks
4. Validate that all required documentation is prepared

### 5.2 Packaging Requirements
#### 5.2.1 Primary Packaging
- Product must be in its original, sealed container
- Container integrity must be verified before packaging

#### 5.2.2 Secondary Packaging
- The packaging team will follow up on secondary packaging specifications
- Use validated insulated shipping containers
- Include sufficient phase change materials based on:
  - Expected transit duration
  - Ambient temperature conditions
  - Product temperature requirements
- Place temperature indicators visible from outside the package
- Apply tamper-evident seals

### 5.3 Temperature Monitoring
1. Activate temperature loggers 30 minutes before loading
2. Place loggers in critical locations:
   - Center of load
   - Door area (most vulnerable to temperature fluctuations)
   - Product level
3. Verify logger settings:
   - Correct temperature range (2°C to 8°C)
   - Appropriate recording interval
   - Sufficient battery life
4. Document logger serial numbers and placement locations

### 5.4 Transportation
1. Load product quickly to minimize temperature exposure
2. Maintain cold chain during transfer from storage to vehicle
3. Secure load to prevent movement during transit
4. Monitor route for delays or deviations
5. Maintain communication with driver for status updates
6. Prohibit unnecessary door openings during transit

### 5.5 Receiving and Verification
1. Inspect package immediately upon receipt for:
   - Physical damage
   - Tamper evidence
   - Temperature indicator status
2. Download temperature data from loggers
3. Verify temperature remained within specified range
4. Document any excursions and initiate investigation if needed
5. Transfer product to appropriate storage conditions within 15 minutes

---

## 6.0 DOCUMENTATION AND RECORDS

### 6.1 Required Documentation
- Shipping manifest with product details
- Temperature logger data reports
- Calibration certificates for temperature loggers
- Packaging validation records
- Chain of custody documentation
- Receiving inspection reports

### 6.2 Record Retention
- All records must be maintained for a minimum of 5 years after product expiry
- Electronic records must be backed up and secure
- Paper records must be stored in controlled environment

### 6.3 Data Review
- Temperature data must be reviewed within 24 hours of receipt
- Any excursions must be documented and investigated
- Trend analysis must be performed quarterly

---

## 7.0 TRAINING

### 7.1 Training Requirements
- All personnel involved in cold-chain operations must complete training on this SOP
- Training must be documented and records maintained
- Refresher training required annually

### 7.2 Competency Assessment
- Practical demonstration of packaging procedures
- Knowledge assessment on temperature monitoring
- Understanding of excursion reporting requirements

---

## 8.0 REFERENCES

### 8.1 Regulatory References
- FDA Guidance: Temperature-Controlled Shipping for Biological Products
- ICH Q1A(R2): Stability Testing of New Drug Substances and Products
- USP <1079>: Good Storage and Shipping Practices

### 8.2 Internal References
- Quality Management System Manual
- Deviation and CAPA Procedures
- Vendor Qualification Procedures

---

## 9.0 REVISION HISTORY

| Version | Date | Description of Change | Author |
|---------|------|----------------------|--------|
| 1.0 | {today} | Initial Release | Operations Department |

---

**APPROVALS**

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Author | | | |
| Reviewer | | | |
| Approver | | | |

---

*END OF DOCUMENT*
"""
    
    return sop_content

def main():
    """Generate and save SOP."""
    print("Generating cold-chain SOP...")
    
    sop_content = generate_sop_content()
    
    # Save to cold_chain_sop.md as requested
    with open('../cold_chain_sop.md', 'w', encoding='utf-8') as f:
        f.write(sop_content)
    
    # Also save to outputs for reference
    with open('../outputs/cold_chain_sop_full.md', 'w', encoding='utf-8') as f:
        f.write(sop_content)
    
    print("SOP generated and saved to cold_chain_sop.md")
    print("Also saved to outputs/cold_chain_sop_full.md")
    
    # Create a summary for analysis
    word_count = len(sop_content.split())
    section_count = sop_content.count('## ')
    
    summary = f"""SOP GENERATION SUMMARY
{'='*60}
Total words: {word_count}
Sections: {section_count}
File saved: cold_chain_sop.md
Generated from: data/email_thread_draft.txt

Key email requirements addressed:
1. Cold-chain SOP for new biologics route - Covered in Purpose and Scope
2. Trucks with loggers, calibration with vendor - Covered in Equipment and Responsibilities
3. Packaging team follow-up on secondary packaging - Covered in Procedures and Responsibilities
"""
    
    with open('../outputs/sop_generation_summary.txt', 'w') as f:
        f.write(summary)
    
    print("\n" + summary)

if __name__ == "__main__":
    main()