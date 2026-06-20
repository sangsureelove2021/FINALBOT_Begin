import subprocess
import os
import time

prompt = """You are a professional binary options trader. Analyze the following market data and output ONLY a valid JSON object.
You can choose the optimal expiry time (from 1 to 5 minutes) based on market structure and volatility.

MARKET DATA:
Symbol: EURUSD
Current Price: 1.15679
Timestamp: 2026-06-14T20:13:26

TECHNICAL INDICATORS:
- RSI (14): 36.60
- MACD Histogram/Difference: -0.000017
- Trend: bearish
- Volatility: medium
- Support/Resistance: Support: 1.15500, Resistance: 1.15800

OUTPUT FORMAT (JSON only, no other text):
{
  "action": "CALL",
  "confidence": 85,
  "expiry": 3,
  "reason": "Explain reason briefly in Thai"
}"""

cmd_path = "C:\\Users\\Administrator\\AppData\\Roaming\\npm\\deepseek-agent.cmd"
out_file = os.path.abspath("temp_out.txt")

# Prepare command string or list.
# Using a file redirect on Windows shell
cmd_str = f'"{cmd_path}" --headless "{prompt.replace(chr(10), " ").replace(chr(13), "")}" > "{out_file}" 2>&1'

print("Running command with file redirect...")
print(f"Command: {cmd_str}")

start_time = time.time()
p = subprocess.Popen(cmd_str, shell=True)

try:
    p.wait(timeout=60)
    print(f"Finished in {time.time() - start_time:.2f} seconds with code {p.returncode}")
except subprocess.TimeoutExpired:
    print("Timed out! Killing process tree...")
    subprocess.run(f"taskkill /F /T /PID {p.pid}", shell=True, capture_output=True)
    p.wait()
    print("Killed.")

if os.path.exists(out_file):
    with open(out_file, "r", encoding="utf-8", errors="ignore") as f:
        print("\n--- FILE OUTPUT ---")
        print(f.read())
    os.remove(out_file)
else:
    print("Output file not found!")
