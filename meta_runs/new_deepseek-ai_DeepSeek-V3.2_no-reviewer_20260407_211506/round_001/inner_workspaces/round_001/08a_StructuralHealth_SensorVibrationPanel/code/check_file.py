import csv

with open('data/sensor_panel_timeseries.csv', 'r') as f:
    reader = csv.reader(f)
    rows = list(reader)
    
print(f'Total rows: {len(rows)}')
print('First 10 rows:')
for i, row in enumerate(rows[:10]):
    print(f'{i}: {row}')
    
# Also check raw bytes
print('\nRaw file content (first 200 chars):')
with open('data/sensor_panel_timeseries.csv', 'r') as f:
    content = f.read(200)
    print(repr(content))
    
print('\nFull file content:')
with open('data/sensor_panel_timeseries.csv', 'r') as f:
    print(f.read())