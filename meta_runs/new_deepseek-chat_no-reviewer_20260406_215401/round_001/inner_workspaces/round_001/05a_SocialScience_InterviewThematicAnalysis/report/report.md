# Research Report: Thematic Analysis of Transportation App User Interviews

*Note: This is the main research report as specified in the execution protocol. A more detailed version is available as `interview_thematic_report.md`.*

## Executive Summary

This mixed-methods study analyzed interview excerpts from 18 transportation app users (9 transit-primary, 9 car-primary) to identify user needs, pain points, and UX implications. Quantitative analysis revealed similar response lengths between cohorts (20.22 vs. 19.67 words) with distinct vocabulary patterns. LLM-assisted thematic analysis identified three primary themes per cohort:

**Transit-primary users**: Reliability/real-time information, safety/crowding concerns, information integration/UX design
**Car-primary users**: Multimodal integration/decision support, information filtering/interface simplicity, safety/practical considerations

**Key findings**:
1. Both cohorts share concerns about information reliability, safety, and integration needs
2. Transit users emphasize real-time updates and accessibility
3. Car users focus on multimodal planning and cost comparisons
4. UX implications include unified information displays, intelligent alert filtering, and prominent safety information

## 1. Methodology

### 1.1 Data

- 18 interview excerpts from transportation app users
- Balanced design: 9 transit-primary, 9 car-primary
- Data file: `data/interview_excerpts.csv`

### 1.2 Quantitative Analysis

- Descriptive statistics (cohort distribution, response lengths)
- Word frequency analysis (overall and by cohort)
- Visualization using matplotlib/seaborn

### 1.3 Qualitative Analysis

- LLM-assisted thematic analysis using Claude 3.5 Sonnet
- Structured prompt for thematic identification
- Cross-cohort comparison synthesis

### 1.4 Implementation

- Python scripts in `code/analysis.py`
- Outputs saved to `outputs/` directory
- Visualizations saved to `report/images/`

## 2. Results

### 2.1 Quantitative Results

![Cohort Distribution](images/cohort_distribution.png)

**Cohort Statistics**:
- Equal distribution: 9 respondents per cohort
- Average word count: 19.94 overall (transit: 20.22, car: 19.67)
- Similar variability in response lengths

**Word Frequency**:
- Top overall words: "the", "and", "are", "when", "app"
- Transit-distinctive: "miss", "train", "single"
- Car-distinctive: "drive", "transit", "parking"

### 2.2 Qualitative Results

![Word Frequencies](images/word_frequencies.png)

**Transit-Primary Themes**:
1. **Reliability and Real-time Information** (High frequency)
   - Accuracy of arrival times and delays
   - Need for honest disruption explanations

2. **Safety and Crowding Concerns** (Medium frequency)
   - Platform safety and crowding
   - Accessibility information gaps

3. **Information Integration and UX Design** (High frequency)
   - Fragmented pricing information
   - Poor transfer experience design

**Car-Primary Themes**:
1. **Multimodal Integration and Decision Support** (High frequency)
   - Seamless park-and-ride integration
   - Cost comparison tools (fuel vs. fare)

2. **Information Filtering and Interface Simplicity** (Medium frequency)
   - Alert fatigue reduction
   - Simplified interface design

3. **Safety and Practical Considerations** (Medium frequency)
   - Parking lot safety
   - Trust in map accuracy over ETAs

### 2.3 Cross-Cohort Comparisons

**Shared Concerns**:
1. Information reliability
2. Safety considerations
3. Integrated information needs

**Key Differences**:
1. Transit: Real-time updates, crowding, accessibility
2. Car: Multimodal integration, cost comparisons, interface simplicity

## 3. Discussion

### 3.1 Design Implications

1. **Unified Information Displays**: Combine transit, driving, and cost information
2. **Intelligent Alert Filtering**: User-configurable notification systems
3. **Prominent Safety Information**: Standardized safety displays across contexts
4. **Seamless Multimodal Planning**: Integrated trip planning across modes

### 3.2 Limitations

- Sample size (n=9 per cohort) limits generalizability
- Brief excerpts may not capture full user experiences
- LLM interpretation may miss human nuance
- No demographic/geographic context

### 3.3 Future Research

1. Comparative studies on information prioritization
2. Effectiveness testing of cost presentation interfaces
3. Development of safety information standards
4. Longitudinal tracking of evolving user needs

## 4. Conclusion

This study demonstrates that transportation app users have both distinct and shared needs based on their primary mode. Transit users require accurate real-time information and accessibility details, while car users need better multimodal integration and cost comparison tools. Both groups value information reliability, safety, and integrated displays. These findings provide actionable guidance for designing more effective, user-centered transportation applications.

## 5. Files and Reproducibility

- **Code**: `code/analysis.py`, `code/requirements.txt`
- **Data**: `data/interview_excerpts.csv`
- **Outputs**: `outputs/analysis_summary.json`, `outputs/anthropic_messages_response.json`
- **Visualizations**: `report/images/cohort_distribution.png`, `report/images/word_frequencies.png`, `report/images/response_length_distribution.png`
- **Reports**: `report/interview_thematic_report.md` (detailed), `report/report.md` (this summary)

All analysis is reproducible using the provided code and data.
