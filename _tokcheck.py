raw = open(
    r"f:\Aworks\1readraft\ai_scientist\meta_runs\new_Pro_moonshotai_Kimi-K2.5_no-reviewer\round_001\inner_workspaces\round_001\01b_ComputationalLinguistics_MorphologicalSegmentationSuite\trace.json",
    "rb",
).read()
i = raw.find(b"list_files:0")
seg = raw[i - 50 : i + 45]
print(seg)
print(seg.hex())
