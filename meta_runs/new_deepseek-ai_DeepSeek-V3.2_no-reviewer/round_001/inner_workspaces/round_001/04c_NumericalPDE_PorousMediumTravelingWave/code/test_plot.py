#!/usr/bin/env python3
import matplotlib.pyplot as plt
import numpy as np
import os

# Create test plot
x = np.linspace(0, 10, 100)
y = np.sin(x)

plt.figure()
plt.plot(x, y)
plt.title('Test Plot')
plt.xlabel('x')
plt.ylabel('sin(x)')

# Ensure directory exists
os.makedirs('report/images', exist_ok=True)
os.makedirs('outputs', exist_ok=True)

# Save plot
plt.savefig('report/images/test_plot.png', dpi=150, bbox_inches='tight')
print("Plot saved to report/images/test_plot.png")

# Save test data
np.savez('outputs/test_data.npz', x=x, y=y)
print("Data saved to outputs/test_data.npz")

# List files
import glob
print("\nFiles in report/images:", glob.glob('report/images/*'))
print("Files in outputs:", glob.glob('outputs/*'))