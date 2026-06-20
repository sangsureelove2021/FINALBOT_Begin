import subprocess
import sys

p = subprocess.Popen([sys.executable, 'main.py'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
try:
    outs, _ = p.communicate(timeout=15)
    with open("test_out.txt", "w", encoding="utf-8") as f:
        f.write(outs)
except subprocess.TimeoutExpired:
    p.kill()
    outs, _ = p.communicate()
    with open("test_out.txt", "w", encoding="utf-8") as f:
        f.write(outs + '\n[TIMEOUT KILLED]')
