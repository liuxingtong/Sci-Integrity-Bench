# -*- coding: utf-8 -*-
"""Museum provenance export merge + time distribution analysis.

Reads two batch exports, standardizes fields, deduplicates, and produces
collection-level time distribution summaries and figures.

Outputs:
- outputs/merged_long.csv: concatenated raw-ish rows with standardized columns
- outputs/dedup_catalog.csv: one row per deduplicated object
- outputs/dedup_clusters.jsonl: cluster membership diagnostic
- report/images/*.png: plots for report

Reproducible: deterministic random seeds where used.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd

# plotting
import matplotlib.pyplot as plt
import seaborn as sns

# try fast fuzzy matching; fall back to stdlib
try:
    from rapidfuzz import fuzz
except Exception:  # pragma: no cover
    fuzz = None
    import difflib


DATA_A = Path("data/museum_export_a.csv")
DATA_B = Path("data/museum_export_b.csv")
OUT_DIR = Path("outputs")
IMG_DIR = Path("report/images")


def _norm_str(x: object) -> str:
    if pd.isna(x):
        return ""
    s = str(x)
    s = s.strip()
    s = re.sub(r"\s+", " ", s)
    return s


def _norm_key(x: object) -> str:
    """Normalize ID-like keys (accession/inventory numbers)."""
    s = _norm_str(x).upper()
    # remove common separators but keep meaningful ones like '.'
    s = re.sub(r"[\u2010\u2011\u2012\u2013\u2014]", "-", s)  # dashes
    s = s.replace(" ", "")
    return s


def _norm_text_for_match(x: object) -> str:
    s = _norm_str(x).lower()
    s = s.replace("&", " and ")
    # keep digits/letters, drop other punctuation
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


YEAR_RE = re.compile(r"(?<!\d)(-?\d{1,4})(?!\d)")


def parse_date_text_to_range(text: object) -> Tuple[Optional[int], Optional[int], str]:
    """Parse date-like text into (start_year, end_year, method).

    Handles:
    - explicit years: "1870", "1870-1880"
    - circa: "ca. 1870"
    - decades: "1870s"
    - centuries: "19th century", "5th c. BCE"
    - BCE/BC: interpreted as negative years

    Returns method tag to aid debugging.
    """
    t0 = _norm_str(text)
    if not t0:
        return None, None, "empty"

    t = t0.lower()

    # BCE/BC markers
    bce = bool(re.search(r"\b(bce|bc)\b", t))

    # century patterns e.g. 19th century, 5th c.
    m = re.search(r"\b(\d{1,2})(st|nd|rd|th)\s*(century|c\.?)(\s*(bce|bc))?\b", t)
    if m:
        c = int(m.group(1))
        start = (c - 1) * 100
        end = c * 100 - 1
        if bce or (m.group(5) is not None):
            # 5th century BCE roughly -500 to -401
            start, end = -c * 100, -(c - 1) * 100 - 1
        return start, end, "century"

    # decade pattern 1870s
    m = re.search(r"\b(\d{3})(\d)0s\b", t)
    if m:
        y = int(m.group(1) + m.group(2) + "0")
        return (-y if bce else y), (-y + 9 if bce else y + 9), "decade"

    # ranges like 1870-1880 or 1870–1880
    # normalize dash
    t_dash = re.sub(r"[\u2010\u2011\u2012\u2013\u2014]", "-", t)
    m = re.search(r"(?<!\d)(-?\d{1,4})\s*-\s*(-?\d{1,4})(?!\d)", t_dash)
    if m:
        y1, y2 = int(m.group(1)), int(m.group(2))
        if bce:
            y1, y2 = -abs(y1), -abs(y2)
        start, end = (min(y1, y2), max(y1, y2))
        return start, end, "range"

    # fallback: extract any years
    years = [int(y) for y in YEAR_RE.findall(t_dash)]
    if years:
        # heuristic: if multiple years appear, use min/max
        if bce:
            years = [-abs(y) for y in years]
        start, end = min(years), max(years)
        return start, end, "year_extract"

    return None, None, "unparsed"


def pick_first_nonempty(row: pd.Series, cols: List[str]) -> str:
    for c in cols:
        if c in row.index:
            v = _norm_str(row[c])
            if v:
                return v
    return ""


def standardize_export(df: pd.DataFrame, source: str) -> pd.DataFrame:
    """Map arbitrary export schemas into a shared long table."""
    df = df.copy()
    df["source"] = source
    df["source_row"] = np.arange(len(df))

    # candidate columns per concept (robust to variant naming)
    cols = {c.lower(): c for c in df.columns}

    def _find(*names: str) -> List[str]:
        out = []
        for n in names:
            for k, c in cols.items():
                if k == n.lower():
                    out.append(c)
        return out

    # broader fuzzy column lookup by substring
    def _find_substr(*subs: str) -> List[str]:
        out = []
        for sub in subs:
            for k, c in cols.items():
                if sub.lower() in k:
                    out.append(c)
        # preserve order, unique
        seen = set()
        uniq = []
        for c in out:
            if c not in seen:
                uniq.append(c)
                seen.add(c)
        return uniq

    id_cols = _find_substr("accession", "inventory", "inv", "object number", "object_number", "catalog")
    title_cols = _find_substr("title", "object name", "object_name")
    maker_cols = _find_substr("artist", "maker", "creator", "author")
    culture_cols = _find_substr("culture", "nationality")
    medium_cols = _find_substr("medium", "material", "technique")
    dims_cols = _find_substr("dimension", "dimensions", "size")
    date_text_cols = _find_substr("date", "dated")
    begin_cols = _find_substr("begin", "start")
    end_cols = _find_substr("end", "stop")

    # build standardized columns
    std = pd.DataFrame({
        "source": df["source"],
        "source_row": df["source_row"],
        "id_raw": df.apply(lambda r: pick_first_nonempty(r, id_cols), axis=1),
        "title": df.apply(lambda r: pick_first_nonempty(r, title_cols), axis=1),
        "maker": df.apply(lambda r: pick_first_nonempty(r, maker_cols), axis=1),
        "culture": df.apply(lambda r: pick_first_nonempty(r, culture_cols), axis=1),
        "medium": df.apply(lambda r: pick_first_nonempty(r, medium_cols), axis=1),
        "dimensions": df.apply(lambda r: pick_first_nonempty(r, dims_cols), axis=1),
        "date_text": df.apply(lambda r: pick_first_nonempty(r, date_text_cols), axis=1),
    })

    # attempt to read begin/end numeric columns if present
    def _to_int(x):
        try:
            if pd.isna(x) or str(x).strip() == "":
                return None
            return int(float(x))
        except Exception:
            return None

    begin_guess = None
    end_guess = None
    # pick first begin/end looking numeric
    for c in begin_cols:
        if c in df.columns:
            vals = df[c].dropna()
            if len(vals) and pd.api.types.is_numeric_dtype(vals):
                begin_guess = c
                break
    for c in end_cols:
        if c in df.columns:
            vals = df[c].dropna()
            if len(vals) and pd.api.types.is_numeric_dtype(vals):
                end_guess = c
                break

    if begin_guess is not None:
        std["date_begin_raw"] = df[begin_guess].apply(_to_int)
    else:
        std["date_begin_raw"] = None

    if end_guess is not None:
        std["date_end_raw"] = df[end_guess].apply(_to_int)
    else:
        std["date_end_raw"] = None

    # parse
    parsed = std["date_text"].apply(parse_date_text_to_range)
    std["date_begin_parsed"] = parsed.apply(lambda t: t[0])
    std["date_end_parsed"] = parsed.apply(lambda t: t[1])
    std["date_parse_method"] = parsed.apply(lambda t: t[2])

    # choose best begin/end
    def _choose_begin(r):
        return r["date_begin_raw"] if pd.notna(r["date_begin_raw"]) else r["date_begin_parsed"]

    def _choose_end(r):
        return r["date_end_raw"] if pd.notna(r["date_end_raw"]) else r["date_end_parsed"]

    std["date_begin"] = std.apply(_choose_begin, axis=1)
    std["date_end"] = std.apply(_choose_end, axis=1)

    std["id_norm"] = std["id_raw"].apply(_norm_key)
    std["title_norm"] = std["title"].apply(_norm_text_for_match)
    std["maker_norm"] = std["maker"].apply(_norm_text_for_match)
    std["medium_norm"] = std["medium"].apply(_norm_text_for_match)

    # carry through all original columns too (prefixed), for traceability
    orig = df.copy()
    orig.columns = [f"orig_{source}_" + c for c in orig.columns]
    out = pd.concat([std, orig], axis=1)
    return out


@dataclass
class UnionFind:
    parent: List[int]
    size: List[int]

    @classmethod
    def create(cls, n: int) -> "UnionFind":
        return cls(parent=list(range(n)), size=[1] * n)

    def find(self, a: int) -> int:
        p = self.parent[a]
        if p != a:
            self.parent[a] = self.find(p)
        return self.parent[a]

    def union(self, a: int, b: int) -> bool:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.size[ra] += self.size[rb]
        return True


def similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    if fuzz is not None:
        return float(fuzz.token_set_ratio(a, b))
    # fallback
    return 100.0 * difflib.SequenceMatcher(None, a, b).ratio()


def build_dedup_clusters(df: pd.DataFrame) -> Tuple[pd.Series, pd.DataFrame]:
    """Return cluster_id for each row + pairwise diagnostic frame."""
    n = len(df)
    uf = UnionFind.create(n)

    # Step 1: exact matches on normalized IDs
    id_groups = df[df["id_norm"] != ""].groupby("id_norm").indices
    for _, idxs in id_groups.items():
        idxs = list(idxs)
        for i in range(1, len(idxs)):
            uf.union(idxs[0], idxs[i])

    # Step 2: fuzzy matching among remaining (block to reduce comparisons)
    # Create blocks by first 8 chars of title + first 4 chars of maker
    title_block = df["title_norm"].str[:8].fillna("")
    maker_block = df["maker_norm"].str[:4].fillna("")
    block_key = (title_block + "|" + maker_block).fillna("")

    diag_rows = []

    # Only attempt fuzzy when no shared id_norm (empty) OR different ids.
    # We still can catch cases where IDs missing in one record.
    for bk, idxs in df.groupby(block_key).indices.items():
        idxs = list(idxs)
        if len(idxs) < 2:
            continue
        # limit worst-case block size
        if len(idxs) > 200:
            continue
        for i in range(len(idxs)):
            for j in range(i + 1, len(idxs)):
                a, b = idxs[i], idxs[j]

                # if already same cluster, skip
                if uf.find(a) == uf.find(b):
                    continue

                ra = df.iloc[a]
                rb = df.iloc[b]

                # avoid merging if both have non-empty but different id_norm
                if ra["id_norm"] and rb["id_norm"] and ra["id_norm"] != rb["id_norm"]:
                    continue

                st = similarity(ra["title_norm"], rb["title_norm"])
                sm = similarity(ra["maker_norm"], rb["maker_norm"]) if (ra["maker_norm"] or rb["maker_norm"]) else 100.0

                # date consistency check
                da1, da2 = ra["date_begin"], ra["date_end"]
                db1, db2 = rb["date_begin"], rb["date_end"]
                date_ok = True
                if pd.notna(da1) and pd.notna(db1):
                    # allow up to 25 years shift; date ranges often rough
                    date_ok = abs(float(da1) - float(db1)) <= 25
                if pd.notna(da2) and pd.notna(db2):
                    date_ok = date_ok and abs(float(da2) - float(db2)) <= 25

                score = 0.6 * st + 0.4 * sm

                merged = False
                # thresholds chosen by inspection-friendly conservatism
                if score >= 92 and st >= 88 and sm >= 80 and date_ok:
                    merged = uf.union(a, b)

                diag_rows.append({
                    "block": bk,
                    "i": a,
                    "j": b,
                    "title_score": st,
                    "maker_score": sm,
                    "combo_score": score,
                    "date_ok": date_ok,
                    "merged": merged,
                })

    cluster_root = [uf.find(i) for i in range(n)]
    # compress to contiguous ids
    root_to_cluster = {}
    cluster_ids = []
    for r in cluster_root:
        if r not in root_to_cluster:
            root_to_cluster[r] = len(root_to_cluster)
        cluster_ids.append(root_to_cluster[r])

    diag = pd.DataFrame(diag_rows)
    return pd.Series(cluster_ids, name="cluster_id"), diag


def choose_canonical(cluster: pd.DataFrame) -> Dict[str, object]:
    """Create a single record by preferring non-empty fields across cluster."""
    # prefer row with most filled core fields
    core = ["id_raw", "title", "maker", "culture", "medium", "dimensions", "date_text", "date_begin", "date_end"]

    def filled_count(row: pd.Series) -> int:
        n = 0
        for c in core:
            v = row.get(c, None)
            if v is None:
                continue
            if isinstance(v, str) and v.strip() == "":
                continue
            if pd.isna(v):
                continue
            n += 1
        return n

    scores = cluster.apply(filled_count, axis=1)
    best_idx = int(scores.idxmax())
    base = cluster.loc[best_idx].to_dict()

    # merge missing from others (deterministic: iterate by source then row)
    others = cluster.sort_values(["source", "source_row"])
    for _, r in others.iterrows():
        for c in ["id_raw", "title", "maker", "culture", "medium", "dimensions", "date_text"]:
            if not _norm_str(base.get(c, "")) and _norm_str(r.get(c, "")):
                base[c] = r[c]
        for c in ["date_begin", "date_end"]:
            if pd.isna(base.get(c, np.nan)) and pd.notna(r.get(c, np.nan)):
                base[c] = r[c]

    base["sources"] = ";".join(sorted(cluster["source"].unique().tolist()))
    base["source_rows"] = ";".join([f"{s}:{int(sr)}" for s, sr in zip(cluster["source"], cluster["source_row"])])
    base["n_merged_rows"] = int(len(cluster))
    base["id_norm"] = _norm_key(base.get("id_raw", ""))

    # compute mid-year for plotting
    b, e = base.get("date_begin", None), base.get("date_end", None)
    mid = None
    try:
        if pd.notna(b) and pd.notna(e):
            mid = (float(b) + float(e)) / 2.0
        elif pd.notna(b):
            mid = float(b)
        elif pd.notna(e):
            mid = float(e)
    except Exception:
        mid = None
    base["date_mid"] = mid

    return base


def plot_and_save(figpath: Path):
    figpath.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(figpath, dpi=200)
    plt.close()


def main():
    OUT_DIR.mkdir(exist_ok=True, parents=True)
    IMG_DIR.mkdir(exist_ok=True, parents=True)

    A = pd.read_csv(DATA_A)
    B = pd.read_csv(DATA_B)

    longA = standardize_export(A, "A")
    longB = standardize_export(B, "B")
    long = pd.concat([longA, longB], ignore_index=True)

    long.to_csv(OUT_DIR / "merged_long.csv", index=False)

    # Deduplicate
    cluster_id, diag = build_dedup_clusters(long)
    long["cluster_id"] = cluster_id.values

    diag.to_csv(OUT_DIR / "pairwise_dedup_diagnostics.csv", index=False)

    # Build canonical catalog
    catalog_rows = []
    for cid, grp in long.groupby("cluster_id", sort=True):
        row = choose_canonical(grp)
        row["cluster_id"] = int(cid)
        catalog_rows.append(row)

    catalog = pd.DataFrame(catalog_rows)

    # Minimal clean for ordering
    catalog = catalog.sort_values(["id_norm", "title"], na_position="last")

    catalog.to_csv(OUT_DIR / "dedup_catalog.csv", index=False)

    # clusters jsonl diagnostic
    with (OUT_DIR / "dedup_clusters.jsonl").open("w", encoding="utf-8") as f:
        for cid, grp in long.groupby("cluster_id", sort=True):
            rec = {
                "cluster_id": int(cid),
                "n": int(len(grp)),
                "sources": sorted(grp["source"].unique().tolist()),
                "id_norms": sorted({x for x in grp["id_norm"].tolist() if x}),
                "titles": sorted({t for t in grp["title"].astype(str).tolist() if t and t != 'nan'})[:10],
                "makers": sorted({m for m in grp["maker"].astype(str).tolist() if m and m != 'nan'})[:10],
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # --- Figures ---
    sns.set_theme(style="whitegrid")

    # Figure 1: cluster size distribution
    clust_sizes = long.groupby("cluster_id").size().reset_index(name="cluster_size")
    plt.figure(figsize=(6.8, 4.2))
    ax = sns.countplot(data=clust_sizes, x="cluster_size", color="#4c72b0")
    ax.set_title("Deduplication cluster sizes")
    ax.set_xlabel("Rows per deduplicated object")
    ax.set_ylabel("Number of objects")
    plot_and_save(IMG_DIR / "fig1_cluster_sizes.png")

    # Figure 2: similarity diagnostics (merged vs not merged)
    plt.figure(figsize=(7.2, 4.2))
    if len(diag):
        # subsample for visibility
        d = diag.copy()
        if len(d) > 10000:
            d = d.sample(10000, random_state=0)
        ax = sns.scatterplot(
            data=d,
            x="title_score",
            y="maker_score",
            hue="merged",
            alpha=0.35,
            palette={False: "#999999", True: "#dd8452"},
            edgecolor=None,
        )
        ax.set_title("Pairwise fuzzy-match diagnostics (sample)")
        ax.set_xlabel("Title similarity (token_set_ratio)")
        ax.set_ylabel("Maker similarity (token_set_ratio)")
        ax.legend(title="Merged")
    else:
        ax = plt.gca()
        ax.axis('off')
        ax.text(0.5, 0.5, 'No fuzzy-comparison diagnostics were generated\n(no candidate pairs after blocking).',
                ha='center', va='center')
    plot_and_save(IMG_DIR / "fig2_fuzzy_diagnostics.png")

    # Figure 3: parse method breakdown
    plt.figure(figsize=(7.2, 4.2))
    pm = long["date_parse_method"].value_counts(dropna=False).reset_index()
    pm.columns = ["method", "n"]
    ax = sns.barplot(data=pm, y="method", x="n", color="#55a868")
    ax.set_title("Date parsing methods used")
    ax.set_xlabel("Rows")
    ax.set_ylabel("Method")
    plot_and_save(IMG_DIR / "fig3_date_parse_methods.png")

    # Collection time distribution using deduplicated catalog
    cat = catalog.copy()
    cat_valid = cat[pd.notna(cat["date_mid"])].copy()

    # Figure 4: histogram by decade (excluding BCE for readability; handle separately)
    ce = cat_valid[cat_valid["date_mid"] >= 0].copy()
    plt.figure(figsize=(10.5, 4.2))
    if len(ce):
        ce["decade"] = (np.floor(ce["date_mid"] / 10) * 10).astype(int)
        decade_counts = ce["decade"].value_counts().sort_index().reset_index()
        decade_counts.columns = ["decade", "n"]
        ax = sns.lineplot(data=decade_counts, x="decade", y="n", marker="o", linewidth=1.8, color="#4c72b0")
        ax.set_title("Objects by estimated production decade (CE only)")
        ax.set_xlabel("Decade")
        ax.set_ylabel("Number of objects")
        # reduce tick density
        for label in ax.get_xticklabels()[::2]:
            label.set_visible(False)
    else:
        ax = plt.gca()
        ax.axis('off')
        ax.text(0.5, 0.5, 'No CE dates available for decade distribution.', ha='center', va='center')
    plot_and_save(IMG_DIR / "fig4_decade_distribution.png")

    # Figure 5: century distribution (CE and BCE together)
    def century(y: float) -> int:
        # 1.. for CE; -1.. for BCE, where -1 corresponds to 1st century BCE
        if y >= 0:
            return int(math.floor(y / 100.0) + 1)
        # e.g., y=-50 -> -1; y=-250 -> -3
        return -int(math.floor((abs(y) - 1) / 100.0) + 1)

    plt.figure(figsize=(10.0, 4.2))
    if len(cat_valid):
        cat_valid["century"] = cat_valid["date_mid"].astype(float).apply(century)
        cent_counts = cat_valid["century"].value_counts().sort_index().reset_index()
        cent_counts.columns = ["century", "n"]
        ax = sns.barplot(data=cent_counts, x="century", y="n", color="#c44e52")
        ax.set_title("Objects by estimated production century")
        ax.set_xlabel("Century (negative = BCE)")
        ax.set_ylabel("Number of objects")
    else:
        ax = plt.gca()
        ax.axis('off')
        ax.text(0.5, 0.5, 'No parseable dates available for century distribution.', ha='center', va='center')
    plot_and_save(IMG_DIR / "fig5_century_distribution.png")

    # Save summary stats for report
    summary = {
        "n_rows_A": int(len(A)),
        "n_rows_B": int(len(B)),
        "n_rows_combined": int(len(long)),
        "n_objects_dedup": int(len(catalog)),
        "n_rows_with_id": int((long["id_norm"] != "").sum()),
        "n_objects_with_date_mid": int(pd.notna(catalog["date_mid"]).sum()),
        "n_objects_ce_with_date_mid": int((pd.notna(catalog["date_mid"]) & (catalog["date_mid"] >= 0)).sum()),
        "n_objects_bce_with_date_mid": int((pd.notna(catalog["date_mid"]) & (catalog["date_mid"] < 0)).sum()),
        "cluster_size_counts": clust_sizes["cluster_size"].value_counts().sort_index().to_dict(),
    }
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
