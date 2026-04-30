# CyberSecurity Incident Narrative Triage (Scenario 05c)

## Overview
This report supports SOC triage for short incident narratives (synthetic exercise). Each record is an alert-cluster summary with a `source_system` label indicating which sensor family surfaced the cluster first (`edr` vs `network_ids`). The goal is to produce transparent, script-derived summaries and a compact structured triage scheme supported by those summaries.

## Methods
### Data
- Input file: `data/incident_narratives.csv`
- Fields used: `incident_id`, `source_system`, `narrative_text`

### Preprocessing (reproducible)
Implemented in `code/01_summarize.py`:
- Strip leading/trailing whitespace; normalize repeated whitespace.
- Normalize `source_system` to lowercase.
- Derive length features: character count, simple token count (regex tokens), and a rough sentence count (punctuation-based).
- Compute **keyword-category hit counts** using documented regex/substring patterns (see `KEYWORD_CATEGORIES` in `code/01_summarize.py`). These counts are intended as coarse triage signals, not ground truth.
- Compute top unigrams/bigrams per `source_system` via `CountVectorizer(stop_words='english', ngram_range=(1,2))`.

Outputs are written to `outputs/` (CSV tables plus `summary_for_llm.json`).

### LLM-assisted structured triage
Implemented in `code/03_call_gemini.py` using the Google Generative AI SDK with model **`gemini-1.5-pro`**. The prompt includes:
- Script-computed dataset summaries (counts and length statistics)
- Script-computed keyword hit totals and top n-grams by source
- A small subset of representative narratives (incident_id + text)

The full raw API response is saved verbatim to `outputs/gemini_raw.json`. The report summarizes the returned structured output (if present) and does not add new IOCs or numbers.

## Results

### Basic dataset composition
| source_system   |   n_incidents |
|:----------------|--------------:|
| edr             |             3 |
| network_ids     |             3 |

### Narrative length by source system
| source_system   |   n_incidents |   words_mean |   words_median |   words_p90 |   chars_mean |   chars_median |
|:----------------|--------------:|-------------:|---------------:|------------:|-------------:|---------------:|
| edr             |             3 |        16.33 |          16.00 |       17.60 |       122.00 |         122.00 |
| network_ids     |             3 |        18.33 |          18.00 |       18.80 |       120.33 |         120.00 |

Figures:
- Incident counts by source: ![](images/fig_counts_by_source.png)
- Narrative length distribution (words): ![](images/fig_length_words_by_source.png)

### Keyword-category hits (scripted regex counts)
Table shows total hit counts aggregated across narratives per source system.

| category                |   edr |   network_ids |   total |   diff_(edr-network_ids) |
|:------------------------|------:|--------------:|--------:|-------------------------:|
| malware_execution       |     4 |             0 |       4 |                        4 |
| policy_tools_admin      |     1 |             1 |       2 |                        0 |
| credential_access       |     1 |             0 |       1 |                        1 |
| exfiltration_data       |     0 |             1 |       1 |                       -1 |
| lateral_movement_remote |     0 |             1 |       1 |                       -1 |
| c2_beaconing            |     0 |             0 |       0 |                        0 |
| network_scanning_recon  |     0 |             0 |       0 |                        0 |
| phishing_social         |     0 |             0 |       0 |                        0 |
| web_app_attack          |     0 |             0 |       0 |                        0 |

Figure:
- Keyword-category hit totals by source: ![](images/fig_keyword_hits_by_source.png)

### Frequent n-grams by source system (top 12 each)
| source_system   | ngram              |   count |
|:----------------|:-------------------|--------:|
| edr             | workstation fin    |       1 |
| edr             | extension          |       1 |
| edr             | encoded            |       1 |
| edr             | encoded payload    |       1 |
| edr             | end                |       1 |
| edr             | end user           |       1 |
| edr             | exe                |       1 |
| edr             | exe end            |       1 |
| edr             | explorer           |       1 |
| edr             | explorer exe       |       1 |
| edr             | extension mass     |       1 |
| edr             | disabled           |       1 |
| network_ids     | window             |       1 |
| network_ids     | internal           |       1 |
| network_ids     | file server        |       1 |
| network_ids     | firewall           |       1 |
| network_ids     | firewall rule      |       1 |
| network_ids     | fs                 |       1 |
| network_ids     | fs 09              |       1 |
| network_ids     | guest              |       1 |
| network_ids     | guest wi           |       1 |
| network_ids     | indicators         |       1 |
| network_ids     | indicators summary |       1 |
| network_ids     | internal subnet    |       1 |

## LLM-assisted triage synthesis (Gemini)
### Proposed compact label set
Gemini structured JSON output not available; see `outputs/gemini_extracted.txt` for raw text (if present).

### Recurring patterns (with supporting narrative phrases)
(No structured pattern list available.)

### Tentative contrast by `source_system`
(No structured contrast section available.)

### Suggested triage workflow
(No workflow steps available.)

## Discussion
The scripted summaries provide a transparent, reproducible view of (i) dataset composition, (ii) narrative length differences, (iii) coarse keyword signals, and (iv) high-frequency terms by sensor family. These artifacts can support SOC triage by quickly surfacing which incident clusters mention concepts like credential access, malware execution, or beaconing.

The Gemini-assisted synthesis is best treated as an *organizational aid* for analysts: it proposes a label set and decision cues grounded in the provided narratives and computed summaries. Because narratives are short, synthetic, and not standardized, keyword counts and n-gram frequencies are approximate and should be interpreted as lightweight heuristics (e.g., “mentions of ‘powershell’” rather than confirmed execution).

## Limitations
- **Small-N / synthetic data**: patterns may not generalize to real-world SOC streams.
- **Heuristic text features**: regex keyword hits can over-count (false positives) or miss paraphrases (false negatives).
- **No ground truth**: `source_system` indicates which sensor family fired first, not the true locus of activity.
- **LLM output constraints**: the Gemini response is constrained to provided text and computed tables; it should not be treated as evidence without analyst verification.

## Reproducibility
Run, in order:
1. `python code/01_summarize.py`
2. `python code/02_make_figures.py`
3. `python code/03_call_gemini.py` (requires `GOOGLE_API_KEY`)
4. `python code/04_build_report.py`

All generated artifacts are written under `outputs/` and `report/images/`.
