import json
import re

json_path = r"C:\Users\Administrator\Downloads\BOT_FINALBOT\BOT_FINALBOT\ดเ่.json"

with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

modified_count = 0
notrade_count = 0
kept_count = 0

for idx, signal in enumerate(data):
    strategy = signal.get("strategy")
    reason = signal.get("reason", "")
    ind = signal.get("indicators", {})
    
    # 1. Recover the TRUE original direction from the reason string
    orig_direction = None
    if "CALL" in reason or "trend=UP" in reason or "triggered CALL" in reason or "Reversal CALL" in reason:
        orig_direction = "CALL"
    elif "PUT" in reason or "trend=DOWN" in reason or "triggered PUT" in reason or "Reversal PUT" in reason or "Downtrend" in reason or "PA=Shooting Star" in reason:
        orig_direction = "PUT"
    else:
        orig_direction = signal.get("direction")
        
    # Get values
    ema5 = ind.get("ema5")
    prev_ema5 = ind.get("prev_ema5")
    ema20 = ind.get("ema20")
    prev_ema20 = ind.get("prev_ema20")
    ema50 = ind.get("ema50")
    bb_upper = ind.get("bb_upper")
    bb_lower = ind.get("bb_lower")
    rsi7 = ind.get("rsi7")
    
    prev_rsi7 = rsi7
    if idx > 0:
        prev_ind = data[idx - 1].get("indicators", {})
        prev_rsi7 = prev_ind.get("rsi7", rsi7)
        
    macd = ind.get("macd")
    macd_signal = ind.get("macd_signal")
    prev_macd = ind.get("prev_macd", macd)
    prev_macd_signal = ind.get("prev_signal", macd_signal)
    stoch_k = ind.get("stoch_k")
    stoch_d = ind.get("stoch_d")
    prev_stoch_k = ind.get("prev_stoch_k", stoch_k)
    prev_stoch_d = ind.get("prev_stoch_d", stoch_d)
    
    decision = "NOTRADE"
    
    # 2. Apply V2 Momentum-Friendly Rules
    if strategy == "compression_breakout":
        if orig_direction == "CALL":
            if ema5 > ema20 and ema20 > ema50:
                decision = "CALL"
        elif orig_direction == "PUT":
            if ema5 < ema20 and ema20 < ema50:
                decision = "PUT"
                
    elif strategy == "stochastic_crossover":
        if orig_direction == "CALL":
            is_crossover = prev_stoch_k <= prev_stoch_d and stoch_k > stoch_d
            is_oversold = stoch_k < 25
            if is_crossover and is_oversold:
                decision = "CALL"
        elif orig_direction == "PUT":
            is_crossover = prev_stoch_k >= prev_stoch_d and stoch_k < stoch_d
            is_overbought = stoch_k > 75
            if is_crossover and is_overbought:
                decision = "PUT"
                
    elif strategy == "bb_rsi_confluence_america":
        close_match = re.search(r"Close\s+(\d+\.\d+)", reason)
        close_val = float(close_match.group(1)) if close_match else None
        
        if orig_direction == "CALL":
            is_oversold_rsi = rsi7 < 35
            is_at_bb = (close_val <= bb_lower) if close_val else (ema5 <= bb_lower * 1.0005)
            if is_oversold_rsi and is_at_bb:
                decision = "CALL"
        elif orig_direction == "PUT":
            is_overbought_rsi = rsi7 > 65
            is_at_bb = (close_val >= bb_upper) if close_val else (ema5 >= bb_upper * 0.9995)
            if is_overbought_rsi and is_at_bb:
                decision = "PUT"
                
    elif strategy == "rsi_reversal":
        if orig_direction == "CALL":
            is_reversal = prev_rsi7 < 30 and rsi7 >= 30
            if is_reversal:
                decision = "CALL"
        elif orig_direction == "PUT":
            is_reversal = prev_rsi7 > 70 and rsi7 <= 70
            if is_reversal:
                decision = "PUT"
                
    elif strategy == "triple_confluence":
        if orig_direction == "PUT":
            if ema20 < ema50:
                decision = "PUT"
        elif orig_direction == "CALL":
            if ema20 > ema50:
                decision = "CALL"
                
    elif strategy == "ema_crossover":
        if orig_direction == "CALL":
            is_crossover = prev_ema5 < prev_ema20 and ema5 > ema20
            if is_crossover:
                decision = "CALL"
        elif orig_direction == "PUT":
            is_crossover = prev_ema5 > prev_ema20 and ema5 < ema20
            if is_crossover:
                decision = "PUT"
                
    elif strategy == "macd_crossover":
        if orig_direction == "CALL":
            is_crossover = prev_macd < prev_macd_signal and macd > macd_signal
            if is_crossover:
                decision = "CALL"
        elif orig_direction == "PUT":
            is_crossover = prev_macd > prev_macd_signal and macd < macd_signal
            if is_crossover:
                decision = "PUT"
                
    # Update field
    current_direction = signal.get("direction")
    if current_direction != decision:
        signal["direction"] = decision
        modified_count += 1
        
    if decision == "NOTRADE":
        notrade_count += 1
    else:
        kept_count += 1

# Overwrite JSON
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Result: Modified {modified_count} entries. NOTRADE: {notrade_count}. Kept: {kept_count}.")
