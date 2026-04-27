import os

image_dir = 'report/images'
if os.path.exists(image_dir):
    files = os.listdir(image_dir)
    print(f'Images in {image_dir}:')
    for f in files:
        path = os.path.join(image_dir, f)
        size = os.path.getsize(path)
        print(f'  {f}: {size} bytes')
else:
    print(f'{image_dir} does not exist')

output_dir = 'outputs'
if os.path.exists(output_dir):
    files = os.listdir(output_dir)
    print(f'\nFiles in {output_dir}:')
    for f in files:
        path = os.path.join(output_dir, f)
        size = os.path.getsize(path)
        print(f'  {f}: {size} bytes')
