import shutil
import os

os.makedirs('outputs', exist_ok=True)
shutil.copy('data/train.csv', 'outputs/train.csv')
shutil.copy('data/val.csv', 'outputs/val.csv')
shutil.copy('data/test.csv', 'outputs/test.csv')
print('Copied successfully')
