import sys
print('Python version:', sys.version)
print('Starting...')

try:
    import pandas as pd
    print('pandas imported')
    df = pd.read_csv('data/sensor_panel_timeseries.csv')
    print('Data loaded, shape:', df.shape)
    print('Columns:', df.columns.tolist())
    print('First row:', df.iloc[0].to_dict())
except Exception as e:
    print('Error:', e)
    import traceback
    traceback.print_exc()

with open('outputs/test_output.txt', 'w') as f:
    f.write('test complete\n')
    try:
        import pandas as pd
        df = pd.read_csv('data/sensor_panel_timeseries.csv')
        f.write(f'Shape: {df.shape}\n')
        f.write(f'Columns: {df.columns.tolist()}\n')
        f.write(f'Head:\n{df.head().to_string()}\n')
        f.write(f'Describe:\n{df.describe().to_string()}\n')
        f.write(f'Assets: {df["asset_id"].unique().tolist()}\n')
        f.write(f'Zones: {df["zone"].unique().tolist()}\n')
        f.write(f'Quality flags: {df["quality_flag"].value_counts().to_dict()}\n')
    except Exception as e:
        f.write(f'Error: {e}\n')
        import traceback
        f.write(traceback.format_exc())
