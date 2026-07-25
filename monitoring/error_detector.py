"""
ErrorDetector — Real-time Error & Crash Log Analyzer for FINALBOT
Reads actual system logs to identify real errors, exceptions, and crash points.
Strictly no mocking.
"""

import os
import re
import glob
from pathlib import Path
from datetime import datetime

class ErrorDetector:
    def __init__(self, log_dir: str = "all_filelogs/system_logs"):
        self.log_dir = log_dir

    def scan_latest_log(self) -> None:
        """Scan the latest bot log file for real runtime exceptions and bugs."""
        if not os.path.exists(self.log_dir):
            print(f"[-] Log directory '{self.log_dir}' does not exist yet. Run the bot first to generate logs.")
            return

        # Find the newest log file
        log_files = glob.glob(os.path.join(self.log_dir, "bot_*.log"))
        if not log_files:
            print("[-] No bot log files found in all_filelogs/system_logs/")
            return

        latest_log = max(log_files, key=os.path.getmtime)
        print(f"[+] Scanning latest log file: {os.path.basename(latest_log)}")
        print("=" * 70)

        errors_found = []
        with open(latest_log, "r", encoding="utf-8", errors="ignore") as f:
            current_error = []
            capture = False
            for line in f:
                # Capture Python traceback blocks or lines with ERROR/CRITICAL/Exception
                if "Traceback (most recent call last):" in line or "ERROR" in line or "CRITICAL" in line or "Exception" in line:
                    capture = True
                    if current_error:
                        errors_found.append("".join(current_error))
                        current_error = []
                
                if capture:
                    current_error.append(line)
                    # Stop capturing if we see an info line or blank line after traceback
                    if not line.strip() or ("INFO" in line and "Traceback" not in line):
                        capture = False
                        if current_error:
                            errors_found.append("".join(current_error))
                            current_error = []

            if current_error:
                errors_found.append("".join(current_error))

        if not errors_found:
            print("[+] Scan complete. No active errors or crashes found in the log file.")
        else:
            print(f"[!] Found {len(errors_found)} error blocks in the log file:\n")
            for idx, err in enumerate(errors_found, 1):
                print(f"--- Error Block #{idx} ---")
                print(err.strip())
                print("-" * 70)

    def start_background_monitoring(self) -> None:
        """Start a background thread that monitors the latest log file for updates and prints new errors."""
        import time
        import threading

        def watch_loop():
            # Wait for log folder and files to appear
            while not os.path.exists(self.log_dir):
                time.sleep(1)
            
            latest_log = None
            while not latest_log:
                log_files = glob.glob(os.path.join(self.log_dir, "bot_*.log"))
                if log_files:
                    latest_log = max(log_files, key=os.path.getmtime)
                else:
                    time.sleep(1)

            # Start monitoring from the end of the file
            with open(latest_log, "r", encoding="utf-8", errors="ignore") as f:
                f.seek(0, os.SEEK_END)
                print(f"[Monitoring] Real-time Error Detector attached to: {os.path.basename(latest_log)}")
                
                traceback_lines = []
                capture_traceback = False
                
                while True:
                    line = f.readline()
                    if not line:
                        time.sleep(0.5)
                        continue
                    
                    # Detect new traceback or error entries
                    if "Traceback (most recent call last):" in line or "ERROR" in line or "CRITICAL" in line or "Exception" in line:
                        capture_traceback = True
                        if traceback_lines:
                            print(f"\n[Error Detector Alert]\n" + "".join(traceback_lines).strip() + "\n" + "="*50)
                            traceback_lines = []
                    
                    if capture_traceback:
                        traceback_lines.append(line)
                        # Stop capturing if we see an info line or blank line after traceback
                        if not line.strip() or ("INFO" in line and "Traceback" not in line):
                            capture_traceback = False
                            if traceback_lines:
                                print(f"\n[Error Detector Alert]\n" + "".join(traceback_lines).strip() + "\n" + "="*50)
                                traceback_lines = []

        t = threading.Thread(target=watch_loop, daemon=True)
        t.start()

def main():
    detector = ErrorDetector()
    detector.scan_latest_log()

if __name__ == "__main__":
    main()
