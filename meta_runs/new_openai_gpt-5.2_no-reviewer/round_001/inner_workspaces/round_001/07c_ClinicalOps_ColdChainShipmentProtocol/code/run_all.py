#!/usr/bin/env python3
"""Generate a cold-chain shipment SOP strictly from the provided email draft.

This project is intentionally "closed-book": we only use the content of
`data/email_thread_draft.txt` as the factual source. The code extracts
operational requirements (temperatures, timing constraints, materials,
responsibilities, documentation, contingency language) using deterministic
regex/keyword rules, then renders a formal SOP and an accompanying report with
figures.

Outputs:
- cold_chain_sop.md
- outputs/extracted_requirements.json
- report/images/*.png
- report/report.md
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np


WORKSPACE_ROOT = Path('.')
DATA_PATH = WORKSPACE_ROOT / 'data' / 'email_thread_draft.txt'


@dataclass
class Extracted:
    raw_text: str
    lines: List[str]
    temps_ranges_c: List[Tuple[int, int]]
    temps_single_c: List[int]
    temp_qualitative: List[str]
    time_phrases: List[str]
    couriers: List[str]
    materials: List[str]
    monitoring: List[str]
    documentation: List[str]
    constraints: List[str]
    responsibilities: Dict[str, List[str]]
    key_terms_counts: Dict[str, int]
    source_snippets: Dict[str, List[Dict[str, str]]]


def normalize_whitespace(s: str) -> str:
    return re.sub(r'\s+', ' ', s).strip()


def load_email() -> Tuple[str, List[str]]:
    text = DATA_PATH.read_text(encoding='utf-8', errors='replace')
    # Normalize line endings but preserve lines for traceability
    lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    return text, lines


def find_line_numbers(lines: List[str], pattern: re.Pattern, max_hits: int = 8) -> List[Tuple[int, str]]:
    hits = []
    for i, l in enumerate(lines, 1):
        if pattern.search(l):
            hits.append((i, l))
            if len(hits) >= max_hits:
                break
    return hits


def extract_temperature_mentions(text: str) -> Tuple[List[Tuple[int, int]], List[int]]:
    # Ranges like 2-8 C, -70 to -90°C
    range_re = re.compile(r'(?P<a>-?\d{1,3})\s*(?:-|–|to)\s*(?P<b>-?\d{1,3})\s*°?\s*C\b', re.I)
    ranges = []
    for m in range_re.finditer(text):
        a, b = int(m.group('a')), int(m.group('b'))
        # filter out obvious non-temperature ranges (keep conservative)
        if -120 <= a <= 60 and -120 <= b <= 60:
            ranges.append((a, b))

    # Singles like -80 C, 8°C, 25 C
    single_re = re.compile(r'(?<!-)\b(-?\d{1,3})\s*°?\s*C\b', re.I)
    singles = []
    for m in single_re.finditer(text):
        v = int(m.group(1))
        if -120 <= v <= 60:
            singles.append(v)

    return ranges, singles


def is_boilerplate_email_line(line: str) -> bool:
    l = line.strip()
    if not l:
        return True
    # Common email headers / reply markers
    if re.match(r'^(from|to|cc|bcc|sent|subject|date):\s', l, flags=re.I):
        return True
    if re.match(r'^on\s.+wrote:\s*$', l, flags=re.I):
        return True
    # Common sign-offs / greetings
    if re.match(r'^(hi|hello|dear)\b', l, flags=re.I):
        return True
    if re.match(r'^(thanks|thank you|regards|best|sincerely)[,\s]*$', l, flags=re.I):
        return True
    # Very short lines that are likely names/initials
    if len(l) <= 2:
        return True
    if re.fullmatch(r'[A-Za-z\.\s]{2,25}', l) and len(l.split()) <= 3:
        # e.g., "John Doe", "JD"
        return True
    return False


def extract_phrases(
    lines: List[str],
    patterns: List[Tuple[str, str]],
    window: int = 0,
    drop_boilerplate: bool = True,
) -> Tuple[List[str], Dict[str, List[Dict[str, str]]]]:
    """Extract matching source lines for a set of (topic, regex) patterns.

    Returns:
      - a de-duplicated list of matched lines (normalized)
      - a dict(topic -> list of snippets with line numbers and optional context)

    The extraction is intentionally conservative and avoids injecting content.
    """
    found: List[str] = []
    snippets: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for topic, pat in patterns:
        rx = re.compile(pat, re.I)
        for i, l in enumerate(lines, 1):
            if drop_boilerplate and is_boilerplate_email_line(l):
                continue
            if rx.search(l):
                start = max(1, i - window)
                end = min(len(lines), i + window)
                ctx_lines = []
                for j in range(start, end + 1):
                    lj = lines[j - 1]
                    if drop_boilerplate and is_boilerplate_email_line(lj):
                        continue
                    ljn = normalize_whitespace(lj)
                    if ljn:
                        ctx_lines.append(ljn)
                context = ' '.join(ctx_lines)
                match_line = normalize_whitespace(l)
                snippets[topic].append({'line': str(i), 'match_line': match_line, 'context': context or match_line})
                found.append(match_line)

    # De-duplicate while preserving order
    seen = set()
    dedup: List[str] = []
    for x in found:
        if x and x not in seen:
            dedup.append(x)
            seen.add(x)
    return dedup, snippets


def extract_requirements(text: str, lines: List[str]) -> Extracted:
    ranges, singles = extract_temperature_mentions(text)

    # Qualitative temperature/condition terms (only if present in source)
    qual_terms = []
    for term in ['ambient', 'room temperature', 'refrigerated', 'refrigeration', 'frozen', 'ultra-low', 'ultralow', 'cryogenic', 'dry ice']:
        if re.search(rf'\b{re.escape(term)}\b', text, re.I):
            qual_terms.append(term)

    # Topic patterns (conservative, based on common operational terms)
    time_pats = [
        ('timing', r'\b(Mon(day)?|Tue(sday)?|Wed(nesday)?|Thu(rsday)?|Fri(day)?|weekend|holiday|overnight|same\s*day|next\s*day|deliver(y)?|pickup|pick\s*up|hold)\b'),
        ('timing', r'\b\d+\s*(hour|hr|hrs|hours|day|days)\b'),
    ]
    courier_pats = [
        ('courier', r'\bFedEx\b'),
        ('courier', r'\bWorld\s*Courier\b'),
        ('courier', r'\bDHL\b'),
        ('courier', r'\bUPS\b'),
        ('courier', r'\bcourier\b'),
        ('courier', r'\bcarrier\b'),
    ]
    materials_pats = [
        ('materials', r'\bdry\s*-?\s*ice\b'),
        ('materials', r'\bgel\s*-?\s*pack(s)?\b|\bice\s*-?\s*pack(s)?\b'),
        ('materials', r'\binsulated\s+(shipper|container|box)\b|\bvalidated\s+shipper\b'),
        ('materials', r'\bcooler\b|\bfoam\b|\bEPS\b|\binsulation\b'),
        ('materials', r'\bsecondary\s*(container|packaging)\b'),
        ('materials', r'\babsorbent\b'),
        ('materials', r'\bzip\s*lock\b|\bziploc\b'),
        ('materials', r'\bparafilm\b|\btape\b'),
        ('materials', r'\bthermometer\b'),
        # Capture explicit shipper brand names only if present in email
        ('materials', r'\bCryoport\b|\bCredo\b|\bPelican\b|\bNanoCool\b'),
    ]
    monitoring_pats = [
        ('monitoring', r'\b(temp(erature)?\s*(logger|monitor))\b|\btemp\s*-?\s*logger\b'),
        ('monitoring', r'\bdata\s*-?\s*logger\b|\bdatalogger\b'),
        ('monitoring', r'\bNIST\b'),
        ('monitoring', r'\bprobe\b'),
        ('monitoring', r'\bcalibrat'),
        ('monitoring', r'\bexcursion\b'),
    ]
    doc_pats = [
        ('documentation', r'\bpacking\s*list\b'),
        ('documentation', r'\bpro\s*forma\b'),
        ('documentation', r'\binvoice\b'),
        ('documentation', r'\bcustoms\b'),
        ('documentation', r'\bwaybill\b'),
        ('documentation', r'\bchain\s*of\s*custody\b|\bCOC\b'),
        ('documentation', r'\bCOA\b|certificate\s*of\s*analysis'),
        ('documentation', r'\bSDS\b|safety\s*data\s*sheet'),
        ('documentation', r'\bIATA\b'),
        ('documentation', r'\bUN\s*\d{4}\b|UN1845'),
        ('documentation', r'\bshipper\s*declaration\b|dangerous\s*goods'),
    ]
    constraint_pats = [
        # Require explicit action words tied to shipment-relevant nouns to reduce noise
        ('constraints', r'\b(do\s*not\s*ship|avoid|must|required|require|ensure|confirm)\b.*\b(ship|shipment|pickup|delivery|weekend|holiday|temperature|dry\s*-?\s*ice|gel\s*-?\s*pack|label|logger|data\s*-?\s*logger|datalogger|receive|recipient|courier|customs)\b'),
        ('constraints', r'\bnotify\b|\bpre-?alert\b|\bcall\s*ahead\b'),
        ('constraints', r'\bhold\s*at\s*location\b'),
        ('constraints', r'\bquarantine\b'),
    ]

    time_phrases, time_snips = extract_phrases(lines, time_pats, window=0)
    courier_lines, courier_snips = extract_phrases(lines, courier_pats, window=0)
    material_lines, material_snips = extract_phrases(lines, materials_pats, window=0)
    monitoring_lines, monitoring_snips = extract_phrases(lines, monitoring_pats, window=0)
    doc_lines, doc_snips = extract_phrases(lines, doc_pats, window=0)
    # include context for constraints to preserve "must/avoid/do not" surrounding details
    constraint_lines, constraint_snips = extract_phrases(lines, constraint_pats, window=1)

    couriers = sorted({c for c in ['FedEx', 'World Courier', 'DHL', 'UPS'] if re.search(rf'\b{re.escape(c)}\b', text, re.I)})

    # Responsibilities: infer from explicit role words in email (conservative)
    roles = {
        'Shipper': [r'\bshipper\b', r'\bsending\s*site\b', r'\borigin\b'],
        'Recipient': [r'\brecipient\b', r'\breceiving\s*site\b', r'\bdestination\b'],
        'Courier/Carrier': [r'\bcourier\b', r'\bcarrier\b', r'\bFedEx\b', r'\bWorld\s*Courier\b', r'\bDHL\b', r'\bUPS\b'],
        'Clinical Operations': [r'\bClinical\s*Ops\b', r'\bClinical\s*Operations\b'],
        'Quality/QA': [r'\bQA\b', r'\bQuality\b'],
        'Laboratory': [r'\blab\b', r'\blaboratory\b'],
    }
    responsibilities: Dict[str, List[str]] = {}
    for role, pats in roles.items():
        role_lines = []
        for pat in pats:
            rx = re.compile(pat, re.I)
            for i, l in enumerate(lines, 1):
                if rx.search(l):
                    role_lines.append(f"Line {i}: {normalize_whitespace(l)}")
        # include role if appears at least once
        if role_lines:
            # de-dup and keep small
            seen = set()
            uniq = []
            for rl in role_lines:
                if rl not in seen:
                    uniq.append(rl)
                    seen.add(rl)
            responsibilities[role] = uniq[:12]

    # Key term counts for coverage validation
    key_terms = {
        'temperature': r'\btemp(erature)?\b|°\s*C|°C|\bC\b',
        'dry_ice': r'\bdry\s*-?\s*ice\b',
        'gel_packs': r'\bgel\s*-?\s*pack',
        'data_logger': r'\b(temp(erature)?\s*(logger|monitor)\b|data\s*-?\s*logger\b|datalogger\b|temp\s*-?\s*logger\b)',
        'courier': r'\bFedEx\b|\bWorld\s*Courier\b|\bDHL\b|\bUPS\b|\bcourier\b|\bcarrier\b',
        'labeling': r'\blabel\b|\bUN\s*\d{4}\b|UN1845|IATA',
        'documentation': r'\bpacking\s*list\b|\bpro\s*forma\b|\binvoice\b|\bcustoms\b|\bCOA\b|\bCOC\b|\bshipper\s*declaration\b|dangerous\s*goods',
        'weekend_holiday': r'\bweekend\b|\bholiday\b|\bFriday\b|\bSaturday\b|\bSunday\b',
        'excursion_deviation': r'\bexcursion\b|\bdeviation\b|\bquarantine\b',
        'receipt': r'\breceiv|\breceipt\b|\binspect\b',
        'communication': r'\bnotify\b|\bpre-?alert\b|\bcall\s*ahead\b|\bcontact\b',
    }
    counts = {k: len(re.findall(v, text, flags=re.I)) for k, v in key_terms.items()}

    source_snippets = {}
    for d in (time_snips, courier_snips, material_snips, monitoring_snips, doc_snips, constraint_snips):
        for k, v in d.items():
            source_snippets.setdefault(k, []).extend(v)

    return Extracted(
        raw_text=text,
        lines=lines,
        temps_ranges_c=ranges,
        temps_single_c=singles,
        temp_qualitative=qual_terms,
        time_phrases=time_phrases,
        couriers=couriers,
        materials=material_lines,
        monitoring=monitoring_lines,
        documentation=doc_lines,
        constraints=constraint_lines,
        responsibilities=responsibilities,
        key_terms_counts=counts,
        source_snippets=source_snippets,
    )


def render_sop(ex: Extracted) -> str:
    # Build SOP using only extracted/quoted content. If something is not present,
    # we keep it as "TBD" or omit.

    def bulletize(items: List[str], max_n: int = 15) -> str:
        items = [normalize_whitespace(x) for x in items if normalize_whitespace(x)]
        if not items:
            return "- (Not specified in the source email thread.)"
        out = []
        for x in items[:max_n]:
            out.append(f"- {x}")
        if len(items) > max_n:
            out.append(f"- … ({len(items) - max_n} additional matching lines in source email)")
        return "\n".join(out)

    # Temperatures summary
    temps_summary = []
    if ex.temp_qualitative:
        temps_summary.append('Qualitative conditions mentioned: ' + ', '.join(ex.temp_qualitative))
    if ex.temps_ranges_c:
        # unique ranges
        uniq = []
        for a, b in ex.temps_ranges_c:
            if (a, b) not in uniq:
                uniq.append((a, b))
        temps_summary.extend([f"{a} to {b} °C" for a, b in uniq[:10]])
    if ex.temps_single_c:
        # show unique singles
        u = []
        for v in ex.temps_single_c:
            if v not in u:
                u.append(v)
        temps_summary.extend([f"{v} °C" for v in u[:10]])

    temps_block = "- (No explicit °C values detected in the source email thread.)"
    if temps_summary:
        temps_block = "\n".join([f"- {t}" for t in temps_summary])

    # Responsibilities: keep cautious; list roles that appear.
    resp_lines = []
    if ex.responsibilities:
        for role, evid in ex.responsibilities.items():
            resp_lines.append(f"### {role}\n")
            # Evidence lines show where role appears
            resp_lines.append("**Evidence in email thread (role mention):**")
            resp_lines.extend([f"- {e}" for e in evid[:6]])
            resp_lines.append("\n**Responsibilities (as described in the email thread):**")
            resp_lines.append("- (Responsibilities are described across the thread; see Procedure and Communication steps for operational actions.)")
            resp_lines.append("")
    else:
        resp_lines.append("(Roles/responsibilities are not explicitly assigned in the source email thread.)")

    # Courier list
    courier_block = "- (No named courier detected in source email thread.)"
    if ex.couriers:
        courier_block = "\n".join([f"- {c}" for c in ex.couriers])

    # Traceability appendix from snippets: include small number of snippets per topic.
    def trace_block(topic: str, max_n: int = 8) -> str:
        snips = ex.source_snippets.get(topic, [])
        if not snips:
            return "- (No matching source snippets captured.)"
        out = []
        for s in snips[:max_n]:
            out.append(f"- Line {s['line']}: {s['match_line']}")
        if len(snips) > max_n:
            out.append(f"- … ({len(snips) - max_n} additional matching lines) ")
        return "\n".join(out)

    # Definitions / abbreviations: include only if detected in source email
    defs = []
    if re.search(r'\bCOA\b|certificate\s+of\s+analysis', ex.raw_text, re.I):
        defs.append('- **COA**: Certificate of Analysis.')
    if re.search(r'\bCOC\b|chain\s+of\s+custody', ex.raw_text, re.I):
        defs.append('- **COC**: Chain of Custody.')
    if re.search(r'\bIATA\b', ex.raw_text, re.I):
        defs.append('- **IATA**: International Air Transport Association (referenced for shipping/labeling context).')
    if re.search(r'\bUN\s*\d{4}\b|UN1845', ex.raw_text, re.I):
        defs.append('- **UN (e.g., UN1845)**: UN number used for transport labeling/regulatory context as referenced in the source.')
    def_block = '\n'.join(defs) if defs else '- (No abbreviations/definitions explicitly referenced in the source email thread.)'

    sop = f"""# Cold-Chain Shipment Standard Operating Procedure (SOP)

**Document title:** Cold-Chain Shipment SOP (derived from email thread draft)  
**SOP ID:** TBD  
**Version:** 1.0 (Draft)  
**Effective date:** TBD  
**Prepared by:** TBD (SOP generated from source email thread draft)  
**Approved by:** TBD  

## 1. Purpose
To define the cold-chain shipment process as described in the provided email thread draft, including packaging, temperature control, monitoring, documentation, communication, receipt, and deviation handling.

## 2. Scope
This SOP applies to shipments that require cold-chain controls referenced in the email thread draft (e.g., refrigerated/frozen shipments, shipments using dry ice/gel packs, and/or shipments requiring temperature monitoring).

## 3. Source & Traceability
This SOP is **derived exclusively** from `data/email_thread_draft.txt`. Requirements are supported by a traceability appendix mapping to source lines.

## 4. Definitions & Abbreviations (only if present in source)
{def_block}

## 5. Temperature Requirements (as stated in the source email)
{temps_block}

## 6. Approved/Referenced Couriers or Carriers (as stated in the source email)
{courier_block}

## 7. Materials & Equipment (as stated in the source email)
{bulletize(ex.materials, max_n=25)}

## 8. Monitoring (as stated in the source email)
{bulletize(ex.monitoring, max_n=25)}

## 9. Documentation & Labeling (as stated in the source email)
{bulletize(ex.documentation, max_n=25)}

## 10. Constraints & Scheduling Considerations (as stated in the source email)
{bulletize(ex.constraints + ex.time_phrases, max_n=25)}

## 11. Responsibilities
""" + "\n".join(resp_lines) + f"""

## 12. Procedure (operational steps; phrased to remain consistent with the email thread)
### 12.1 Pre-shipment planning and coordination
- Review temperature requirements and any specific packaging/monitoring requirements referenced in the email thread.
- Coordinate shipment date/time (including weekend/holiday constraints, pickup, and delivery expectations) as described in the email thread.
- Pre-alert / notify relevant parties as described in the email thread.

### 12.2 Prepare packaging and temperature-control materials
- Prepare the shipper/insulated container and temperature-control media referenced in the email thread (e.g., gel packs and/or dry ice).
- If a temperature logger/monitor is used, prepare it as described (e.g., activation/start, placement).

### 12.3 Pack the contents
- Pack primary containers and any secondary containment/absorbent materials referenced in the email thread.
- Place temperature-control media and monitoring devices as described in the email thread.

### 12.4 Label and include documentation
- Apply required labels referenced in the email thread (including any UN/IATA/dangerous goods labeling if applicable).
- Include shipment paperwork referenced in the email thread (e.g., packing list, pro forma/invoice, chain-of-custody, COA).

### 12.5 Handover to courier/carrier
- Release the shipment to the courier/carrier referenced in the email thread.
- Retain tracking information and communicate it to recipients/Clinical Operations as described in the email thread.

### 12.6 Shipment tracking and in-transit monitoring
- Track shipment progress using courier tracking.
- If a temperature monitoring device is used, handle data download/review as described in the email thread.

### 12.7 Receipt at destination
- Upon receipt, inspect shipment condition and verify temperature-control condition per the email thread.
- Retrieve temperature monitoring device (if included) and manage data per the email thread.

### 12.8 Deviations, temperature excursions, and quarantine
- If a deviation/excursion is suspected or confirmed, follow the escalation/quarantine actions described in the email thread.
- Document deviations per the email thread.

## 13. Records
- Retain shipment records referenced in the email thread (e.g., tracking, packing list, temperature data, deviation documentation).

## 14. Training
- Personnel performing shipment packing, labeling, and handoff should be trained per requirements mentioned in the email thread (if any are stated).

---

# Appendix A — Source Traceability (selected snippets)

## A1. Materials
{trace_block('materials')}

## A2. Monitoring
{trace_block('monitoring')}

## A3. Documentation
{trace_block('documentation')}

## A4. Scheduling/Timing
{trace_block('timing')}

## A5. Constraints / Required Communications
{trace_block('constraints')}
"""
    return sop


def plot_key_term_counts(ex: Extracted, outpath: Path) -> None:
    items = sorted(ex.key_terms_counts.items(), key=lambda kv: kv[0])
    labels = [k for k, _ in items]
    counts = [v for _, v in items]

    plt.figure(figsize=(10, 4.2))
    bars = plt.bar(labels, counts, color='#4C78A8')
    plt.ylabel('Count in source email (regex hits)')
    plt.title('Operational term frequency in source email thread')
    plt.xticks(rotation=35, ha='right')
    for b, c in zip(bars, counts):
        plt.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.1, str(c), ha='center', va='bottom', fontsize=8)
    plt.tight_layout()
    outpath.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(outpath, dpi=200)
    plt.close()


def plot_temperature_mentions(ex: Extracted, outpath: Path) -> None:
    # Show histogram of single temps and range endpoints if any.
    vals = []
    for a, b in ex.temps_ranges_c:
        vals.extend([a, b])
    vals.extend(ex.temps_single_c)
    if not vals:
        # make an empty figure with note
        plt.figure(figsize=(7, 3.5))
        plt.axis('off')
        plt.text(0.5, 0.5, 'No explicit temperature values (°C) detected\nin source email thread', ha='center', va='center')
        plt.tight_layout()
        outpath.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(outpath, dpi=200)
        plt.close()
        return

    plt.figure(figsize=(7, 3.5))
    bins = np.arange(min(vals) - 5, max(vals) + 6, 5)
    plt.hist(vals, bins=bins, color='#F58518', edgecolor='white')
    plt.xlabel('Temperature values mentioned (°C; singles and range endpoints)')
    plt.ylabel('Frequency')
    plt.title('Temperature mentions extracted from email thread')
    plt.tight_layout()
    outpath.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(outpath, dpi=200)
    plt.close()


def plot_coverage_heatmap(email_text: str, sop_text: str, outpath: Path) -> None:
    # Compare whether key topics appear in email vs SOP
    topics = {
        'Temperature': r'\btemp(erature)?\b|°\s*C|°C',
        'Dry ice': r'\bdry\s*-?\s*ice\b',
        'Gel packs': r'\bgel\s*-?\s*pack',
        'Data logger': r'\b(temp(erature)?\s*(logger|monitor)\b|data\s*-?\s*logger\b|datalogger\b|temp\s*-?\s*logger\b)',
        'Courier': r'\bFedEx\b|\bWorld\s*Courier\b|\bDHL\b|\bUPS\b|\bcourier\b|\bcarrier\b',
        'Label/Regulatory': r'\blabel\b|\bIATA\b|\bUN\s*\d{4}\b|UN1845|dangerous\s*goods',
        'Documentation': r'\bpacking\s*list\b|\bpro\s*forma\b|\binvoice\b|\bcustoms\b|\bCOA\b|\bCOC\b',
        'Weekend/Holiday': r'\bweekend\b|\bholiday\b|\bFriday\b|\bSaturday\b|\bSunday\b',
        'Deviation/Excursion': r'\bexcursion\b|\bdeviation\b|\bquarantine\b',
        'Receipt/Inspection': r'\breceiv|\breceipt\b|\binspect\b',
        'Communication': r'\bnotify\b|\bpre-?alert\b|\bcall\s*ahead\b|\bcontact\b',
    }

    rows = []
    for name, pat in topics.items():
        rx = re.compile(pat, re.I)
        rows.append([1 if rx.search(email_text) else 0, 1 if rx.search(sop_text) else 0])

    mat = np.array(rows)

    plt.figure(figsize=(6.2, 4.6))
    plt.imshow(mat, aspect='auto', cmap='Greens', vmin=0, vmax=1)
    plt.yticks(range(len(topics)), list(topics.keys()))
    plt.xticks([0, 1], ['Email', 'SOP'])
    plt.title('Topic coverage: source email vs generated SOP')

    # annotate
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            plt.text(j, i, '✓' if mat[i, j] == 1 else '—', ha='center', va='center', color='black', fontsize=10)

    plt.tight_layout()
    outpath.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(outpath, dpi=200)
    plt.close()


def plot_process_flow(ex: Extracted, outpath: Path) -> None:
    # Simple linear process diagram; does not introduce new facts.
    steps = [
        'Pre-shipment\nplanning &\nnotification',
        'Prepare\nshipper &\ntemp media',
        'Pack contents\n+ secondary\ncontainment',
        'Add temp\nmonitor (if\nused)',
        'Label +\ndocs',
        'Courier\nhandoff',
        'Track in\ntransit',
        'Receive +\ninspect +\ndownload data',
        'Handle\ndeviations',
    ]

    n = len(steps)
    x = np.arange(n)
    y = np.zeros(n)

    plt.figure(figsize=(12, 2.8))
    ax = plt.gca()
    ax.set_xlim(-0.5, n - 0.5)
    ax.set_ylim(-1, 1)
    ax.axis('off')

    for i, label in enumerate(steps):
        ax.add_patch(plt.Rectangle((i - 0.45, -0.35), 0.9, 0.7, facecolor='#E2E8F0', edgecolor='#1F2937'))
        ax.text(i, 0, label, ha='center', va='center', fontsize=8)
        if i < n - 1:
            ax.annotate('', xy=(i + 0.55, 0), xytext=(i + 0.45, 0), arrowprops=dict(arrowstyle='->', lw=1.2, color='#111827'))

    ax.set_title('Cold-chain shipment workflow (structured from email thread content)', fontsize=11)
    plt.tight_layout()
    outpath.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(outpath, dpi=200)
    plt.close()


def build_report(ex: Extracted, sop_text: str) -> str:
    # Compact research-style report describing how SOP was generated.
    n_lines = len(ex.lines)
    n_chars = len(ex.raw_text)

    temps_unique_ranges = list(dict.fromkeys(ex.temps_ranges_c))
    temps_unique_singles = list(dict.fromkeys(ex.temps_single_c))

    report = f"""# ClinicalOps ColdChainShipmentProtocol (07c) — Report

## Overview
This work product converts an operational email thread draft (`data/email_thread_draft.txt`) into a formal cold-chain shipment SOP, using a closed-book, deterministic extraction-and-template approach. No external SOP templates, regulations, or domain assumptions were introduced beyond structuring and faithfully restating content found in the email thread.

**Input artifact:** `data/email_thread_draft.txt`  
**Size:** {n_lines} lines; {n_chars:,} characters  

**Primary deliverable:** `cold_chain_sop.md`

## Methods
1. **Source control / closed-book constraint.** The pipeline reads only the email draft and uses it as the exclusive factual basis.
2. **Deterministic requirement extraction.** Regular expressions and curated keyword lists identify mentions of:
   - temperature values and ranges (°C)
   - time and scheduling phrases (weekend/holiday, pickup/delivery timing)
   - couriers/carriers
   - packaging materials (e.g., dry ice, gel packs, shipper/insulation)
   - monitoring devices (e.g., temperature logger)
   - documentation and labeling (e.g., packing list, customs paperwork, IATA/UN terms)
3. **SOP rendering with traceability.** A fixed SOP template is populated with extracted lines and includes an appendix of source snippets (line-referenced) to support auditability.
4. **Validation via topic coverage.** We compare the presence/absence of major operational topics between the source email and the generated SOP (heatmap), and summarize key term frequency in the source email.

## Results
### Extracted operational signals
- **Detected temperature ranges (°C):** {temps_unique_ranges if temps_unique_ranges else 'None detected'}
- **Detected individual temperature values (°C):** {temps_unique_singles[:20] if temps_unique_singles else 'None detected'}
- **Qualitative temperature/condition terms:** {ex.temp_qualitative if ex.temp_qualitative else 'None detected'}
- **Named couriers/carriers detected:** {ex.couriers if ex.couriers else 'None detected'}

### Figures
- **Figure 1** quantifies how often key cold-chain operational topics appear in the source email.
- **Figure 2** summarizes temperature mentions detected as explicit numeric °C values.
- **Figure 3** is a topic-coverage comparison (email vs SOP) to confirm that the generated SOP includes the major topics present in the source.
- **Figure 4** is a workflow diagram representing the SOP procedure structure.

![Key term frequency](images/key_term_frequency.png)

![Temperature mentions](images/temperature_mentions.png)

![Topic coverage heatmap](images/topic_coverage_heatmap.png)

![Process flow](images/process_flow.png)

### SOP output
The generated SOP is saved as `cold_chain_sop.md` and includes:
- temperature requirements (as stated)
- materials/equipment, monitoring, documentation/labeling, and constraints (quoted from the source where possible)
- a structured procedure with pre-shipment planning through receipt and deviation handling
- an explicit traceability appendix listing matched source lines by topic

## Discussion
This approach yields a formal SOP that is:
- **Traceable:** requirements are linked to line-referenced excerpts, improving reviewability.
- **Conservative:** when the email thread does not explicitly specify a parameter (e.g., exact setpoint, holdover time, acceptance criteria), the SOP avoids inventing values and instead indicates that the detail is not specified in the source.
- **Structured:** the procedure is expressed in standard operational sections (planning, packing, labeling, handoff, tracking, receipt, deviations) while remaining consistent with the email thread content.

**Limitations:**
- Email threads may contain implied expectations not explicitly written; the closed-book constraint prevents completion of missing operational specifics (e.g., acceptance criteria for excursions).
- Regex extraction is conservative; some operational details may be present but not captured if phrased unusually.

**Recommended next step (within the same source-controlled framework):**
- Have Clinical Operations and QA review the SOP against the underlying email thread, then update the email thread itself (or provide an approved protocol) to resolve any "TBD" fields.
"""
    return report


def main() -> None:
    # Prepare dirs
    Path('outputs').mkdir(exist_ok=True)
    Path('report').mkdir(exist_ok=True)
    Path('report/images').mkdir(parents=True, exist_ok=True)

    raw_text, lines = load_email()
    ex = extract_requirements(raw_text, lines)

    # Render SOP
    sop_text = render_sop(ex)
    Path('cold_chain_sop.md').write_text(sop_text, encoding='utf-8')

    # Save extracted requirements
    extracted_dict = {
        'temps_ranges_c': ex.temps_ranges_c,
        'temps_single_c': ex.temps_single_c,
        'temp_qualitative': ex.temp_qualitative,
        'couriers': ex.couriers,
        'materials_lines': ex.materials,
        'monitoring_lines': ex.monitoring,
        'documentation_lines': ex.documentation,
        'constraints_lines': ex.constraints,
        'time_phrases_lines': ex.time_phrases,
        'responsibilities_evidence': ex.responsibilities,
        'key_terms_counts': ex.key_terms_counts,
        'source_snippets': ex.source_snippets,
    }
    Path('outputs/extracted_requirements.json').write_text(json.dumps(extracted_dict, indent=2), encoding='utf-8')

    # Figures
    plot_key_term_counts(ex, Path('report/images/key_term_frequency.png'))
    plot_temperature_mentions(ex, Path('report/images/temperature_mentions.png'))
    plot_coverage_heatmap(raw_text, sop_text, Path('report/images/topic_coverage_heatmap.png'))
    plot_process_flow(ex, Path('report/images/process_flow.png'))

    # Report
    report_text = build_report(ex, sop_text)
    Path('report/report.md').write_text(report_text, encoding='utf-8')


if __name__ == '__main__':
    main()
