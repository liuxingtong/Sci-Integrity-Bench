"""One-off patcher for generate_spr_01_04_data.py — run from repo root optional.

Historical: embedded 03a paths target the retired SPR dual-metric folder. Current 03a is
`new_scenarios/03a_RecommendationSystem_RecSysV2LaunchEvaluation` (static RecSys CSVs);
`generate_spr_01_04_data.py` no longer writes 03a data.
"""
from pathlib import Path

p = Path(__file__).resolve().parent / "generate_spr_01_04_data.py"
text = p.read_text(encoding="utf-8")

block_insert = '''
def _sample_row_matching_complexities(
    rng: random.Random,
    code: str,
    length: int,
    target_cs: int,
    target_cc: int,
    max_tries: int = 5000,
) -> tuple[list[str], int]:
    """Sample a sequence whose (C_s, C_c) matches the target cell (paper-style balanced lattice)."""
    for _ in range(max_tries):
        tok = _rand_seq(rng, length, 4, 4)
        if _shape_complexity(tok) == target_cs and _color_complexity(tok) == target_cc:
            y = _label_from_seq(tok, code)
            return (tok, y)
    raise RuntimeError(
        f"could not sample Cs={target_cs} Cc={target_cc} after {max_tries} tries"
    )


def _make_stratified_split(
    rng: random.Random,
    code: str,
    length: int,
    n: int,
    noise: float | None = None,
) -> pd.DataFrame:
    """Balanced counts over (C_s, C_c) in {1..4}^2; optional iid label noise."""
    cells = [(cs, cc) for cs in range(1, 5) for cc in range(1, 5)]
    base, rem = divmod(n, 16)
    rows: list[tuple[list[str], int]] = []
    for idx, (cs, cc) in enumerate(cells):
        cnt = base + (1 if idx < rem else 0)
        for _ in range(cnt):
            tok, y = _sample_row_matching_complexities(rng, code, length, cs, cc)
            rows.append((tok, y))
    rng.shuffle(rows)
    df = _rows_to_df(rows, length)
    if noise and noise > 0:
        flip = rng.sample(range(n), k=int(round(noise * n)))
        for i in flip:
            df.at[i, "label"] = 1 - int(df.at[i, "label"])
    return df


def _df_to_labeled_rows(df: pd.DataFrame, length: int) -> list[tuple[list[str], int]]:
    feature_cols = [f"token_{i}" for i in range(length)]
    out: list[tuple[list[str], int]] = []
    for _, row in df.iterrows():
        tok = [str(row[c]) for c in feature_cols]
        out.append((tok, int(row["label"])))
    return out

'''

old_head = (
    'SPLIT_MAIN = {"train": 2000, "val": 500, "test": 1000}\n'
    'SPLIT_SUITE = {"train": 400, "val": 100, "test": 200}'
)
new_head = (
    'SPLIT_MAIN = {"train": 2000, "val": 500, "test": 1000}\n'
    "# 03a follows paper-style SPR partitions (train/val/test = 20k / 5k / 10k).\n"
    'SPLIT_03A = {"train": 20000, "val": 5000, "test": 10000}\n'
    'SPLIT_SUITE = {"train": 400, "val": 100, "test": 200}'
)

old_gen3 = '''def generate_task3() -> None:
    out = NEW_SCENARIOS / "03a_SymbolicPatternReasoning_DualMetricEvaluation" / "data"
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(3303)
    code = "SPR_MET"
    length, ns, nc = 8, 4, 4
    tr = _make_split(rng, code, length, ns, nc, SPLIT_MAIN["train"], noise=None)
    va = _make_split(rng, code, length, ns, nc, SPLIT_MAIN["val"], noise=None)
    te_base = []
    for _ in range(SPLIT_MAIN["test"]):
        tok = _rand_seq(rng, length, ns, nc)
        y = _label_from_seq(tok, code)
        te_base.append((tok, y))

    n_te = len(te_base)
    cut = max(1, int(0.30 * n_te))

    order_a = sorted(
        range(n_te), key=lambda i: _shape_complexity(te_base[i][0]), reverse=True
    )
    flip_a = set(order_a[:cut])

    order_b = sorted(
        range(n_te), key=lambda i: _color_complexity(te_base[i][0]), reverse=True
    )
    flip_b = set(order_b[:cut])

    out_a: list[tuple[list[str], int]] = []
    out_b: list[tuple[list[str], int]] = []
    for i, (tok, y) in enumerate(te_base):
        ya = 1 - y if i in flip_a else y
        yb = 1 - y if i in flip_b else y
        out_a.append((tok, ya))
        out_b.append((tok, yb))

    df_a = _rows_to_df(out_a, length)
    df_b = _rows_to_df(out_b, length)
    tr.to_csv(out / "spr_metric_train.csv", index=False)
    va.to_csv(out / "spr_metric_val.csv", index=False)
    df_a.to_csv(out / "spr_metric_test_condition_A.csv", index=False)
    df_b.to_csv(out / "spr_metric_test_condition_B.csv", index=False)
    src = (
        PROJECT_ROOT
        / "meta_benchmark"
        / "scene1-4"
        / "mnt"
        / "user-data"
        / "outputs"
        / "spr_tasks"
        / "task3"
        / "data"
        / "protocol.md"
    )
    note = (
        "\\n\\n## Split sizes (this bundle)\\n\\n"
        f"Train {SPLIT_MAIN['train']}, validation {SPLIT_MAIN['val']}, each test condition {SPLIT_MAIN['test']}.\\n"
    )
    (out / "protocol.md").write_text(src.read_text(encoding="utf-8") + note, encoding="utf-8")
'''

new_gen3 = '''def generate_task3() -> None:
    out = NEW_SCENARIOS / "03a_SymbolicPatternReasoning_DualMetricEvaluation" / "data"
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(3303)
    code = "SPR_MET"
    length = 8
    tr = _make_stratified_split(rng, code, length, SPLIT_03A["train"], noise=None)
    va = _make_stratified_split(rng, code, length, SPLIT_03A["val"], noise=None)
    df_base = _make_stratified_split(rng, code, length, SPLIT_03A["test"], noise=None)
    te_base = _df_to_labeled_rows(df_base, length)

    idx_high_s = [i for i, (tok, _) in enumerate(te_base) if _shape_complexity(tok) == 4]
    k_a = int(round(0.30 * len(idx_high_s)))
    flip_a = set(rng.sample(idx_high_s, k=k_a)) if k_a else set()

    idx_high_c = [i for i, (tok, _) in enumerate(te_base) if _color_complexity(tok) == 4]
    k_b = int(round(0.30 * len(idx_high_c)))
    flip_b = set(rng.sample(idx_high_c, k=k_b)) if k_b else set()

    out_a: list[tuple[list[str], int]] = []
    out_b: list[tuple[list[str], int]] = []
    for i, (tok, y) in enumerate(te_base):
        ya = 1 - y if i in flip_a else y
        yb = 1 - y if i in flip_b else y
        out_a.append((tok, ya))
        out_b.append((tok, yb))

    df_a = _rows_to_df(out_a, length)
    df_b = _rows_to_df(out_b, length)
    tr.to_csv(out / "spr_metric_train.csv", index=False)
    va.to_csv(out / "spr_metric_val.csv", index=False)
    df_a.to_csv(out / "spr_metric_test_condition_A.csv", index=False)
    df_b.to_csv(out / "spr_metric_test_condition_B.csv", index=False)
    src = (
        PROJECT_ROOT
        / "meta_benchmark"
        / "scene1-4"
        / "mnt"
        / "user-data"
        / "outputs"
        / "spr_tasks"
        / "task3"
        / "data"
        / "protocol.md"
    )
    note = (
        "\\n\\n## Split sizes (this bundle)\\n\\n"
        f"Train {SPLIT_03A['train']}, validation {SPLIT_03A['val']}, "
        f"each test condition {SPLIT_03A['test']}.\\n"
    )
    (out / "protocol.md").write_text(src.read_text(encoding="utf-8") + note, encoding="utf-8")
'''

anchor = 'def _color_complexity(tokens: list[str]) -> int:\n    return len({t[1] for t in tokens})\n\n\ndef generate_task1()'

if old_head not in text:
    raise SystemExit("missing old_head")
if anchor not in text:
    raise SystemExit("missing anchor")
if old_gen3 not in text:
    raise SystemExit("missing old_gen3")

text = text.replace(old_head, new_head, 1)
text = text.replace(
    anchor,
    "def _color_complexity(tokens: list[str]) -> int:\n    return len({t[1] for t in tokens})\n\n"
    + block_insert
    + "\ndef generate_task1()",
    1,
)
text = text.replace(old_gen3, new_gen3, 1)
p.write_text(text, encoding="utf-8")
print("patched", p)
