# Dataset Format and Versioning

## 1) Directory layout

```
meta_benchmark/new_scenarios/
  <scenario_id>/
    task_info.json
    data/
      ...
```

Scenario summaries live in `docs/TASK_INFO_REGISTER.md`.

## 2) `task_info.json` schema (per scenario)

```json
{
  "task": "Research Task\n\nTask Description...",
  "data": [
    {
      "name": "benchmark_registry",
      "path": "./data/benchmark_registry.json",
      "type": "metadata",
      "description": "..."
    }
  ]
}
```

Field definitions:

- `task` (string): full task prompt shown to the agent.
- `data` (array): list of data artifacts.
  - `name` (string): short identifier.
  - `path` (string): relative path from scenario root.
  - `type` (string): `metadata | documentation | feature_data | sequence_data`.
  - `description` (string): human-readable summary.

## 3) Data file types

- **feature_data**: structured tables, typically CSV.
- **sequence_data**: free-form text logs or sequences.
- **metadata**: JSON or CSV registries.
- **documentation**: markdown protocol notes or instructions.

## 4) Versioning

- Release versions are recorded in `CHANGELOG.md` and `CITATION.cff`.
- Any regeneration of data must update the version and checksum manifest.

## 5) Checksums

`checksums/sha256sums.txt` records SHA-256 hashes for release-scope files.

Regenerate from the repo root using standard tooling:

```
find meta_benchmark/new_scenarios -type f ! -path "*/__pycache__/*" ! -name "*.pyc" ! -name ".DS_Store" | sort | xargs sha256sum > checksums/sha256sums.txt
```

If additional release-scope files are added (docs, protocol files), append their hashes to the same file or regenerate a full manifest.

## 6) Immutable vs regenerable artifacts

- **Immutable for a release:** `task_info.json` and all `data/` files under each scenario.
- **Regenerable assets:** some datasets are produced by scripts such as `meta_benchmark/new_scenarios/_gen_*.py`. If regenerated, treat as a new release and update the checksums.
