import json
import re

file_path = r"C:\Users\Administrator\Downloads\BOT_FINALBOT\BOT_FINALBOT\data trade.json"
output_path = r"C:\Users\Administrator\.gemini\antigravity\brain\bf808087-316a-4062-af9c-a51da648c8ed\scratch\proposed_arbitration_v2.txt"

with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

proposed = []

for idx, signal in enumerate(data):
    strategy = signal.get("strategy")
    orig_direction = signal.get("direction")
    ind = signal.get("indicators", {})
    reason = signal.get("reason", "")
    
    # Get values
    ema5 = ind.get("ema5")
    prev_ema5 = ind.get("prev_ema5")
    ema20 = ind.get("ema20")
    prev_ema20 = ind.get("prev_ema20")
    ema50 = ind.get("ema50")
    bb_upper = ind.get("bb_upper")
    bb_lower = ind.get("bb_lower")
    rsi7 = ind.get("rsi7")
    
    # Correctly retrieve prev_rsi7 from previous index if possible
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
    detail = ""
    
    if strategy == "compression_breakout":
        # OTC Momentum-Friendly Rules: Ignore RSI boundary, only check if trend is strongly established!
        if orig_direction == "CALL":
            if ema5 > ema20 and ema20 > ema50:
                decision = "CALL"
                detail = f"Keep CALL: Strong established uptrend (EMA5={ema5:.5f} > EMA20={ema20:.5f} > EMA50={ema50:.5f}) - Momentum ride in OTC."
            else:
                detail = f"Change to NOTRADE: Trend not established (EMA5={ema5:.5f}, EMA20={ema20:.5f}, EMA50={ema50:.5f})."
        elif orig_direction == "PUT":
            if ema5 < ema20 and ema20 < ema50:
                decision = "PUT"
                detail = f"Keep PUT: Strong established downtrend (EMA5={ema5:.5f} < EMA20={ema20:.5f} < EMA50={ema50:.5f}) - Momentum ride in OTC."
            else:
                detail = f"Change to NOTRADE: Trend not established (EMA5={ema5:.5f}, EMA20={ema20:.5f}, EMA50={ema50:.5f})."
                
    elif strategy == "stochastic_crossover":
        if orig_direction == "CALL":
            is_crossover = prev_stoch_k <= prev_stoch_d and stoch_k > stoch_d
            is_oversold = stoch_k < 25
            if is_crossover and is_oversold:
                decision = "CALL"
                detail = f"Keep CALL: Stoch K crossed above D ({prev_stoch_k:.1f}->{stoch_k:.1f} vs {prev_stoch_d:.1f}->{stoch_d:.1f}) in oversold zone."
            else:
                detail = f"Change to NOTRADE: Crossover={is_crossover}, Oversold={is_oversold} (K={stoch_k:.1f}, D={stoch_d:.1f}, prevK={prev_stoch_k:.1f}, prevD={prev_stoch_d:.1f})."
        elif orig_direction == "PUT":
            is_crossover = prev_stoch_k >= prev_stoch_d and stoch_k < stoch_d
            is_overbought = stoch_k > 75
            if is_crossover and is_overbought:
                decision = "PUT"
                detail = f"Keep PUT: Stoch K crossed below D ({prev_stoch_k:.1f}->{stoch_k:.1f} vs {prev_stoch_d:.1f}->{stoch_d:.1f}) in overbought zone."
            else:
                detail = f"Change to NOTRADE: Crossover={is_crossover}, Overbought={is_overbought} (K={stoch_k:.1f}, D={stoch_d:.1f}, prevK={prev_stoch_k:.1f}, prevD={prev_stoch_d:.1f})."
                
    elif strategy == "bb_rsi_confluence_america":
        close_match = re.search(r"Close\s+(\d+\.\d+)", reason)
        close_val = float(close_match.group(1)) if close_match else None
        
        if orig_direction == "CALL":
            is_oversold_rsi = rsi7 < 35
            is_at_bb = (close_val <= bb_lower) if close_val else (ema5 <= bb_lower * 1.0005)
            if is_oversold_rsi and is_at_bb:
                decision = "CALL"
                detail = f"Keep CALL: Close={close_val} <= LowerBB={bb_lower:.5f} and RSI7={rsi7:.1f} < 35."
            else:
                detail = f"Change to NOTRADE: OversoldRSI={is_oversold_rsi} (RSI7={rsi7:.1f}), AtBB={is_at_bb} (Close={close_val}, LowerBB={bb_lower:.5f})."
        elif orig_direction == "PUT":
            is_overbought_rsi = rsi7 > 65
            is_at_bb = (close_val >= bb_upper) if close_val else (ema5 >= bb_upper * 0.9995)
            if is_overbought_rsi and is_at_bb:
                decision = "PUT"
                detail = f"Keep PUT: Close={close_val} >= UpperBB={bb_upper:.5f} and RSI7={rsi7:.1f} > 65."
            else:
                detail = f"Change to NOTRADE: OverboughtRSI={is_overbought_rsi} (RSI7={rsi7:.1f}), AtBB={is_at_bb} (Close={close_val}, UpperBB={bb_upper:.5f})."
                
    elif strategy == "rsi_reversal":
        if orig_direction == "CALL":
            is_reversal = prev_rsi7 < 30 and rsi7 >= 30
            if is_reversal:
                decision = "CALL"
                detail = f"Keep CALL: RSI7 reversed upward from oversold ({prev_rsi7:.1f} -> {rsi7:.1f})."
            else:
                detail = f"Change to NOTRADE: Invalid RSI7 reversal ({prev_rsi7:.1f} -> {rsi7:.1f})."
        elif orig_direction == "PUT":
            is_reversal = prev_rsi7 > 70 and rsi7 <= 70
            if is_reversal:
                decision = "PUT"
                detail = f"Keep PUT: RSI7 reversed downward from overbought ({prev_rsi7:.1f} -> {rsi7:.1f})."
            else:
                detail = f"Change to NOTRADE: Invalid RSI7 reversal ({prev_rsi7:.1f} -> {rsi7:.1f})."
                
    elif strategy == "triple_confluence":
        if orig_direction == "PUT":
            if ema20 < ema50:
                decision = "PUT"
                detail = f"Keep PUT: Strong downtrend (EMA20={ema20:.5f} < EMA50={ema50:.5f}) for triple confluence."
            else:
                detail = f"Change to NOTRADE: Trend is uptrend/flat (EMA20={ema20:.5f} >= EMA50={ema50:.5f})."
        elif orig_direction == "CALL":
            if ema20 > ema50:
                decision = "CALL"
                detail = f"Keep CALL: Strong uptrend (EMA20={ema20:.5f} > EMA50={ema50:.5f}) for triple confluence."
            else:
                detail = f"Change to NOTRADE: Trend is downtrend/flat (EMA20={ema20:.5f} <= EMA50={ema50:.5f})."
                
    elif strategy == "ema_crossover":
        if orig_direction == "CALL":
            is_crossover = prev_ema5 < prev_ema20 and ema5 > ema20
            if is_crossover:
                decision = "CALL"
                detail = f"Keep CALL: EMA5 crossed above EMA20 ({prev_ema5:.5f}->{ema5:.5f} vs {prev_ema20:.5f}->{ema20:.5f})."
            else:
                detail = f"Change to NOTRADE: No active crossover (EMA5={ema5:.5f}, EMA20={ema20:.5f}, prev5={prev_ema5:.5f}, prev20={prev_ema20:.5f})."
        elif orig_direction == "PUT":
            is_crossover = prev_ema5 > prev_ema20 and ema5 < ema20
            if is_crossover:
                decision = "PUT"
                detail = f"Keep PUT: EMA5 crossed below EMA20 ({prev_ema5:.5f}->{ema5:.5f} vs {prev_ema20:.5f}->{ema20:.5f})."
            else:
                detail = f"Change to NOTRADE: No active crossover (EMA5={ema5:.5f}, EMA20={ema20:.5f}, prev5={prev_ema5:.5f}, prev20={prev_ema20:.5f})."
                
    elif strategy == "macd_crossover":
        if orig_direction == "CALL":
            is_crossover = prev_macd < prev_macd_signal and macd > macd_signal
            if is_crossover:
                decision = "CALL"
                detail = f"Keep CALL: MACD line crossed above Signal line ({prev_macd:.6f}->{macd:.6f} vs {prev_macd_signal:.6f}->{macd_signal:.6f})."
            else:
                detail = f"Change to NOTRADE: No active crossover (MACD={macd:.6f}, Signal={macd_signal:.6f})."
        elif orig_direction == "PUT":
            is_crossover = prev_macd > prev_macd_signal and macd < macd_signal
            if is_crossover:
                decision = "PUT"
                detail = f"Keep PUT: MACD line crossed below Signal line ({prev_macd:.6f}->{macd:.6f} vs {prev_macd_signal:.6f}->{macd_signal:.6f})."
            else:
                detail = f"Change to NOTRADE: No active crossover (MACD={macd:.6f}, Signal={macd_signal:.6f})."
    else:
        detail = f"Unknown strategy {strategy}. Change to NOTRADE."
        decision = "NOTRADE"
        
    proposed.append({
        "index": idx,
        "timestamp": signal.get("timestamp"),
        "strategy": strategy,
        "original": orig_direction,
        "proposed": decision,
        "detail": detail
    })

with open(output_path, "w", encoding="utf-8") as f:
    f.write(f"Total processed: {len(proposed)}\n\n")
    for item in proposed:
        f.write(f"Index: {item['index']}\n")
        f.write(f"Timestamp: {item['timestamp']}\n")
        f.write(f"Strategy: {item['strategy']}\n")
        f.write(f"Original Direction: {item['original']} | Proposed: {item['proposed']}\n")
        f.write(f"Detail: {item['detail']}\n")
        f.write("-" * 50 + "\n")

print(f"Proposed decisions v2 saved to proposed_arbitration_v2.txt")
