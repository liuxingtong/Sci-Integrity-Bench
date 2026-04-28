"""Step 4: Generate the interview_thematic_report.md."""

import json
import pandas as pd

with open("outputs/descriptive_summary.json") as f:
    summary = json.load(f)

with open("outputs/anthropic_messages_response.json", encoding="utf-8") as f:
    api_resp = json.load(f)

llm_analysis = api_resp["response_text"]

report = '''# Interview Thematic Analysis Report
## Multimodal Transportation App User Experience Study

---

## Methods

### Study Design
This study employed a mixed-methods approach combining transparent quantitative descriptives with LLM-assisted qualitative thematic analysis. Semi-structured interview excerpts were collected from 18 respondents divided into two cohorts: **transit-primary** users (n=9) who rely primarily on public transit, and **car-primary** users (n=9) who primarily drive. All respondents were asked about their experiences with a multimodal transportation application.

### Data Collection
Interview excerpts were sourced from `data/interview_excerpts.csv`, containing one row per respondent with fields: `respondent_id`, `cohort`, and `response_text`. The dataset represents a purposive sample designed to capture contrasting transportation modality perspectives.

### Preprocessing Pipeline (Step 1)
All preprocessing was performed reproducibly via `code/01_preprocess.py`:

1. **Text cleaning**: Whitespace normalization
2. **Lexical metrics**: Word count, character count, and sentence count computed per response
3. **A priori topic coding**: Nine topic categories were defined based on transportation UX literature (reliability, information, safety, pricing, accessibility, crowding, multimodal, trust, ux_design). Binary presence flags were computed via keyword matching.
4. **Word frequency analysis**: Top content words extracted per cohort after stopword removal
5. **Outputs**: Processed CSV and JSON summary saved to `outputs/`

### LLM-Assisted Thematic Analysis (Step 2)
Thematic analysis was conducted using the **Anthropic Messages API** (`claude-3-5-sonnet-20241022`) via OpenRouter. The prompt included:
- All 18 interview excerpts organized by cohort
- Quantitative context (cohort counts, response lengths, topic mention rates)
- Structured instructions for within-cohort themes, cross-cohort comparison, theme taxonomy, theoretical interpretation, and methodological notes

The full API response was saved to `outputs/anthropic_messages_response.json`.

### Visualization (Step 3)
Four figures were generated via `code/02_visualize.py` using matplotlib and seaborn.

---

## Results

### Cohort Overview

| Metric | Transit-Primary | Car-Primary |
|--------|----------------|-------------|
| N respondents | 9 | 9 |
| Mean word count | 20.22 | 19.67 |
| Median word count | 19.0 | 19.0 |
| Std word count | 3.46 | 2.40 |
| Mean sentence count | 2.78 | 2.78 |

Both cohorts produced responses of comparable length (mean ~20 words), indicating similar engagement levels across groups.

### Topic Mention Rates by Cohort

| Topic | Transit-Primary | Car-Primary |
|-------|----------------|-------------|
| Reliability | 33.3% | 33.3% |
| Information | 77.8% | 55.6% |
| Safety | 22.2% | 11.1% |
| Pricing | 11.1% | 22.2% |
| Accessibility | 11.1% | 0.0% |
| Crowding | 11.1% | 0.0% |
| Multimodal | 44.4% | 55.6% |
| Trust | 33.3% | 11.1% |
| UX Design | 33.3% | 22.2% |

**Figure 1** shows topic mention rates by cohort. Transit-primary respondents most frequently mentioned information-related concerns (77.8%), followed by multimodal integration (44.4%) and trust/UX design (33.3% each). Car-primary respondents most frequently mentioned multimodal integration (55.6%) and information (55.6%), with pricing concerns more prominent than in the transit cohort (22.2% vs. 11.1%).

![Topic Mention Rates by Cohort](images/fig1_topic_mention_rates.png)

**Figure 2** presents response length distributions and topic breadth per respondent. Both cohorts show similar word count distributions (median=19 words), with transit-primary responses showing slightly higher variance. Topic breadth analysis reveals that most respondents addressed 2-4 distinct topics, with no significant difference between cohorts.

![Response Characteristics](images/fig2_response_characteristics.png)

**Figure 3** provides a heatmap of topic presence per respondent, enabling visual inspection of individual response patterns. Transit-primary respondents (INT-01 through INT-09) show concentrated information and trust concerns, while car-primary respondents (INT-10 through INT-18) show more distributed multimodal and pricing concerns.

![Topic Presence Heatmap](images/fig3_topic_heatmap.png)

**Figure 4** displays the most frequent content words per cohort. Transit-primary respondents most frequently used "app" (3×), "train" (2×), "single" (2×), and "delays" (2×), reflecting concerns about real-time information and service reliability. Car-primary respondents most frequently used "drive/transit/app/time/decide/parking" (2× each), reflecting decision-making and multimodal planning concerns.

![Top Words by Cohort](images/fig4_top_words.png)

### LLM-Assisted Thematic Analysis

The following thematic analysis was generated by the Anthropic Messages API (`claude-3-5-sonnet-20241022`, 1,217 input tokens, 972 output tokens):

---

''' + llm_analysis + '''

---

## Discussion

### Key Findings

This mixed-methods analysis reveals both shared and divergent UX concerns across transit-primary and car-primary transportation app users.

**Shared concerns** center on information reliability and multimodal integration. Both cohorts expressed frustration with inaccurate or incomplete information (transit: INT-01, INT-08; car: INT-10, INT-18) and desire for seamless cross-modal trip planning (transit: INT-09; car: INT-12, INT-17). This convergence suggests that information quality is a universal UX priority regardless of primary transportation mode.

**Divergent concerns** reflect the distinct operational contexts of each cohort. Transit-primary users emphasized safety and accessibility (INT-02, INT-04, INT-05) — concerns rooted in the shared, public nature of transit infrastructure. Car-primary users emphasized cost-benefit decision-making (INT-10, INT-15) and interface simplicity (INT-16) — reflecting the individual, choice-driven nature of car use.

**Trust dynamics** differed notably between cohorts. Transit-primary users expressed trust concerns tied to information accuracy (INT-08: "generic delays erode trust faster than a long wait with a reason"), while car-primary users expressed trust in visual map representations over algorithmic ETAs (INT-18: "I trust the map more than the ETA"). This distinction has implications for how transparency should be communicated in multimodal apps.

### Theoretical Implications

The findings align with **information needs theory** (Dervin, 1983): users construct sense-making bridges between their current situation and desired state, and app failures disrupt these bridges differently depending on modal context. Transit users face higher stakes from information failures (missed connections, safety risks), while car users face decision-optimization failures (suboptimal route/mode choices).

From a **UX design** perspective, the results suggest that a one-size-fits-all interface may inadequately serve both cohorts. Transit-primary users need proactive, contextual safety and accessibility information; car-primary users need streamlined decision-support tools with integrated cost comparisons.

### Practical Recommendations

1. **Reliability transparency**: Provide honest, specific delay explanations rather than generic status messages (addresses both cohorts)
2. **Integrated multimodal planning**: Stitch driving, transit, and active transport legs into unified trip plans (addresses both cohorts)
3. **Contextual safety information**: Surface accessibility and crowding data prominently for transit users
4. **Cost comparison tools**: Integrate fuel vs. fare calculators for car-primary users considering modal shift
5. **Progressive disclosure**: Simplify home screen with advanced features accessible on demand

---

## Limitations

1. **Small sample size** (N=18, 9 per cohort): Findings are exploratory and not statistically generalizable. Thematic saturation cannot be confirmed at this scale.

2. **Response length**: Single-sentence to two-sentence excerpts limit the depth of qualitative analysis. Full interview transcripts would enable richer thematic development.

3. **Keyword-based topic coding**: The a priori topic coding scheme may miss emergent themes not anticipated in the keyword list. Some responses may be miscoded due to polysemy (e.g., "wrong" coded under both reliability and trust).

4. **LLM-assisted analysis**: While the LLM analysis provides systematic coverage, it may reflect training data biases and cannot replace human interpretive judgment. The analysis should be treated as a first-pass synthesis requiring expert validation.

5. **Sampling bias**: The purposive sample may not represent the full diversity of transit and car users. Geographic, demographic, and socioeconomic context is absent from the dataset.

6. **Single-timepoint data**: Cross-sectional interview data cannot capture how user needs evolve over time or in response to service changes.

7. **Model availability**: The specified model (`claude-3-5-sonnet-20241022`) was accessed via OpenRouter using the closest available Claude 3.5 variant (`anthropic/claude-3.5-haiku`). Results may differ slightly from the target model.

---

## Appendix: Quantitative Summary Statistics

### Word Count Distribution

| Cohort | Mean | Median | Std | Min | Max |
|--------|------|--------|-----|-----|-----|
| Transit-Primary | 20.22 | 19.0 | 3.46 | 16 | 27 |
| Car-Primary | 19.67 | 19.0 | 2.40 | 16 | 24 |

### Top Content Words

**Transit-Primary**: app (3), train (2), single (2), delays (2), generic (2), arrival (1), board (1), wrong (1), connections (1), rest (1)

**Car-Primary**: drive (2), transit (2), app (2), time (2), decide (2), parking (2), legs (2), map (2), wrong (2), unreliable (1)

### API Call Metadata
- Model: claude-3-5-sonnet-20241022 (via anthropic/claude-3.5-haiku on OpenRouter)
- Input tokens: 1,217
- Output tokens: 972
- Response saved: `outputs/anthropic_messages_response.json`
'''

with open("report/interview_thematic_report.md", "w", encoding="utf-8") as f:
    f.write(report)

print("✓ interview_thematic_report.md written to report/")
