import os

# Search for files
def find_files(root_dir, extensions):
    files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if any(filename.endswith(ext) for ext in extensions):
                files.append(os.path.join(dirpath, filename))
    return files

# Search in current directory
files = find_files('.', ['.md', '.txt', '.json', '.py', '.csv'])
print("Found files:")
for f in sorted(files):
    print(f"  {f}")

# Check if related_work exists
if os.path.exists('related_work'):
    print("\nRelated work directory exists.")
    related_files = find_files('related_work', ['.md', '.txt', '.pdf', '.json'])
    for f in related_files:
        print(f"  {f}")