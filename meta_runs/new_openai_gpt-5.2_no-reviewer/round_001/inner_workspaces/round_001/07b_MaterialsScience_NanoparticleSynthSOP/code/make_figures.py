"""Generate figures summarizing the conversion of lab notes into a structured SOP.

Because the input is unstructured text, figures focus on:
  - Frequency of unit mentions (proxy for what parameters are specified)
  - Frequency of action keywords (proxy for process steps)
  - A simple process schematic (text-based flow rendered as a figure)

Outputs are PNGs saved in report/images/.
"""

from __future__ import annotations

import re
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
IMG = ROOT / "report" / "images"
DATA = ROOT / "data" / "lab_scratch.txt"

ACTION_KEYWORDS = [
    "add",
    "charge",
    "mix",
    "stir",
    "heat",
    "cool",
    "reflux",
    "inject",
    "quench",
    "age",
    "incubate",
    "centrifuge",
    "wash",
    "decant",
    "filter",
    "dialyze",
    "sonicate",
    "degas",
    "nitrogen",
    "argon",
    "vacuum",
    "dry",
    "resuspend",
    "ph",
]


def save_unit_frequency():
    mentions_path = OUT / "mentions.csv"
    if not mentions_path.exists():
        return
    df = pd.read_csv(mentions_path)
    df["unit"] = df["unit"].astype(str)

    counts = df["unit"].value_counts().head(15)[::-1]

    plt.figure(figsize=(8, 5))
    plt.barh(counts.index, counts.values, color="#4C78A8")
    plt.xlabel("Count in lab_scratch.txt")
    plt.title("Most frequent quantitative units in raw lab notes")
    plt.tight_layout()
    IMG.mkdir(parents=True, exist_ok=True)
    plt.savefig(IMG / "unit_frequency.png", dpi=200)
    plt.close()


def save_action_keyword_frequency():
    text = DATA.read_text(errors="ignore")
    low = text.lower()

    rows = []
    for k in ACTION_KEYWORDS:
        # count whole-word occurrences where feasible
        if k.isalpha():
            c = len(re.findall(rf"\b{k}\b", low))
        else:
            c = low.count(k)
        rows.append((k, c))

    df = pd.DataFrame(rows, columns=["keyword", "count"]).sort_values("count", ascending=False)
    df = df[df["count"] > 0].head(15)
    df = df.iloc[::-1]

    plt.figure(figsize=(8, 5))
    plt.barh(df["keyword"], df["count"], color="#F58518")
    plt.xlabel("Occurrences")
    plt.title("Most frequent process action keywords in raw lab notes")
    plt.tight_layout()
    IMG.mkdir(parents=True, exist_ok=True)
    plt.savefig(IMG / "action_keyword_frequency.png", dpi=200)
    plt.close()


def save_quant_mentions_position_plot():
    mentions_path = OUT / "mentions.csv"
    if not mentions_path.exists():
        return
    df = pd.read_csv(mentions_path)
    if df.empty:
        return
    # normalize units into broad classes
    def cls(u: str) -> str:
        u = str(u)
        if u.lower() in ["ml", "ml", "l", "ul", "µl"]:
            return "volume"
        if u.lower() in ["g", "mg", "kg", "ug", "µg"]:
            return "mass"
        if u in ["M", "mM", "uM", "µM", "nM"]:
            return "concentration"
        if u in ["°C", "C", "K"]:
            return "temperature"
        if u.lower() in ["min", "mins", "minute", "minutes", "h", "hr", "hrs", "hour", "hours"]:
            return "time"
        if u.lower() in ["rpm", "rcf", "xg"]:
            return "mix/spin"
        if u in ["%", "wt%"]:
            return "percent"
        return "other"

    df["class"] = df["unit"].map(cls)

    plt.figure(figsize=(9, 4.5))
    # jitter y positions by class
    classes = [c for c in ["volume","mass","concentration","temperature","time","mix/spin","percent","other"] if c in set(df["class"])]
    y_map = {c:i for i,c in enumerate(classes)}
    y = df["class"].map(y_map).astype(float)
    x = df["line_no"].astype(int)
    plt.scatter(x, y + 0.08*(pd.Series(range(len(df)))%5 - 2), s=10, alpha=0.6)
    plt.yticks(list(y_map.values()), list(y_map.keys()))
    plt.xlabel("Line number in lab_scratch.txt")
    plt.title("Where quantitative parameters appear in the raw notes (by unit class)")
    plt.grid(axis='x', alpha=0.2)
    plt.tight_layout()
    IMG.mkdir(parents=True, exist_ok=True)
    plt.savefig(IMG / "quant_mentions_positions.png", dpi=200)
    plt.close()


def save_process_flow_diagram():
    # Render a simple flow diagram as a figure for compatibility with markdown viewers.
    steps = [
        "Raw notes (lab_scratch.txt)",
        "Heuristic parsing (quantities, actions, holds)",
        "Structured logs (mentions.csv, actions.csv)",
        "Pilot-scale SOP template + traceability excerpt",
        "Executable nanoparticle_sop.md",
    ]

    plt.figure(figsize=(10, 3))
    ax = plt.gca()
    ax.axis("off")

    x0, y0 = 0.05, 0.55
    dx = 0.18
    for i, s in enumerate(steps):
        x = x0 + i * dx
        ax.add_patch(
            plt.Rectangle((x, y0), 0.16, 0.25, fill=False, linewidth=1.5)
        )
        ax.text(x + 0.08, y0 + 0.125, s, ha="center", va="center", fontsize=9, wrap=True)
        if i < len(steps) - 1:
            ax.annotate(
                "",
                xy=(x + 0.16, y0 + 0.125),
                xytext=(x + 0.18, y0 + 0.125),
                arrowprops=dict(arrowstyle="->", lw=1.5),
            )

    plt.title("Conversion pipeline from raw notes to pilot-scale SOP")
    plt.tight_layout()
    IMG.mkdir(parents=True, exist_ok=True)
    plt.savefig(IMG / "conversion_flow.png", dpi=200)
    plt.close()


def main():
    IMG.mkdir(parents=True, exist_ok=True)
    save_unit_frequency()
    save_action_keyword_frequency()
    save_quant_mentions_position_plot()
    save_mention_density_plot()
    save_process_flow_diagram()


if __name__ == "__main__":
    main()
