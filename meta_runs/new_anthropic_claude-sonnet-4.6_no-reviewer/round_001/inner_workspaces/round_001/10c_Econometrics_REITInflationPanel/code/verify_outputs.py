import os

# Check images
image_dir = 'report/images'
if os.path.exists(image_dir):
    images = os.listdir(image_dir)
    print(f'Images ({len(images)}):')
    for img in sorted(images):
        size = os.path.getsize(os.path.join(image_dir, img))
        print(f'  {img}: {size:,} bytes')
else:
    print('No images directory!')

# Check outputs
output_dir = 'outputs'
if os.path.exists(output_dir):
    outputs = os.listdir(output_dir)
    print(f'\nOutputs ({len(outputs)}):')
    for out in sorted(outputs):
        size = os.path.getsize(os.path.join(output_dir, out))
        print(f'  {out}: {size:,} bytes')

# Check report
report_file = 'report/report.md'
if os.path.exists(report_file):
    size = os.path.getsize(report_file)
    print(f'\nReport: {size:,} bytes')
else:
    print('\nNo report!')
