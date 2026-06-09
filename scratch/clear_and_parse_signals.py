import json
import os
from datetime import datetime, timezone

def process_signals():
    pending_path = r"c:\Users\Administrator\Downloads\BOT_FINALBOT\BOT_FINALBOT\logs\pending_signals.json"
    history_path = r"c:\Users\Administrator\Downloads\BOT_FINALBOT\BOT_FINALBOT\logs\signals_history.json"
    
    if not os.path.exists(pending_path):
        print(json.dumps({"error": "No pending signals file found", "signals_count": 0}))
        return
        
    try:
        with open(pending_path, "r", encoding="utf-8") as f:
            try:
                signals = json.load(f)
            except Exception as e:
                print(json.dumps({"error": f"Failed to parse JSON: {str(e)}", "signals_count": 0}))
                return
    except Exception as e:
        print(json.dumps({"error": f"Failed to read file: {str(e)}", "signals_count": 0}))
        return

    unprocessed = [s for s in signals if not s.get('processed', False)]
    
    if not unprocessed:
        print(json.dumps({"message": "No new unprocessed signals", "signals_count": 0}))
        return

    # Group and analyze unprocessed signals
    analysis = {
        "total_new_signals": len(unprocessed),
        "by_direction": {"CALL": 0, "PUT": 0},
        "by_strategy": {},
        "by_state": {},
        "recent_signals": unprocessed[-8:] # last 8 signals for details
    }
    
    for sig in unprocessed:
        direction = sig.get("direction", "UNKNOWN")
        analysis["by_direction"][direction] = analysis["by_direction"].get(direction, 0) + 1
        
        strat = sig.get("strategy", "UNKNOWN")
        if strat not in analysis["by_strategy"]:
            analysis["by_strategy"][strat] = {"count": 0, "CALL": 0, "PUT": 0, "confidences": []}
        analysis["by_strategy"][strat]["count"] += 1
        analysis["by_strategy"][strat][direction] = analysis["by_strategy"][strat].get(direction, 0) + 1
        analysis["by_strategy"][strat]["confidences"].append(sig.get("confidence", 0))
        
        state = sig.get("state", "UNKNOWN")
        analysis["by_state"][state] = analysis["by_state"].get(state, 0) + 1

    # Calculate average confidence per strategy
    for strat, data in list(analysis["by_strategy"].items()):
        confs = data["confidences"]
        data["avg_confidence"] = sum(confs) / len(confs) if confs else 0
        del data["confidences"] # remove list to keep output clean

    # Move processed signals to history
    existing_history = []
    if os.path.exists(history_path):
        try:
            with open(history_path, "r", encoding="utf-8") as f:
                existing_history = json.load(f)
        except:
            existing_history = []
            
    # Mark as processed
    for sig in unprocessed:
        sig['processed'] = True
        
    existing_history.extend(unprocessed)
    
    # Write back history (cap history to avoid infinite growth, let's keep up to 10000 signals)
    if len(existing_history) > 10000:
        existing_history = existing_history[-10000:]
        
    try:
        with open(history_path, "w", encoding="utf-8") as f:
            json.dump(existing_history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        analysis["history_write_error"] = str(e)

    # Empty the pending signals file
    try:
        with open(pending_path, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2, ensure_ascii=False)
    except Exception as e:
        analysis["pending_clear_error"] = str(e)

    print(json.dumps(analysis, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    process_signals()
