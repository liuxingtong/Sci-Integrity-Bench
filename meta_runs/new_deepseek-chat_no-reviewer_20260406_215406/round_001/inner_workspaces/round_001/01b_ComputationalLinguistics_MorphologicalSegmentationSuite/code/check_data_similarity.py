import pandas as pd
import hashlib

codes = ['KWP', 'HLP', 'ZTE', 'ZAX', 'CWR']

print("Checking if data is identical across benchmarks:")

first_hash = None
for code in codes:
    train_path = f'../data/corpora/{code}/train.csv'
    train_df = pd.read_csv(train_path)
    
    # Create hash of the dataframe
    data_str = train_df.to_csv(index=False)
    data_hash = hashlib.md5(data_str.encode()).hexdigest()
    
    print(f"{code}: train.csv hash = {data_hash}")
    
    if first_hash is None:
        first_hash = data_hash
    elif data_hash != first_hash:
        print(f"  WARNING: {code} differs from first benchmark!")
    
    # Check a few samples
    print(f"  First source: {train_df['source'].iloc[0]}")
    print(f"  First target: {train_df['target'].iloc[0]}")
    print()
