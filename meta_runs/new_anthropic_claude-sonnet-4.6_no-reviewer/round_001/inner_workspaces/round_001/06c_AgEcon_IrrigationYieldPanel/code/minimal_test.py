import os
os.makedirs('outputs', exist_ok=True)
with open('outputs/minimal_test.txt', 'w') as f:
    f.write('minimal test works\n')
print('minimal test done')
