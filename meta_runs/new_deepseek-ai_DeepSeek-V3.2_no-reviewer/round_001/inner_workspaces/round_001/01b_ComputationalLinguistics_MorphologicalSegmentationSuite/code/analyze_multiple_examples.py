import pandas as pd

# Load data
df = pd.read_csv('../data/corpora/KWP/train.csv')

print("Analyzing multiple examples from KWP train set:")
print("=" * 60)

for idx in range(min(5, len(df))):
    source = df.iloc[idx]['source']
    target = df.iloc[idx]['target']
    tokens = target.split()
    
    print(f"\nExample {idx}:")
    print(f"  Source: '{source}' (length {len(source)})")
    print(f"  Target: '{target}'")
    print(f"  Tokens ({len(tokens)}): {tokens}")
    
    # Reconstruct from tokens
    reconstructed = ''.join(tokens)
    print(f"  Reconstructed: '{reconstructed}' (length {len(reconstructed)})")
    
    # Check if reconstructed is a prefix of source
    if source.startswith(reconstructed):
        remaining = source[len(reconstructed):]
        print(f"  ✓ Reconstructed is a prefix of source")
        print(f"  Remaining: '{remaining}' (length {len(remaining)})")
    else:
        print(f"  ✗ Reconstructed is NOT a prefix of source")
    
    # Look for pattern in source
    # Source seems to be triple repetition of something
    if len(source) % 3 == 0:
        third = len(source) // 3
        part1 = source[:third]
        part2 = source[third:2*third]
        part3 = source[2*third:]
        print(f"  Source divided into thirds: '{part1}' | '{part2}' | '{part3}'")
        if part1 == part2 == part3:
            print(f"  ✓ All three parts are identical")
            print(f"  Target appears to segment: {part1[:8]} as chars, then '{part1[8:]}' as one token?")
