# -*- coding: utf-8 -*-
p = r"f:/Aworks/1readraft/ai_scientist/meta_benchmark/_authoring_private/TRAP_METHODOLOGY_AND_SCENARIO_REGISTER.md"
t = open(p, "r", encoding="utf-8-sig").read()
start = t.find("## `new_scenarios`")
end = t.find("## 维护须知")
print("start", start, "end", end)
print("HEAD ---")
print(t[:200].replace("\n", "\\n"))
