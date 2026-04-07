import pandas as pd

code = 'KWP'
train_path = f'../data/corpora/{code}/train.csv'
train_df = pd.read_csv(train_path)

print("Analyzing pattern in KWP train data:")
for i in range(min(5, len(train_df))):
    source = train_df['source'].iloc[i]
    target = train_df['target'].iloc[i]
    print(f"\nSample {i}:")
    print(f"  Source: {source}")
    print(f"  Target: {target}")
    
    # Try to understand the transformation
    # The source appears to be "wordNxyz" repeated 3 times
    # Let's check if this is consistent
    if source.startswith('word') and 'xyz' in source:
        # Find the number N
        import re
        match = re.search(r'word(\d+)xyz', source)
        if match:
            N = match.group(1)
            print(f"  Contains pattern: word{N}xyz")
            
            # Check if target matches expected pattern
            expected = f"w o r d {N} x y zw o r d {N} x y z"
            if target == expected:
                print(f"  Target matches expected pattern")
            else:
                print(f"  Target does NOT match expected pattern")
                print(f"  Expected: {expected}")
    
    # Check character by character
    print(f"  Source length: {len(source)}")
    print(f"  Target length: {len(target)}")
    print(f"  Target without spaces: '{target.replace(' ', '')}'")
    print(f"  Source == Target (no spaces)? {source == target.replace(' ', '')}")
