from pathlib import Path

p = Path(__file__).resolve().parent / "_authoring_private" / "SCENARIO_TRAP_INDEX.md"
lines = p.read_text(encoding="utf-8").splitlines()
out = []
for L in lines:
    if L.startswith("3. **RIGOR"):
        L = "3. **RIGOR 组**：`04` → `06` → `12` → `13` → `16` → `18`  "
    elif L.startswith("4. **COGN"):
        L = "4. **COGN 组**：`09` → `17`  "
    out.append(L)
p.write_text("\n".join(out), encoding="utf-8")
print("ok")
