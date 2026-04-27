from pathlib import Path
import re
import pandas as pd

text = Path('data/email_thread_draft.txt').read_text(encoding='utf-8', errors='replace')
lines = text.splitlines()
words = re.findall(r"\b\w+\b", text)

req = pd.read_csv('outputs/extracted_requirements.csv')

rep_path = Path('report/report.md')
rep = rep_path.read_text(encoding='utf-8')
rep = rep.replace('{{N_LINES}}', str(len(lines)))
rep = rep.replace('{{N_WORDS}}', str(len(words)))
rep = rep.replace('{{N_REQ_LINES}}', str(len(req)))

rep_path.write_text(rep, encoding='utf-8')
print('Filled placeholders in', rep_path)
