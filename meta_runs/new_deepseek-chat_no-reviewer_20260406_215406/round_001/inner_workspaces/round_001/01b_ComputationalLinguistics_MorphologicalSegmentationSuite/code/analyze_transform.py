import pandas as pd

code = 'KWP'
train_path = f'../data/corpora/{code}/train.csv'
train_df = pd.read_csv(train_path)

print("Analyzing transformation pattern:")
for i in range(len(train_df)):
    source = train_df['source'].iloc[i]
    target = train_df['target'].iloc[i]
    
    print(f"\nSample {i}:")
    print(f"  Source: {source}")
    print(f"  Target: {target}")
    
    # Try to understand the mapping
    # Source is "wordNxyz" repeated 3 times
    # Let's split source into characters
    source_chars = list(source)
    target_chars = list(target)
    
    print(f"  Source chars: {source_chars}")
    print(f"  Target chars: {target_chars}")
    
    # Remove spaces from target for comparison
    target_no_spaces = target.replace(' ', '')
    print(f"  Target without spaces: {target_no_spaces}")
    print(f"  Target length without spaces: {len(target_no_spaces)}")
    print(f"  Source length: {len(source)}")
    
    # Check if target is a subsequence of source
    # Find target_no_spaces in source
    if target_no_spaces in source:
        idx = source.find(target_no_spaces)
        print(f"  Target found in source at index {idx}")
    else:
        print(f"  Target NOT found as substring in source")
        
    # Check character by character alignment
    src_idx = 0
    tgt_idx = 0
    alignments = []
    while src_idx < len(source) and tgt_idx < len(target):
        if target[tgt_idx] == ' ':
            alignments.append((' ', source[src_idx] if src_idx < len(source) else '?'))
            tgt_idx += 1
        else:
            alignments.append((target[tgt_idx], source[src_idx]))
            tgt_idx += 1
            src_idx += 1
    
    print(f"  First 20 alignments: {alignments[:20]}")
    
    # Check if it's consistent
    mismatches = [(t, s) for t, s in alignments if t != ' ' and t != s]
    if mismatches:
        print(f"  Mismatches: {mismatches}")
    else:
        print(f"  All non-space characters match source")
