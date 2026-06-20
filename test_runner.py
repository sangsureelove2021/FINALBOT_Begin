import subprocess
import sys

p = subprocess.Popen([sys.executable, 'runner.py'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
try:
    outs, _ = p.communicate(timeout=15)
    print(outs)
except subprocess.TimeoutExpired:
    p.kill()
    outs, _ = p.communicate()
    print(outs + '\n[TIMEOUT KILLED]')
