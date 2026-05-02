# Anonymized Submission Bundle

This checklist describes how to prepare a double-blind release bundle while keeping a full (named) version for camera-ready.

## 1) Bundle layout (example)

```
anonymized_bundle/
  README.md
  docs/
  meta_benchmark/new_scenarios/
  checksums/sha256sums.txt
  LICENSE.md
  CITATION.cff
  CHANGELOG.md
```

## 2) Build steps

1. Start from the **release scope** in `docs/RELEASE_SCOPE.md` and copy only those paths into a new bundle directory.
2. Sanitize the top-level `README.md` and any docs that may contain author/affiliation/project identifiers.
3. Remove git history (`.git/`) and any external links that identify the authors or institutions.
4. Remove private materials listed in `docs/RELEASE_SCOPE.md` (e.g., `_authoring_private/`, `meta_runs/`, reviewer registry).
5. Verify the checksum manifest in `checksums/sha256sums.txt` after the bundle is finalized.

## 3) Redaction checklist

- [ ] No author names, lab names, or institution names appear in README or docs.
- [ ] No personal emails or project URLs are present.
- [ ] `CITATION.cff` and `LICENSE.md` use **"Anonymous Authors"**.
- [ ] File names, figure captions, and PDF metadata are anonymized.
- [ ] References to internal infrastructure (private repos, issue trackers) are removed.
- [ ] Only release-scope files are included.

## 4) Camera-ready version

Keep the full, named version on a private branch. After acceptance, update `LICENSE.md`, `CITATION.cff`, and any anonymized references with the final author and affiliation information.
