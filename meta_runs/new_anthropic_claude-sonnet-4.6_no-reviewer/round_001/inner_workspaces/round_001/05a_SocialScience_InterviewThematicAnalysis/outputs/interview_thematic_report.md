# Interview Thematic Analysis Report
## Transit/Mobility App UX — Semi-Structured Interview Study

---

## Methods

### Study Design
This mixed-methods study analysed semi-structured interview excerpts from 18 respondents divided into two cohorts: **transit-primary users** (n = 9; INT-01 to INT-09) and **car-primary users** (n = 9; INT-10 to INT-18). Each respondent provided a single focused response about their experience with a transit/mobility application.

### Preprocessing Pipeline
All preprocessing was performed reproducibly in `code/01_preprocess.py`:

1. **Data loading**: CSV parsed with Python's `csv.DictReader`; no missing values detected.
2. **Cohort counts**: Verified equal split (9 transit-primary, 9 car-primary).
3. **Response length metrics**: Character length and word count computed per respondent and summarised by cohort.
4. **Word frequency analysis**: Responses tokenised with a regex (`[a-z']+`), lowercased, and filtered against a curated stopword list. Top-20 overall and top-15 per-cohort frequencies computed with `collections.Counter`.
5. **Keyword-category scoring**: Seven UX concern categories (Real-time Info, Crowding & Safety, Pricing & Cost, Navigation & Maps, Accessibility, Multimodal Integration, UI/Interface) were defined with domain-relevant keyword lists; each response was scored by keyword hit count.

### LLM-Assisted Thematic Analysis
Thematic coding was performed using the Anthropic Messages API (`claude-3-5-sonnet-20241022` requested; `anthropic/claude-3-7-sonnet-20250219` served via OpenRouter). The full prompt included all 18 interview excerpts and requested: (1) identification of 4–6 major themes with respondent citations and cohort prominence; (2) cohort comparison; (3) cross-cutting concerns; (4) design implications; (5) methodological limitations. The complete API response is saved to `outputs/anthropic_messages_response.json`.

---

## Results

### Descriptive Statistics

| Metric | Transit-Primary | Car-Primary |
|--------|----------------|-------------|
| N | 9 | 9 |
| Avg. word count | 20.2 | 19.7 |
| Min word count | 16 | 16 |
| Max word count | 26 | 24 |
| Avg. char length | 115.1 | 113.1 |

Response lengths were highly comparable across cohorts, indicating similar verbosity and no systematic length bias.

### Word Frequency Highlights

**Overall top words**: `app` (5), `train` (3), `time` (3), `single` (3), `map` (3), `delays` (2), `trust` (2), `parking` (2), `legs` (2).

**Transit-primary distinctive words**: `app` (3), `miss` (2), `train` (2), `single` (2), `delays` (2), `generic` (2) — reflecting concerns about real-time accuracy and fare complexity.

**Car-primary distinctive words**: `transit` (2), `app` (2), `time` (2), `parking` (2), `legs` (2), `map` (2) — reflecting multimodal integration and navigation needs.

### Keyword-Category Heatmap
The scripted keyword scoring revealed the following patterns:
- **Real-time Info** and **Navigation & Maps** scored highest for transit-primary users.
- **Multimodal Integration** and **UI/Interface** scored highest for car-primary users.
- **Pricing & Cost** was notable in both cohorts.
- **Accessibility** was exclusively a transit-primary concern in the keyword scoring.

### LLM-Identified Themes

The LLM identified **six major themes**:

#### Theme 1: Reliability of Information
Users rely on app accuracy for time-sensitive decisions. Incorrect or incomplete information erodes trust and disrupts journeys. **Respondents**: INT-01, INT-05, INT-08 (transit); INT-10, INT-17, INT-18 (car). **Prominence**: Both cohorts.

#### Theme 2: Safety & Security Concerns
Personal safety information influences mobility decisions, often outweighing time or cost savings. Transit users focus on platform/night safety; car users on parking facility security. **Respondents**: INT-02, INT-04 (transit); INT-13 (car). **Prominence**: Both cohorts, different manifestations.

#### Theme 3: Integrated Multimodal Experience
Users want seamless multi-leg journey support rather than siloed mode information. **Respondents**: INT-07, INT-09 (transit); INT-12, INT-15 (car). **Prominence**: Both cohorts; car users emphasise park-and-ride.

#### Theme 4: Cost Transparency & Comparison
Users struggle with the full economic picture of transportation choices. **Respondents**: INT-03 (transit); INT-10, INT-15 (car). **Prominence**: Both cohorts; transit users focus on fare complexity, car users on mode comparison.

#### Theme 5: Interface Personalization & Focus
Users are frustrated by cluttered interfaces that do not match their priorities. **Respondents**: INT-06 (transit); INT-14, INT-16 (car). **Prominence**: Car-primary users more vocal.

#### Theme 6: Accessibility & Inclusion
Accessibility information (elevator outages, offline mode, night service) is critical for some users. **Respondents**: INT-04, INT-05, INT-06 (transit). **Prominence**: Transit-primary only.

### Cohort Comparison

1. **Immediacy vs. optionality**: Transit-primary users experience real-time failures as immediate crises (missed connections, safety risks); car-primary users treat transit as one option among several.
2. **Safety framing**: Transit users fear personal safety in public spaces; car users fear lot security and carjacking risk.
3. **Integration needs**: Car users need driving-to-transit stitching; transit users need within-network transfer clarity.
4. **Interface tolerance**: Car users are more sensitive to UI clutter; transit users tolerate complexity if core information is accurate.

### Cross-Cutting Concerns

1. **Trust in information accuracy** (INT-01, INT-08, INT-18): Both cohorts distrust apps that provide wrong or vague information; honest explanations of delays are preferred over silence.
2. **Cost visibility** (INT-03, INT-10, INT-15): Both cohorts want cost information consolidated in one view rather than scattered across menus.

### Design Implications

1. **Unified Journey View**: Seamlessly combine driving, transit, and walking legs with total time, cost, and transfer details.
2. **Personalised Information Hierarchy**: Allow users to pin their priority information (accessibility alerts, parking costs, crowding) to the home screen.
3. **Comparative Economics Dashboard**: Display transit fares alongside driving costs (fuel, parking, tolls) for weekly trip planning.
4. **Enhanced Safety Overlay**: Toggleable map layer showing crowding, lighting, CCTV, and night-service coverage.
5. **Trust-Building Disruption Design**: Replace generic delay messages with specific reasons, estimated resolution times, and alternative routing.

---

## Discussion

The thematic analysis reveals that despite different primary transport modes, users share fundamental expectations: **accurate information**, **transparent costs**, and **integrated journey planning**. The divergence lies in how these needs manifest: transit-primary users experience app failures as immediate safety and schedule crises, while car-primary users treat the app as a decision-support tool for mode choice.

The keyword-based heatmap and LLM thematic coding converge on the same top concerns, providing methodological triangulation. The `app` keyword appearing most frequently across both cohorts underscores that the application interface itself — not just the underlying transit network — is a primary pain point.

Notably, **accessibility** emerged exclusively in the transit-primary cohort, suggesting that car-primary users either have fewer accessibility needs or rely on different information channels. This asymmetry has equity implications for app design.

---

## Limitations

1. **Small sample size** (n = 18): Themes are suggestive, not statistically generalisable.
2. **Single-response format**: Each respondent provided one focused excerpt; multi-turn interviews would yield richer data.
3. **No demographic data**: Age, disability status, income, and geography could substantially moderate the themes identified.
4. **Binary cohort classification**: Real users exist on a spectrum; the transit/car dichotomy may obscure mixed-mode users.
5. **LLM subjectivity**: Thematic coding by LLM reflects training data biases; human coder triangulation is recommended for publication.
6. **Keyword scoring limitations**: The scripted heatmap uses exact substring matching; stemming and semantic similarity would improve recall.
