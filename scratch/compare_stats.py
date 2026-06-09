import json
import re

file_path = r"C:\Users\Administrator\Downloads\TEST\backtest_with_outcomes.json"

with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# original
bot_wins = 0
bot_losses = 0
bot_pnl = 0.0

# V2 Athena
athena_wins = 0
athena_losses = 0
athena_pnl = 0.0
athena_taken = 0
athena_skipped = 0

details = []

for idx, entry in enumerate(data):
    strat = entry.get("strategy")
    orig_direction = entry.get("direction") # originally recorded direction
    reason = entry.get("reason", "")
    ind = entry.get("indicators", {})
    outcome = entry.get("trade_outcome", {})
    won = outcome.get("won", False)
    pnl = outcome.get("pnl", 0.0)
    
    # original bot performance
    if won:
        bot_wins += 1
    else:
        bot_losses += 1
    bot_pnl += pnl
    
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
    
    # Apply V2 Momentum-Friendly Rules
    if strategy := entry.get("strategy"):
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
                    
    if decision == "NOTRADE":
        athena_skipped += 1
    else:
        athena_taken += 1
        if won:
            athena_wins += 1
        else:
            athena_losses += 1
        athena_pnl += pnl

print(f"Original Bot: Wins={bot_wins}, Losses={bot_losses}, WinRate={bot_wins/(bot_wins+bot_losses)*100:.2f}%, PnL={bot_pnl:.2f}")
print(f"Athena V2: Wins={athena_wins}, Losses={athena_losses}, WinRate={athena_wins/(athena_wins+athena_losses)*100:.2f}% (Taken={athena_taken}, Skipped={athena_skipped}), PnL={athena_pnl:.2f}")
