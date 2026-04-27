#!/usr/bin/env python
"""Pipeline for scenario 07c: parse email_thread_draft.txt, extract requirements,
generate a formal SOP draft (cold_chain_sop.md), and generate figures + report inputs.

Constraint: SOP content must be grounded in email_thread_draft.txt only.
We therefore:
- quote or paraphrase only statements present in the email thread
- mark unspecified items as 'Not specified in email thread'

Outputs:
- outputs/extracted_requirements.csv
- outputs/keyword_counts.csv
- report/images/fig_top_terms.png
- report/images/fig_keyword_counts.png
- cold_chain_sop.md

"""

from __future__ import annotations

import re
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


ROOT = Path('.')
DATA = ROOT / 'data' / 'email_thread_draft.txt'
OUT = ROOT / 'outputs'
IMG = ROOT / 'report' / 'images'


STOPWORDS = set(
    """a an and are as at be been being but by can could did do does doing done for from had has have having he her hers him his how i if in into is it its may might more most must my no not of on or our ours please should so some such than that the their them then there these they this to too very was we were what when where which who will with would you your""".split()
)


KEYWORDS = {
    # cold chain temps
    '2-8': [r"\b2\s*[–-]\s*8\b", r"\b2\s*to\s*8\b"],
    '-20': [r"\b-\s*20\b", r"\bminus\s*20\b"],
    '-80': [r"\b-\s*80\b", r"\bminus\s*80\b"],
    'dry ice': [r"dry\s*ice"],
    'gel pack': [r"gel\s*packs?"],
    'ice pack': [r"ice\s*packs?"],
    'data logger': [r"data\s*logger", r"temperature\s*logger", r"logger"],
    'monitoring': [r"monitor", r"temperature\s*excursion"],
    'courier': [r"fedex", r"dhl", r"ups", r"courier"],
    'labeling': [r"label", r"waybill", r"air\s*bill"],
    'weekend/holiday': [r"weekend", r"holiday"],
    'receipt': [r"receive", r"receipt", r"upon\s*arrival"],
    'deviation': [r"deviation", r"excursion", r"out\s*of\s*range"],
    'chain of custody': [r"chain\s*of\s*custody", r"custody"],
    'quarantine': [r"quarantine", r"hold"],
    'precondition': [r"pre[-\s]*condition"],
    'packing list': [r"packing\s*list"],
}


REQ_CUES = [
    r"\bmust\b",
    r"\bshould\b",
    r"\bshall\b",
    r"\bplease\b",
    r"\bensure\b",
    r"\brequire\b",
    r"\bdo not\b",
    r"\bneed to\b",
    r"\bneeds to\b",
]


def read_email() -> str:
    return DATA.read_text(encoding='utf-8', errors='replace')


def normalize(text: str) -> str:
    # drop email quote markers and common headers but keep content
    text = re.sub(r"^>+\s?", "", text, flags=re.MULTILINE)
    return text


def tokenize(text: str) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z\-']+", text.lower())
    return [w for w in words if w not in STOPWORDS and len(w) > 2]


def extract_requirements(text: str) -> pd.DataFrame:
    lines = [l.rstrip() for l in text.splitlines()]
    req_re = re.compile("|".join(REQ_CUES), flags=re.IGNORECASE)
    rows = []
    for i, line in enumerate(lines, 1):
        s = line.strip()
        if not s:
            continue
        if req_re.search(s):
            rows.append({"line_no": i, "text": s})
        # Also capture bullet items, often instructions
        if re.match(r"\s*(?:[-*]|\d+\.)\s+", line):
            rows.append({"line_no": i, "text": s})
    df = pd.DataFrame(rows).drop_duplicates().sort_values(['line_no', 'text'])
    return df


def keyword_counts(text: str) -> pd.DataFrame:
    lc = text.lower()
    counts = {}
    for k, pats in KEYWORDS.items():
        c = 0
        for pat in pats:
            c += len(re.findall(pat, lc, flags=re.IGNORECASE))
        counts[k] = c
    return pd.DataFrame({"keyword": list(counts.keys()), "count": list(counts.values())}).sort_values('count', ascending=False)


def plot_top_terms(tokens: list[str], path: Path, n: int = 20):
    top = Counter(tokens).most_common(n)
    if not top:
        raise RuntimeError('No tokens extracted; check input text')
    terms, freqs = zip(*top)
    plt.figure(figsize=(10, 5))
    plt.barh(list(reversed(terms)), list(reversed(freqs)), color='#4C78A8')
    plt.xlabel('Frequency')
    plt.title(f'Top {n} terms in email thread (stopwords removed)')
    plt.tight_layout()
    plt.savefig(path, dpi=200)
    plt.close()


def plot_keyword_counts(df: pd.DataFrame, path: Path):
    df2 = df[df['count'] > 0].copy()
    if df2.empty:
        # still create an empty plot to satisfy report figure requirement
        df2 = df.copy().head(10)
    df2 = df2.sort_values('count', ascending=True)
    plt.figure(figsize=(10, 5))
    plt.barh(df2['keyword'], df2['count'], color='#F58518')
    plt.xlabel('Mentions (regex count)')
    plt.title('Mentions of cold-chain shipment elements in email thread')
    plt.tight_layout()
    plt.savefig(path, dpi=200)
    plt.close()


def plot_bucket_counts(buckets: dict[str, list[str]], path: Path):
    counts = {k: len(v) for k, v in buckets.items()}
    if not counts:
        counts = {'No requirements detected': 0}
    items = sorted(counts.items(), key=lambda x: x[1])
    labels = [k for k, _ in items]
    vals = [v for _, v in items]
    plt.figure(figsize=(10, 5))
    plt.barh(labels, vals, color='#54A24B')
    plt.xlabel('Number of extracted requirement-like lines')
    plt.title('Distribution of extracted requirements across SOP sections')
    plt.tight_layout()
    plt.savefig(path, dpi=200)
    plt.close()


def classify_requirements(req_df: pd.DataFrame) -> dict[str, list[str]]:
    """Rule-based categorization of requirement-like lines into SOP sections."""
    buckets: dict[str, list[str]] = defaultdict(list)
    for _, r in req_df.iterrows():
        t = r['text']
        tl = t.lower()
        key = 'General'
        if any(x in tl for x in ['pickup', 'courier', 'fedex', 'dhl', 'deliver', 'shipping', 'ship ', 'dispatch', 'schedule', 'eta']):
            key = 'Courier, Scheduling, & Handover'
        if any(x in tl for x in ['pack', 'shipper', 'dry ice', 'gel', 'ice', 'insulat', 'coolant', 'refrigerant']):
            key = 'Packaging & Packing'
        if any(x in tl for x in ['label', 'waybill', 'airbill', 'documentation', 'packing list']):
            key = 'Labeling & Documentation'
        if any(x in tl for x in ['logger', 'monitor', 'excursion', 'temperature', 'probe']):
            key = 'Temperature Monitoring & Excursions'
        if any(x in tl for x in ['receive', 'receipt', 'upon arrival', 'arrival', 'unpack']):
            key = 'Receipt & Acceptance'
        if any(x in tl for x in ['quarantine', 'hold', 'deviation', 'nonconform', 'capa']):
            key = 'Deviations, Quarantine, & CAPA'
        buckets[key].append(f"- {t} (Email line {int(r['line_no'])})")
    return buckets


def build_sop_markdown(email_text: str, req_df: pd.DataFrame, kw_df: pd.DataFrame) -> str:
    """Create a formal SOP structure, embedding extracted, source-grounded statements.

    We avoid inventing parameters; where needed, we explicitly mark as unspecified.
    """

    buckets = classify_requirements(req_df)

    def section(title: str, body_lines: list[str]) -> str:
        if not body_lines:
            body_lines = ["- Not specified in email thread."]
        return f"## {title}\n\n" + "\n".join(body_lines) + "\n\n"

    md = []
    md.append("# Cold-Chain Shipment Standard Operating Procedure (SOP)\n")
    md.append("**Document ID:** TBD\n\n**Version:** 0.1 (Draft generated from internal email thread)\n\n**Effective Date:** TBD\n\n**Owner:** TBD\n\n**Approved by:** TBD\n")
    md.append("\n---\n")
    md.append("## 1. Purpose\n\nThis SOP defines the cold-chain shipment process as described in the internal email thread provided in `email_thread_draft.txt`, including packing, labeling, courier handover, temperature monitoring, receipt, and excursion handling.\n\n")
    md.append("## 2. Scope\n\nApplies to shipments requiring temperature control (e.g., refrigerated, frozen, or dry-ice) as referenced in the email thread. Specific temperature setpoints, packaging configurations, and lanes apply only if explicitly stated in the email thread.\n\n")
    md.append("## 3. Source of Requirements\n\nThis SOP is **constrained to the content of** the provided email thread (`data/email_thread_draft.txt`). Any item not specified there is marked as **Not specified in email thread**.\n\n")

    md.append("## 4. Definitions & Abbreviations\n\nDefinitions are limited to terms explicitly referenced in the email thread; if a term is used but not defined, it is treated per common operational meaning.\n\n")

    md.append("## 5. Roles & Interfaces\n\nRoles are described only at a high level to avoid introducing requirements not present in the email thread.\n\n- **Sender (shipping site)**\n- **Courier / carrier**\n- **Receiver (receiving site)**\n\n")

    md.append("## 6. Materials, Equipment, and Documents (as referenced)\n\nThis list is populated only from items mentioned in the email thread.\n\n")
    # Materials/equipment list derived from keyword mentions
    mat_lines = []
    if kw_df.loc[kw_df['keyword'].eq('dry ice'), 'count'].sum() > 0:
        mat_lines.append('- Dry ice (as referenced).')
    if kw_df.loc[kw_df['keyword'].eq('gel pack'), 'count'].sum() > 0:
        mat_lines.append('- Gel packs (as referenced).')
    if kw_df.loc[kw_df['keyword'].eq('ice pack'), 'count'].sum() > 0:
        mat_lines.append('- Ice packs (as referenced).')
    if kw_df.loc[kw_df['keyword'].eq('data logger'), 'count'].sum() > 0:
        mat_lines.append('- Temperature data logger (as referenced).')
    if kw_df.loc[kw_df['keyword'].eq('labeling'), 'count'].sum() > 0:
        mat_lines.append('- Labels / waybill / shipping label (as referenced).')
    if kw_df.loc[kw_df['keyword'].eq('packing list'), 'count'].sum() > 0:
        mat_lines.append('- Packing list (as referenced).')
    if not mat_lines:
        mat_lines = ['- Not specified in email thread.']
    md.append("\n".join(mat_lines) + "\n\n")

    md.append("# 7. Procedure (requirements extracted from email thread)\n\n")

    md.append(section("7.1 Courier, Scheduling, & Handover", buckets.get('Courier, Scheduling, & Handover', [])))
    md.append(section("7.2 Packaging & Packing", buckets.get('Packaging & Packing', [])))
    md.append(section("7.3 Labeling & Documentation", buckets.get('Labeling & Documentation', [])))
    md.append(section("7.4 Temperature Monitoring & Excursions", buckets.get('Temperature Monitoring & Excursions', [])))
    md.append(section("7.5 Receipt & Acceptance", buckets.get('Receipt & Acceptance', [])))
    md.append(section("7.6 Deviations, Quarantine, & CAPA", buckets.get('Deviations, Quarantine, & CAPA', [])))

    md.append("# 8. Records (only if referenced)\n\n")
    rec_lines = []
    if kw_df.loc[kw_df['keyword'].eq('courier'), 'count'].sum() > 0 or kw_df.loc[kw_df['keyword'].eq('labeling'), 'count'].sum() > 0:
        rec_lines.append('- Courier waybill / tracking number (as referenced).')
    if kw_df.loc[kw_df['keyword'].eq('data logger'), 'count'].sum() > 0:
        rec_lines.append('- Temperature logger ID and temperature record/download (as referenced).')
    if kw_df.loc[kw_df['keyword'].eq('packing list'), 'count'].sum() > 0:
        rec_lines.append('- Packing list (as referenced).')
    if kw_df.loc[kw_df['keyword'].eq('receipt'), 'count'].sum() > 0:
        rec_lines.append('- Receipt confirmation / arrival confirmation (as referenced).')
    if kw_df.loc[kw_df['keyword'].eq('deviation'), 'count'].sum() > 0:
        rec_lines.append('- Deviation/excursion documentation and disposition decision (as referenced).')
    if not rec_lines:
        rec_lines = ['- Not specified in email thread.']
    md.append("\n".join(rec_lines) + "\n\n")

    md.append("# 9. Attachments (Templates)\n\n- Not specified in email thread.\n\n")

    md.append("---\n\n## Appendix: Evidence extracted from email thread\n\n")
    md.append("### A1. Extracted requirement statements\n\n")
    if req_df.empty:
        md.append("- No explicit requirement-like statements were detected by the extraction rules.\n")
    else:
        for _, r in req_df.iterrows():
            md.append(f"- (Line {int(r['line_no'])}) {r['text']}\n")

    md.append("\n### A2. Keyword mention counts (sanity check)\n\n")
    for _, r in kw_df.iterrows():
        md.append(f"- {r['keyword']}: {int(r['count'])}\n")

    return "".join(md)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    IMG.mkdir(parents=True, exist_ok=True)

    raw = read_email()
    text = normalize(raw)

    tokens = tokenize(text)
    req_df = extract_requirements(text)
    kw_df = keyword_counts(text)

    # Save intermediates
    req_path = OUT / 'extracted_requirements.csv'
    kw_path = OUT / 'keyword_counts.csv'
    req_df.to_csv(req_path, index=False)
    kw_df.to_csv(kw_path, index=False)

    # Additional intermediate: bucket counts
    buckets = classify_requirements(req_df)
    bucket_counts = pd.DataFrame(
        {"section": list(buckets.keys()), "n_lines": [len(v) for v in buckets.values()]}
    ).sort_values('n_lines', ascending=False)
    bucket_path = OUT / 'bucket_counts.csv'
    bucket_counts.to_csv(bucket_path, index=False)

    # Plots
    plot_top_terms(tokens, IMG / 'fig_top_terms.png', n=20)
    plot_keyword_counts(kw_df, IMG / 'fig_keyword_counts.png')
    plot_bucket_counts(buckets, IMG / 'fig_requirement_buckets.png')

    # SOP draft
    sop_md = build_sop_markdown(text, req_df, kw_df)
    (ROOT / 'cold_chain_sop.md').write_text(sop_md, encoding='utf-8')

    # Also save a machine-readable extraction to support the report
    (OUT / 'extracted_requirements.json').write_text(req_df.to_json(orient='records', indent=2), encoding='utf-8')

    print('Wrote:')
    print(' -', req_path)
    print(' -', kw_path)
    print(' -', bucket_path)
    print(' -', IMG / 'fig_top_terms.png')
    print(' -', IMG / 'fig_keyword_counts.png')
    print(' -', IMG / 'fig_requirement_buckets.png')
    print(' -', ROOT / 'cold_chain_sop.md')


if __name__ == '__main__':
    main()
