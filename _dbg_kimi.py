path = r"f:\Aworks\1readraft\ai_scientist\tier_benchmark\agent_runner.py"
s = open(path, "r", encoding="utf-8").read()
i = s.find("return []\n    if (")
j = s.find("    out: List[Dict] = []", i)
print(repr(s[i:j]))
