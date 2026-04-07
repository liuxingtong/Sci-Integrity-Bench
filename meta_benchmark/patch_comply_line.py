from pathlib import Path

p = Path(__file__).resolve().parent / "_authoring_private" / "SCENARIO_TRAP_INDEX.md"
t = p.read_text(encoding="utf-8")
# normalize common variants
old = "1. **COMPLY 组**：`07` → `11` → `08`"
new = "1. **COMPLY 组**：`07` → `11` → `08` → `15`"
if old not in t:
    # try without arrow unicode
    for o, n in [
        ("`07` → `11` → `08`  ", "`07` → `11` → `08` → `15`  "),
        ("`07` → `11` → `08`", "`07` → `11` → `08` → `15`"),
    ]:
        if o in t:
            t = t.replace(o, n, 1)
            break
else:
    t = t.replace(old, new)
p.write_text(t, encoding="utf-8")
print("done")
