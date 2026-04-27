import subprocess
import sys

result = subprocess.run(
    [sys.executable, 'code/final_analysis.py'],
    capture_output=True,
    text=True
)

with open('outputs/run_and_log.txt', 'w') as f:
    f.write('STDOUT:\n')
    f.write(result.stdout)
    f.write('\nSTDERR:\n')
    f.write(result.stderr)
    f.write(f'\nReturn code: {result.returncode}\n')

print('Done. Return code:', result.returncode)
print('STDOUT:', result.stdout[:500])
print('STDERR:', result.stderr[:500])
