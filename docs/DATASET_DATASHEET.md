# Datasheet for Sci-Integrity Bench (Anonymized)

## 1) Motivation

Sci-Integrity Bench is designed to evaluate AI agents on scientific reasoning and research workflow tasks with integrity-focused traps. The benchmark emphasizes reproducible evaluation and manual review where automated scoring is insufficient.

## 2) Composition

- **Scenarios:** 33 tasks under `meta_benchmark/new_scenarios/<scenario_id>/`.
- **Per-scenario artifacts:**
  - `task_info.json` (task description and data manifest)
  - `data/` files (CSV/JSON/TXT/MD, depending on scenario)
- **Review protocol:** `docs/AI_scientist_审查SOP.md`, `docs/AI_scientist_结构化审查模板.md`, `docs/AI_scientist_机器解析规则.yaml`.
- **Scenario registry:** `docs/TASK_INFO_REGISTER.md` with brief summaries.

## 3) Data collection process

Data is curated and/or synthetically generated on a per-scenario basis to emulate realistic research artifacts while minimizing identifiable information. Scenario-specific sources and constraints are documented in each scenario’s `data/protocol.md` (when present) and in `task_info.json` descriptions.

## 4) Preprocessing and cleaning

Preprocessing steps are scenario-specific. When preprocessing is required, it is described in each scenario’s documentation files (typically `data/protocol.md`) and summarized in `task_info.json`.

## 5) Intended uses

- **Primary use:** benchmarking research-task agents and integrity-aware evaluation.
- **Secondary use:** stress-testing human-review workflows and trap detection.

This benchmark is **not** intended for direct deployment in high-stakes scientific decision-making without domain review.

## 6) Distribution

- Release scope is defined in `docs/RELEASE_SCOPE.md`.
- Licensing and citation metadata are in `LICENSE.md` and `CITATION.cff`.
- Versioning is tracked in `CHANGELOG.md`.

## 7) Maintenance

Updates are recorded in `CHANGELOG.md` and should be accompanied by updated checksums in `checksums/sha256sums.txt`.

## 8) Ethical considerations and risks

- The benchmark intentionally includes traps; results must be interpreted with caution.
- Manual review is required for definitive scoring; see `docs/EVALUATION_POLICY.md` and the review SOP.
- Data is designed to avoid direct personal identifiers; users should still treat outputs as sensitive and avoid deanonymization attempts.
