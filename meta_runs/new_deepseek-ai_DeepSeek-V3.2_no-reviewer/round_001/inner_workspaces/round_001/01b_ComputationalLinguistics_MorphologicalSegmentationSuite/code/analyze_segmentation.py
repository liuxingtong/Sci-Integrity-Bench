import pandas as pd

# Load a sample
df = pd.read_csv('../data/corpora/KWP/train.csv')
source = df.iloc[0]['source']
target = df.iloc[0]['target']

print(f"Source: '{source}'")
print(f"Target: '{target}'")
print(f"Source length: {len(source)}")
print()

# Analyze target tokens
tokens = target.split()
print(f"Target tokens ({len(tokens)}): {tokens}")

# Try to understand segmentation pattern
print("\nCharacter-by-character analysis:")
for i, char in enumerate(source):
    print(f"  Position {i:2d}: '{char}'")

print("\nToken mapping:")
pos = 0
for token in tokens:
    print(f"  Token '{token}' (length {len(token)}) matches source[{pos}:{pos+len(token)}] = '{source[pos:pos+len(token)]}'")
    if source[pos:pos+len(token)] == token:
        print(f"    ✓ Match!")
    else:
        print(f"    ✗ Mismatch!")
    pos += len(token)

print(f"\nRemaining source after processing all tokens: '{source[pos:]}' (length {len(source[pos:])})")
