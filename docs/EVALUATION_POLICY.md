# Evaluation and Submission Policy (Manual Review)

Sci-Integrity Bench requires **manual review** for definitive scoring. This document defines how submissions are evaluated and what to include.

## 1) Evaluation stages

1. **Automated checks:** file presence, basic format validation, and runtime metadata.
2. **Human review:** reviewers follow `docs/AI_scientist_审查SOP.md` and fill `docs/AI_scientist_结构化审查模板.md`.
3. **Adjudication:** disagreements are resolved by a lead reviewer (see SOP).

## 2) Submission materials

For each scenario, include:

- Model report (e.g., `report/report.md` or equivalent).
- Trace/logs (`trace.json`) and summary (`run_summary.json`) if available.
- Reproduction notes (model name, configuration, and any post-processing).

## 3) Public dev set vs hidden test set

- **Public dev set:** `meta_benchmark/new_scenarios/` is the public development set.
- **Hidden test set:** reserved for final evaluation or audit; results are scored via the same human-review protocol.

## 4) Manual review cost reporting

Each release should report:

- Number of reviewers and total review hours.
- Review coverage rate (e.g., full review vs sampled audit).
- Inter-annotator agreement (IAA) and adjudication rate.

These statistics should appear in the paper (see `docs/PAPER_ALIGNMENT.md`) or release notes.
