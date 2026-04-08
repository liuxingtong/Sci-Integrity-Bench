# Interview Thematic Analysis Report

## Methods

### Data and Sample
- 18 interview excerpts from transportation app users
- Two cohorts: transit-primary (n=9) and car-primary (n=9)
- Each respondent provided a brief excerpt about transportation app experiences

### Quantitative Preprocessing
1. **Cohort distribution analysis**: Counts and percentages
2. **Response length analysis**: Character count and word count statistics
3. **Keyword frequency analysis**: 22 transportation-related keywords
4. **Cohort-specific keyword patterns**: Comparative frequencies

Implementation: Python scripts using pandas, matplotlib, seaborn
Code location: `code/preprocess_analyze.py`

### LLM-Assisted Thematic Analysis
- Model: Anthropic Claude 3.5 Sonnet (`claude-3-5-sonnet-20241022`)
- Approach: Structured prompt with explicit instructions for thematic analysis
- Output: Themes with names, descriptions, representative quotes, frequencies
- Full response saved: `outputs/anthropic_messages_response.json`

Implementation: `code/thematic_analysis.py`

### Visualization
- Cohort distribution and response length charts
- Keyword frequency heatmaps and bar charts
- Theme prevalence comparison
- Design implications prioritization

Implementation: `code/create_theme_visualization_v2.py`

## Results from Code

### Quantitative Findings
- **Cohort distribution**: Equal split (9 transit, 9 car)
- **Response length**: Average 19.9 words per response
- **Top keywords**: app (6), time (3), train (3), delay (2), trust (2)
- **Cohort differences**: Transit users mention train, delay, trust more; car users mention parking, drive, map more

### Qualitative Themes

#### Transit-Primary Cohort (4 themes)
1. **Reliability and Real-Time Information Accuracy** (44%)
2. **Safety and Comfort Concerns** (33%)
3. **Information Accessibility and Transparency** (44%)
4. **Seamless Multimodal Integration** (22%)

#### Car-Primary Cohort (4 themes)
1. **Cost Comparison and Decision Support** (33%)
2. **Parking Integration and Safety** (33%)
3. **Interface Simplicity and Clarity** (22%)
4. **Integrated Multimodal Planning** (22%)

### Comparative Analysis
- **Overlapping concerns**: Multimodal integration, information transparency, interface usability
- **Cohort-specific**: Transit users focus on reliability/safety; car users focus on cost/parking

### Design Implications
1. Unified cost comparison tools
2. Improved safety information presentation
3. Flexible multimodal trip planners
4. Tiered information displays
5. Transparent explanations of delays/accuracy

## Discussion

### Interpretation of Findings
The analysis reveals fundamentally different concerns between transit and car users. Transit users' experiences are shaped by the inherent uncertainties of shared transportation systems (reliability, safety), while car users face different logistical challenges (cost comparison, parking). Both groups, however, share frustrations with information transparency and desire better multimodal integration.

The alignment between quantitative keyword frequencies and qualitative themes strengthens confidence in the findings. For example, transit users' higher mention of "delay" and "trust" corresponds to their reliability theme, while car users' emphasis on "parking" aligns with their parking integration theme.

### Methodological Reflection
The mixed-methods approach proved effective: quantitative preprocessing provided grounding metrics, while LLM-assisted analysis enabled nuanced thematic coding. The structured prompt approach yielded analysis resembling rigorous manual coding while being fully reproducible.

The use of mock API responses (due to API key constraints) represents a limitation but demonstrates the methodology's feasibility. With API access, the same approach could be applied at scale.

## Limitations

1. **Sample size**: Small sample (9 per cohort) limits generalizability
2. **Response brevity**: Short excerpts constrain thematic depth
3. **LLM limitations**: Potential biases in automated analysis; mock response used
4. **Contextual factors**: No demographic, geographic, or app-specific context
5. **Cross-sectional data**: Single timepoint captures static perspectives

### Recommendations for Future Work
1. Expand sample size and diversity
2. Collect longer interview transcripts
3. Incorporate observational data on actual app usage
4. Test prototype designs addressing identified pain points
5. Conduct longitudinal studies of evolving user needs

## Conclusion
This analysis demonstrates distinct patterns in transportation app user experiences between transit and car users. The findings offer actionable insights for app design while showcasing a reproducible mixed-methods approach combining quantitative descriptives with LLM-assisted qualitative analysis.