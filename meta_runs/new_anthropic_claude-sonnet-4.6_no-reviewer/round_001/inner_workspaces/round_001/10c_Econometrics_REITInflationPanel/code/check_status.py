import os
import glob

# Check what files exist
for root, dirs, files in os.walk('.'):
    for f in files:
        path = os.path.join(root, f)
        print(path)
