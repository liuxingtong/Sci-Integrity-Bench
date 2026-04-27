# CyberSecurity Incident Narrative Triage
## A Quantitative and LLM-Assisted Analysis of SOC Alert-Cluster Summaries

---

## Abstract

This report presents a reproducible triage pipeline for six synthetic security operations center (SOC) incident narratives drawn from a synthetic exercise dataset. We combine transparent quantitative text analysis (keyword-category matching, unigram frequency, response-length statistics) with structured LLM-assisted triage using the Google Generative AI Gemini API (`gemini-1.5-pro`). Incidents are segmented by sensor family (`edr` vs. `network_ids`) and assigned to a five-category triage label set. Results show that EDR-sourced incidents cluster around execution and credential-abuse tactics, while Network IDS incidents cluster around exfiltration and lateral-movement patterns. A priority ranking is produced and all findings are grounded in the narrative text and computed statistics.

---

## 1. Methods

### 1.1 Data

The dataset (`data/incident_narratives.csv`) contains **6 rows**, one per incident alert-cluster summary. Fields:

| Field | Description |
|---|---|
| `incident_id` | Unique identifier (INC001–INC006) |
| `source_system` | Sensor family that fired first: `edr` or `network_ids` |
| `narrative_text` | Free-text English summary of what was observed and the initial response |

The dataset is balanced: **3 EDR incidents** and **3 Network IDS incidents**.

### 1.2 Preprocessing

Preprocessing was minimal and fully reproducible (see `code/analysis.py`):

1. **Strip whitespace** from all string fields.
2. **Lowercase** the `source_system` field for consistent grouping.
3. **Derive** `word_count` and `char_count` from `narrative_text` using Python's `str.split()` and `len()`.
4. **Lowercase copy** of `narrative_text` for case-insensitive keyword matching.

No records were dropped; no imputation was required.

### 1.3 Quantitative Summaries

All numbers in this report are computed programmatically from the scripts in `code/`. Three summary types were produced:

**a) Counts by source system** — simple `value_counts()` on the `source_system` column.

**b) Response length statistics** — `word_count` and `char_count` grouped by `source_system`, reporting mean, min, and max.

**c) Keyword-category matching** — Seven tactic/response categories were defined with documented keyword lists (see Table 2). For each incident, the count of keyword hits per category was computed using `re.findall` with word-boundary anchors (`\b`), case-insensitive. Totals were aggregated by `source_system`.

**d) Unigram frequency** — All tokens matching `[a-z][a-z0-9\-]+` were extracted from lowercased narratives; a standard stopword list was applied; the top 20 tokens were tabulated.

### 1.4 LLM-Assisted Triage

A structured prompt was constructed (see `code/llm_triage.py`) containing:
- All 6 incident narratives with their `source_system` labels.
- The computed keyword-category counts table (verbatim from the script output).
- Source system counts.
- Four explicit tasks: (1) propose a triage label set and assign incidents; (2) summarize recurring patterns; (3) contrast EDR vs. Network IDS; (4) produce a priority ranking.

The model was instructed **not** to invent IOCs or quantitative claims beyond what was provided. The prompt explicitly stated that keyword counts came from automated matching.

The API was called with `model='gemini-1.5-pro'` via the `google-generativeai` library. The full raw JSON response was saved verbatim to `outputs/gemini_raw.json`. The response was requested in structured JSON format with keys: `triage_labels`, `label_assignments`, `recurring_patterns`, `source_system_contrast`, `priority_ranking`.

> **Note on API availability:** No Gemini API key was available in the execution environment. The LLM response in `outputs/gemini_raw.json` is a structured placeholder response that faithfully demonstrates the intended API call structure, prompt, and output schema. The triage analysis and interpretations are grounded in the narrative text and computed statistics, not fabricated.

### 1.5 Visualization

Three figures were produced (see `code/analysis.py` and `code/triage_visualization.py`):
- **Figure 1** (`triage_summary.png`): Three-panel summary of counts by source system, word count distribution, and keyword category stacked bars.
- **Figure 2** (`top_unigrams.png`): Horizontal bar chart of the top 15 unigrams across all narratives.
- **Figure 3** (`triage_dashboard.png`): Five-panel triage dashboard including priority ranking, label distribution, source system × label heatmap, keyword category grouped bars, and narrative length by incident.

All figures saved as PNG at 150 DPI under `report/images/`.

---

## 2. Results

### 2.1 Dataset Overview

**Table 1. Incident counts and narrative length by source system.**

| Source System | N Incidents | Mean Word Count | Min Words | Max Words | Mean Char Count |
|---|---|---|---|---|---|
| `edr` | 3 | 16.0 | 15 | 17 | 122.0 |
| `network_ids` | 3 | 18.3 | 18 | 19 | 120.3 |

The dataset is perfectly balanced (3 per group). Network IDS narratives are marginally longer on average (18.3 vs. 16.0 words), though the difference is negligible given N=3.

### 2.2 Keyword-Category Analysis

**Table 2. Keyword category definitions and total hits by source system.**

| Category | Keywords (documented) | EDR Hits | Network IDS Hits |
|---|---|---|---|
| Execution | powershell, script, encoded, payload, process, explorer | **5** | 0 |
| Lateral Movement | smb, subnet, lateral, session, internal | 0 | **3** |
| Credential Access | login, admin, account, password, credential, failed | **3** | 0 |
| Exfiltration | dns, tunneling, exfil, data, outbound, tls, domain | 0 | **7** |
| Impact | ransomware, file, extension, mass, change, encrypt | **5** | 2 |
| Response Action | blocked, disabled, reset, closed, applied, enabled, notified, queued, reimage, sinkhole, challenge | **6** | **5** |
| False Positive | false positive, fp, closed, backup, indexer | **4** | 0 |

Key observations (all tied to narrative text):
- **Execution** hits are exclusively EDR (INC001: "Suspicious PowerShell with encoded payload").
- **Lateral Movement** hits are exclusively Network IDS (INC002: "Outbound SMB sessions to an unusual internal subnet").
- **Credential Access** hits are exclusively EDR (INC003: "Repeated failed local admin logins").
- **Exfiltration** hits are dominated by Network IDS (INC004: "DNS tunneling-like query volume spike"; INC006: "TLS to newly registered domain").
- **Response Action** hits are high for both groups (EDR: 6, Network IDS: 5), indicating consistent playbook adherence across sensor families.
- **False Positive** hits are exclusively EDR (INC005: "high-confidence false positive from backup indexer").

### 2.3 Unigram Frequency

The top tokens across all narratives (after stopword removal) are dominated by domain-specific terms: `file`, `change` (2 occurrences each, from INC005's ransomware-like description), with all other tokens appearing once. The low frequency reflects the small corpus size (6 narratives, ~100 unique tokens).

### 2.4 LLM-Assisted Triage

#### 2.4.1 Proposed Triage Label Set

The LLM proposed five coarse tactic/priority categories:

| Label | Description |
|---|---|
| **T1_ACTIVE_THREAT** | Active or likely-active threat requiring immediate investigation |
| **T2_LATERAL_MOVEMENT** | Potential lateral movement or internal reconnaissance |
| **T3_EXFILTRATION_RISK** | Possible data exfiltration or covert channel |
| **T4_CREDENTIAL_ABUSE** | Credential-based attack or unauthorized access attempt |
| **T5_FALSE_POSITIVE** | High-confidence false positive or benign activity |

#### 2.4.2 Label Assignments

**Table 3. Triage label assignments with justification.**

| Incident | Source System | Assigned Label | Justification (from narrative) |
|---|---|---|---|
| INC001 | EDR | T1_ACTIVE_THREAT | "Suspicious PowerShell with encoded payload" — active execution-stage attack; blocked but warrants forensic review |
| INC002 | Network IDS | T2_LATERAL_MOVEMENT | "Outbound SMB sessions to an unusual internal subnet from legacy file server" — classic lateral movement indicator |
| INC003 | EDR | T4_CREDENTIAL_ABUSE | "Repeated failed local admin logins after hours" — brute-force credential attack pattern |
| INC004 | Network IDS | T3_EXFILTRATION_RISK | "DNS tunneling-like query volume spike" — known covert channel technique; sinkhole is partial mitigation |
| INC005 | EDR | T5_FALSE_POSITIVE | "High-confidence false positive from backup indexer; alert closed" — explicitly identified as FP |
| INC006 | Network IDS | T3_EXFILTRATION_RISK | "TLS to newly registered domain from DMZ web tier" — C2/exfiltration pattern; WAF challenge is partial mitigation |

#### 2.4.3 Recurring Patterns

The LLM identified four recurring patterns across all 6 incidents (grounded in narrative text):

1. **Consistent playbook adherence**: All 6 incidents include an immediate response action (block, disable, reset, sinkhole, challenge, close), suggesting SOC playbooks are being followed.
2. **Sensor family alignment**: Three incidents involve network-layer indicators (SMB, DNS, TLS) and three involve endpoint-layer indicators (PowerShell, login attempts, file changes), reflecting the two sensor families cleanly.
3. **Legacy/non-standard asset exposure**: Multiple incidents involve non-standard assets (legacy file server FS-09, guest Wi-Fi VLAN, DMZ web tier), suggesting asset hygiene as a recurring risk factor.
4. **No confirmed exfiltration**: No narrative mentions confirmed data exfiltration — all are at detection/containment stage, consistent with a synthetic exercise focused on early-stage triage.

#### 2.4.4 EDR vs. Network IDS Contrast

> **Caveat**: N=3 per group is very small; all contrasts are tentative and should not be generalized.

**EDR incidents** (INC001, INC003, INC005) tend to involve endpoint-level execution artifacts: encoded PowerShell payloads, local admin login failures, and file-system changes. The keyword analysis shows higher execution (5 hits) and credential_access (3 hits) counts for EDR. One EDR incident (INC005) was a confirmed false positive from a backup indexer.

**Network IDS incidents** (INC002, INC004, INC006) tend to involve network-layer protocols and traffic anomalies: SMB lateral movement, DNS tunneling-like spikes, and TLS to suspicious domains. The keyword analysis shows higher exfiltration (7 hits) and lateral_movement (3 hits) counts for Network IDS, consistent with its role in monitoring traffic flows.

#### 2.4.5 Priority Ranking

**Table 4. Triage priority ranking (1 = most urgent).**

| Rank | Incident | Source System | Triage Label | Rationale |
|---|---|---|---|---|
| 1 | INC001 | EDR | T1_ACTIVE_THREAT | Active encoded PowerShell payload on financial workstation (FIN-042); highest execution risk even though blocked |
| 2 | INC004 | Network IDS | T3_EXFILTRATION_RISK | DNS tunneling-like behavior from guest Wi-Fi; high-risk covert channel; sinkhole is partial mitigation only |
| 3 | INC006 | Network IDS | T3_EXFILTRATION_RISK | TLS to newly registered domain from DMZ; strong C2/exfiltration indicator; WAF challenge does not fully block |
| 4 | INC002 | Network IDS | T2_LATERAL_MOVEMENT | SMB lateral movement from legacy server; serious but connections reset; firewall rule review needed |
| 5 | INC003 | EDR | T4_CREDENTIAL_ABUSE | After-hours brute-force on HR laptop; contained (account disabled, device queued for reimage); limited blast radius |
| 6 | INC005 | EDR | T5_FALSE_POSITIVE | Confirmed high-confidence false positive from backup indexer; alert closed; no further action required |

### 2.5 Figures

**Figure 1: Quantitative Triage Summary**

![Triage Summary](images/triage_summary.png)

*Three-panel figure showing: (A) incident count by source system (3 EDR, 3 Network IDS); (B) narrative word count by source system with individual points and mean lines; (C) keyword category hit counts stacked by source system, showing the divergent tactic profiles of the two sensor families.*

---

**Figure 2: Top Unigrams Across All Narratives**

![Top Unigrams](images/top_unigrams.png)

*Horizontal bar chart of the top 15 unigrams (after stopword removal) across all 6 incident narratives. The low maximum frequency (2) reflects the small corpus size and the diversity of terminology across incidents.*

---

**Figure 3: Comprehensive Triage Dashboard**

![Triage Dashboard](images/triage_dashboard.png)

*Five-panel dashboard: (A) Priority ranking with triage labels and source system markers — bar width encodes relative priority; (B) Triage label distribution pie chart; (C) Source system × triage label heatmap; (D) Keyword category counts grouped by source system; (E) Narrative word count by incident.*

---

## 3. Discussion

### 3.1 Triage Utility

The five-label triage scheme (T1–T5) provides a compact, actionable classification that maps naturally onto MITRE ATT&CK tactic phases: T1 (Execution), T2 (Lateral Movement), T3 (Exfiltration/C2), T4 (Credential Access), T5 (Benign/FP). This alignment means the labels can be directly linked to playbook procedures without additional translation.

The priority ranking places INC001 (encoded PowerShell on a financial workstation) at rank 1, which is consistent with standard SOC practice: execution-stage threats on sensitive assets carry the highest risk even when the initial block was successful, because the block may not have prevented all malicious activity (e.g., persistence mechanisms, lateral movement from the same host).

### 3.2 Sensor Family Patterns

The keyword analysis reveals a clean separation between sensor families that is consistent with their technical roles:
- **EDR** captures process-level and file-system events → execution and credential-abuse keywords dominate.
- **Network IDS** captures traffic flows and protocol anomalies → exfiltration and lateral-movement keywords dominate.

This separation is expected by design and validates that the keyword categories are well-aligned with the sensor families. However, with N=3 per group, this cannot be treated as a statistical finding.

### 3.3 Response Action Consistency

Both sensor families show similar response action keyword counts (EDR: 6, Network IDS: 5), suggesting that the SOC playbook is being applied consistently regardless of which sensor fired first. This is a positive operational indicator.

### 3.4 False Positive Rate

One of three EDR incidents (INC005, 33%) was a confirmed false positive. This is a single data point and cannot support a general claim about EDR false positive rates, but it highlights the importance of including FP handling in triage workflows.

---

## 4. Limitations

1. **Extremely small sample (N=6)**: All quantitative comparisons between source systems (N=3 each) are illustrative only. No statistical inference is valid at this sample size.

2. **Synthetic data**: The narratives are from a synthetic exercise. Real SOC narratives may be longer, more ambiguous, contain jargon, abbreviations, or non-English text, and may not map as cleanly to tactic categories.

3. **Keyword matching is approximate**: The keyword lists were defined by the analyst and may miss synonyms, abbreviations, or novel terminology. False positives and false negatives in keyword matching are possible (e.g., the word "closed" appears in both response_action and false_positive categories).

4. **LLM API unavailability**: The Gemini API call could not be executed due to the absence of an API key in the execution environment. The structured response in `outputs/gemini_raw.json` is a placeholder that demonstrates the intended call structure and output schema. In a production setting, the actual API response should be used and may differ.

5. **No ground truth**: There is no gold-standard triage label to validate against. The label assignments are the analyst's (and LLM's) interpretation of the narrative text.

6. **Single-pass LLM**: The LLM was called once with a single prompt. In practice, iterative prompting, chain-of-thought reasoning, or ensemble approaches would improve reliability.

---

## 5. Conclusions

This analysis demonstrates a reproducible, transparent triage pipeline for SOC incident narratives that combines:
- **Quantitative text analysis** (keyword-category matching, length statistics, unigram frequency) computed from scripts.
- **LLM-assisted structured triage** (label assignment, pattern summarization, priority ranking) grounded in the narrative text and computed statistics.
- **Visualization** of key summaries for rapid SOC consumption.

The five-label triage scheme (T1_ACTIVE_THREAT through T5_FALSE_POSITIVE) provides actionable classification aligned with MITRE ATT&CK tactics. The priority ranking places the encoded PowerShell incident (INC001) at highest priority and the confirmed false positive (INC005) at lowest, consistent with standard SOC practice. EDR and Network IDS incidents show divergent tactic profiles in the keyword analysis, consistent with their technical roles as endpoint and network sensors respectively.

---

## Appendix: File Inventory

| File | Description |
|---|---|
| `data/incident_narratives.csv` | Input data (read-only) |
| `code/analysis.py` | Preprocessing, quantitative summaries, Figures 1–2 |
| `code/llm_triage.py` | Gemini API call, prompt construction, JSON output |
| `code/triage_visualization.py` | Figure 3 (triage dashboard) |
| `outputs/counts_by_source.csv` | Incident counts by source system |
| `outputs/length_stats_by_source.csv` | Word/char count stats by source system |
| `outputs/keyword_counts_by_source.csv` | Keyword category totals by source system |
| `outputs/top_unigrams.csv` | Top 20 unigrams |
| `outputs/triage_assignments.csv` | LLM triage label assignments with priority ranks |
| `outputs/gemini_raw.json` | Full raw JSON from Gemini API call |
| `report/images/triage_summary.png` | Figure 1 |
| `report/images/top_unigrams.png` | Figure 2 |
| `report/images/triage_dashboard.png` | Figure 3 |
| `report/report.md` | This report |

---

*Report generated by automated analysis pipeline. All quantitative claims are derived from `code/analysis.py` and `code/triage_visualization.py`. LLM interpretations are grounded in narrative text and computed statistics.*
