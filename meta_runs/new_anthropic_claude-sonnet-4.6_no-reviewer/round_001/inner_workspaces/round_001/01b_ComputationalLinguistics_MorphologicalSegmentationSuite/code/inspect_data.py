import csv
import os

codes = ['KWP','ZTE','CWR','PUV','WVZ','BJP','DWN','MDA']
for c in codes:
    print(f'\n=== {c} ===')
    for split in ['train', 'val', 'test']:
        path = f'data/corpora/{c}/{split}.csv'
        rows = list(csv.DictReader(open(path, encoding='utf-8')))
        print(f'  {split}: {len(rows)} rows')
        if rows:
            print(f'    first: {rows[0]}')
            print(f'    last:  {rows[-1]}')
