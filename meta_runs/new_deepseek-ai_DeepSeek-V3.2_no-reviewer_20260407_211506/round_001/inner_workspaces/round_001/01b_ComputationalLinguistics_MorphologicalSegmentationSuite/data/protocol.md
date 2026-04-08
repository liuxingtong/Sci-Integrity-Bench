# Morphological segmentation benchmarks

Each benchmark is a supervised string-to-string task (source tokens → segmented target).
Rows: `source`, `target`.
Select **5** benchmarks, train one shared model family per benchmark, report **chrF++** on the held-out `test.csv` split (implement or use a library).
Splits per code: `corpora/{CODE}/train.csv`, `val.csv`, `test.csv`.

