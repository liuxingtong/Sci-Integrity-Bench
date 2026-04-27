import pandas as pd
import os

os.makedirs('outputs', exist_ok=True)

try:
    df = pd.read_csv('data/field_year_panel.csv')
    print('Data loaded successfully')
    print('Shape:', df.shape)
    print('Columns:', list(df.columns))
    
    with open('outputs/test_data.txt', 'w') as f:
        f.write(f'Shape: {df.shape}\n')
        f.write(f'Columns: {list(df.columns)}\n')
        f.write(f'\nFirst 5 rows:\n{df.head()}\n')
        f.write(f'\nDescribe:\n{df.describe()}\n')
        f.write(f'\nDtypes:\n{df.dtypes}\n')
    print('Test data saved')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
    with open('outputs/test_error.txt', 'w') as f:
        f.write(str(e))
