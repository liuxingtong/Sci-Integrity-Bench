path = r"f:\Aworks\1readraft\ai_scientist\tier_benchmark\agent_runner.py"
with open(path, "r", encoding="utf-8") as f:
    s = f.read()
fn = "def _extract_kimi_native_tool_calls"
start = s.index(fn)
chunk = s[start : start + 400]
# Extract the if-block after first "return []" inside this function
sub = chunk.split("if not content:\n        return []\n", 1)[1]
# sub starts with "    if (\n" or "    out:"
print("sub start repr", repr(sub[:120]))
block_end = sub.index("    out: List[Dict] = []")
actual = sub[:block_end]
with open(r"f:\Aworks\1readraft\ai_scientist\_kimi_block_actual.txt", "w", encoding="utf-8") as f:
    f.write(actual)
old = """    if (
        "redacted_tool_call_begin_kimi" not in content
        and "<|redacted_tool_call_begin_kimi|>" not in content
    ):
        return []
"""
with open(r"f:\Aworks\1readraft\ai_scientist\_kimi_block_expected.txt", "w", encoding="utf-8") as f:
    f.write(old)
print("equal", actual == old)
if actual != old:
    for i, (a, b) in enumerate(zip(actual, old)):
        if a != b:
            print("diff at", i, repr(a), ord(a), repr(b), ord(b))
            break
    print("len actual", len(actual), "len old", len(old))
