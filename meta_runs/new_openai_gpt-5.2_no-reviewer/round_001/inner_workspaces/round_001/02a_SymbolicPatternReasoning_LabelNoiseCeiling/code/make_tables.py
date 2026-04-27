import json
import pandas as pd

res = pd.read_csv('outputs/results_table.csv')
# Order: descending val, then test
res = res.sort_values(['val_acc','test_acc'], ascending=False)

def fmt_pct(x):
    return f"{100*x:.2f}%"

rows = []
for _, r in res.iterrows():
    rows.append({
        'Model': r['model'],
        'Params': r['params'],
        'Val acc': fmt_pct(r['val_acc']),
        'Test acc': fmt_pct(r['test_acc']),
    })

df = pd.DataFrame(rows)

# Simple markdown table writer (no external deps)

def md_table(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    # compute column widths
    widths = {c: max(len(c), *(len(str(v)) for v in df[c].tolist())) for c in cols}
    def line(sep='|', pad=' '):
        return sep + sep.join([pad + c.ljust(widths[c]) + pad for c in cols]) + sep
    header = line()
    rule = '|' + '|'.join([' ' + ('-'*widths[c]) + ' ' for c in cols]) + '|'
    body_lines = []
    for _, row in df.iterrows():
        body_lines.append('|' + '|'.join([' ' + str(row[c]).ljust(widths[c]) + ' ' for c in cols]) + '|')
    return '\n'.join([header, rule] + body_lines)

open('outputs/accuracy_table.md','w',encoding='utf-8').write(md_table(df))

ce = json.load(open('outputs/label_noise_ceiling.json'))
order = ['train','val','test','all']
rows2 = []
for k in order:
    d = ce[k]
    rows2.append({
        'Split': k,
        'N': int(d['n']),
        'Unique seq': int(d['unique']),
        'Conflicting unique': int(d['conflicting_unique']),
        'LB error': f"{100*d['lb_error']:.4f}%",
        'Ceiling': f"{100*d['ceiling']:.4f}%",
    })
df2 = pd.DataFrame(rows2)
open('outputs/ceiling_table.md','w',encoding='utf-8').write(md_table(df2))

print('Wrote outputs/accuracy_table.md and outputs/ceiling_table.md')
