# Release Scope (Anonymized Submission)

This document defines what belongs to the **benchmark dataset** versus **tooling** and **private author materials** for double-blind submission.

## 1) Benchmark dataset (included in anonymized bundle)

- `meta_benchmark/new_scenarios/**` (each `scenario_id/` contains `task_info.json` and `data/` files)
- `docs/TASK_INFO_REGISTER.md`
- `docs/_task_register_summaries_en.json`
- `docs/_scenario_register_titles.json`
- Review protocol docs:
  - `docs/AI_scientist_审查SOP.md`
  - `docs/AI_scientist_结构化审查模板.md`
  - `docs/AI_scientist_机器解析规则.yaml`
- Benchmark release docs:
  - `docs/DATASET_DATASHEET.md`
  - `docs/DATASET_FORMAT.md`
  - `docs/EVALUATION_POLICY.md`
  - `docs/BASELINE_RESULTS.md`
  - `docs/PAPER_ALIGNMENT.md`
  - `docs/ANONYMIZED_SUBMISSION.md`
- Release metadata:
  - `LICENSE.md`
  - `CITATION.cff`
  - `CHANGELOG.md`
  - `checksums/sha256sums.txt`

## 2) Tooling (shared for reproducibility, not part of the dataset)

- `meta_benchmark/run_new_scenarios.py`, `meta_benchmark/run_single_scenario.py`
- `meta_benchmark/inner_tool.py`, `meta_benchmark/fabrication_detector.py`
- `tier_benchmark/**` (runner, prompts, monitoring)
- `scripts/parse_human_review.py`, `scripts/init_human_reviews.py`
- `tools/**` (authoring utilities and generators)

## 3) Private / author-only materials (exclude from anonymized bundle)

- `meta_benchmark/_authoring_private/**` (author checklists and trap design)
- `meta_runs/**` (model outputs, human review files, internal logs)
- `docs/AI_scientist_审题人登记表.xlsx` and `docs/AI_scientist_审题人登记表.md` (reviewer identity)
- Local configs and caches: `.env`, `.vscode/`, `__pycache__/`, `.DS_Store`

## 4) Authorship note

Double-blind release uses **"Anonymous Authors"** in `LICENSE.md` and `CITATION.cff`. Update author names in the camera-ready version.
