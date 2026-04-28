import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

train = pd.read_csv('data/train.csv')

chars = ['*', '.', 'u', 'v', 'w', 'x', 'y', 'z']
char_to_idx = {c: i for i, c in enumerate(chars)}

transitions = np.zeros((8, 8))

for s in train['symbol_series']:
    for i in range(len(s) - 1):
        c1 = s[i]
        c2 = s[i+1]
        transitions[char_to_idx[c1], char_to_idx[c2]] += 1

plt.figure(figsize=(8, 6))
sns.heatmap(transitions, xticklabels=chars, yticklabels=chars, annot=True, fmt='g')
plt.title('Character Transitions')
plt.savefig('outputs/transitions.png')

# Also let's check transitions with wrap-around (if it's a folded light curve)
wrap_transitions = np.zeros((8, 8))
for s in train['symbol_series']:
    c1 = s[-1]
    c2 = s[0]
    wrap_transitions[char_to_idx[c1], char_to_idx[c2]] += 1

print("Wrap around transitions:")
print(pd.DataFrame(wrap_transitions, index=chars, columns=chars))
