import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.abspath("."))

from data_evaluate.orchestrator import Orchestrator

def main():
    orc = Orchestrator()
    print("Running process_cycle for EURUSD-OTC...")
    result = orc.process_cycle("EURUSD-OTC")
    print("Process cycle completed successfully!")
    print(f"Result keys: {list(result.keys())}")
    
    # Check orchestrator logs directory for generated txt file
    log_dir = os.path.join("all_filelogs", "logs_orchestrator", "EURUSD-OTC")
    files = sorted(os.listdir(log_dir))
    latest_file = files[-1] if files else None
    print(f"Latest txt payload file: {latest_file}")
    if latest_file:
        with open(os.path.join(log_dir, latest_file), "r", encoding="utf-8") as f:
            content = f.read()
        print("--- Generated Payload TXT ---")
        print(content)

if __name__ == "__main__":
    main()
