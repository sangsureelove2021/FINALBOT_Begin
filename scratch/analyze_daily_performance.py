import json
import pandas as pd
from pathlib import Path
from datetime import datetime

results_dir = Path("logs/batch_backtest_results")
sat_stats = {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0}
sun_stats = {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0}

weekly_daily = []

for file in sorted(results_dir.glob("week_*_results.json")):
    try:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        week = data.get("week")
        trades = data.get("trades", [])
        
        sat_w = {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0}
        sun_w = {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0}
        
        for t in trades:
            ts_str = t.get("timestamp")
            # Parse ISO timestamp, handle offset
            if "+" in ts_str:
                ts = datetime.fromisoformat(ts_str)
            else:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                
            # Convert to local time GMT+7
            local_hour = ts.hour + 7
            day_of_week = ts.weekday()
            
            # Since M5 timestamps are in UTC:
            # Saturday 11:00-23:00 local time = Saturday 04:00-16:00 UTC
            # weekday() in UTC is Saturday (5) or Sunday (6)
            is_sun = (day_of_week == 6)
            
            won = t.get("won")
            pnl = t.get("pnl")
            
            if is_sun:
                sun_w['trades'] += 1
                sun_stats['trades'] += 1
                if won:
                    sun_w['wins'] += 1
                    sun_stats['wins'] += 1
                else:
                    sun_w['losses'] += 1
                    sun_stats['losses'] += 1
                sun_w['pnl'] += pnl
                sun_stats['pnl'] += pnl
            else:
                sat_w['trades'] += 1
                sat_stats['trades'] += 1
                if won:
                    sat_w['wins'] += 1
                    sat_stats['wins'] += 1
                else:
                    sat_w['losses'] += 1
                    sat_stats['losses'] += 1
                sat_w['pnl'] += pnl
                sat_stats['pnl'] += pnl
                
        weekly_daily.append({
            'week': week,
            'sat': sat_w,
            'sun': sun_w
        })
    except Exception as e:
        print(f"Error reading {file.name}: {e}")

print("SATURDAY SUMMARY:")
sat_wr = (sat_stats['wins']/sat_stats['trades']*100) if sat_stats['trades'] > 0 else 0
print(f"Trades: {sat_stats['trades']} | Wins: {sat_stats['wins']} | Losses: {sat_stats['losses']} | WinRate: {sat_wr:.2f}% | P&L: {sat_stats['pnl']:+.2f} THB")

print("\nSUNDAY SUMMARY:")
sun_wr = (sun_stats['wins']/sun_stats['trades']*100) if sun_stats['trades'] > 0 else 0
print(f"Trades: {sun_stats['trades']} | Wins: {sun_stats['wins']} | Losses: {sun_stats['losses']} | WinRate: {sun_wr:.2f}% | P&L: {sun_stats['pnl']:+.2f} THB")

# Output a markdown table
print("\nMARKDOWN TABLE DATA:")
for w in weekly_daily:
    sat_w = w['sat']
    sun_w = w['sun']
    
    sat_wr = (sat_w['wins']/sat_w['trades']*100) if sat_w['trades'] > 0 else 0.0
    sun_wr = (sun_w['wins']/sun_w['trades']*100) if sun_w['trades'] > 0 else 0.0
    
    sat_pnl = f"{sat_w['pnl']:+.2f}"
    sun_pnl = f"{sun_w['pnl']:+.2f}"
    
    print(f"| Week {w['week']:02d} | Sat | {sat_w['trades']} | {sat_w['wins']} | {sat_w['losses']} | {sat_wr:.2f}% | {sat_pnl} THB |")
    print(f"| | Sun | {sun_w['trades']} | {sun_w['wins']} | {sun_w['losses']} | {sun_wr:.2f}% | {sun_pnl} THB |")
