# Cell patch segmentation (tabular features)

Each dataset has pre-extracted patch feature rows for prototyping.
Columns: `feat_0` … `feat_31`, `label` (foreground fraction bucket 0–3).
Select **4** dataset IDs from the registry; for each, train a small U-Net **or** a linear/MLP baseline on the provided CSV and report hold-out Dice.
Deliver `cell_seg_report.md`.
