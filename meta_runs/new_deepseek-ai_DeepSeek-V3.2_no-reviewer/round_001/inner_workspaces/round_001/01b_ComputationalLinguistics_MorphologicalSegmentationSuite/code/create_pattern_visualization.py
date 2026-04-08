import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Create visualization of the segmentation pattern
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

# Example source and target
source = "word200xyzword200xyzword200xyz"
target = "w o r d 200 x y zw o r d 200 x y z"

# Visualization 1: Source structure
ax1.set_title("Source String Structure", fontsize=14, fontweight='bold')
ax1.text(0.5, 0.8, f"Source: {source}", fontsize=12, ha='center', va='center')

# Show the triple repetition
part_len = len(source) // 3
parts = [source[i*part_len:(i+1)*part_len] for i in range(3)]

ax1.text(0.5, 0.6, "Pattern: Triple repetition of 'word200xyz'", fontsize=11, ha='center', va='center', style='italic')
ax1.text(0.5, 0.5, f"Part 1: {parts[0]}", fontsize=11, ha='center', va='center', color='blue')
ax1.text(0.5, 0.4, f"Part 2: {parts[1]}", fontsize=11, ha='center', va='center', color='green')
ax1.text(0.5, 0.3, f"Part 3: {parts[2]}", fontsize=11, ha='center', va='center', color='red')

ax1.set_xlim(0, 1)
ax1.set_ylim(0, 1)
ax1.axis('off')

# Visualization 2: Segmentation pattern
ax2.set_title("Target Segmentation Pattern", fontsize=14, fontweight='bold')
ax2.text(0.5, 0.8, f"Target: {target}", fontsize=12, ha='center', va='center')

# Explain the pattern
pattern_desc = """Segmentation Rules:
1. Most characters separated by spaces
2. 'zw' kept as single token at boundary between repetitions
3. Numbers preserved as multi-digit tokens
4. Only first two repetitions are segmented (third is ignored)"""

ax2.text(0.1, 0.5, pattern_desc, fontsize=11, va='top', linespacing=1.5,
         bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.5))

# Model prediction
prediction = "w o r d 1 x y z w o r d 1 x y z"
ax2.text(0.5, 0.2, f"Model Prediction: {prediction}", fontsize=11, ha='center', va='center', 
         bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))

ax2.set_xlim(0, 1)
ax2.set_ylim(0, 1)
ax2.axis('off')

plt.tight_layout()
plt.savefig('../report/images/segmentation_pattern.png', dpi=300, bbox_inches='tight')
plt.close()

print("Pattern visualization saved to report/images/segmentation_pattern.png")
