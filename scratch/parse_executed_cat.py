import pandas as pd

report_path = r'C:\Users\Administrator\Downloads\BOT_FINALBOT\BOT_FINALBOT\docs\GBPUSD_may_7_backtest_report.md'
executed = []

category_map = {
    'ema_crossover': '📈 ตามเทรนด์',
    'macd_crossover': '📈 ตามเทรนด์',
    'ema_ribbon_momentum': '📈 ตามเทรนด์',
    'triple_confluence': '📈 ตามเทรนด์',
    'pa_snr': '🔄 สวนเทรนด์/ไซเวย์',
    'sr_fakeout_rejection': '🔄 สวนเทรนด์/ไซเวย์',
    'rejection_5m_pa': '🔄 สวนเทรนด์/ไซเวย์',
    'pin_bar_scalper': '🔄 สวนเทรนด์/ไซเวย์',
    'engulfing_scalper': '🔄 สวนเทรนด์/ไซเวย์',
    'rsi_reversal': '🔄 สวนเทรนด์/ไซเวย์',
    'rsi_extreme_bounce': '🔄 สวนเทรนด์/ไซเวย์',
    'bb_rsi_confluence': '🔄 สวนเทรนด์/ไซเวย์',
    'stochastic_crossover': '🔄 สวนเทรนด์/ไซเวย์',
    'compression_breakout': '💥 เบรคเอาต์'
}

with open(report_path, 'r', encoding='utf-8') as f:
    for line in f:
        if line.startswith('| 2026') and '| Yes |' in line:
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 10:
                strat = parts[2]
                executed.append({
                    'Time': parts[1],
                    'Strategy': strat,
                    'Category': category_map.get(strat, 'Unknown'),
                    'Action': parts[3],
                    'Score': parts[4],
                    'Outcome': parts[8],
                    'PnL': parts[9]
                })

print('| เวลา (ICT) | กลยุทธ์ที่ลั่น | ประเภท | ทิศทาง | คะแนน Entry | ผลลัพธ์ | PnL |')
print('| :--- | :--- | :--- | :--- | :--- | :--- | :--- |')
for t in executed:
    print(f"| {t['Time']} | {t['Strategy']} | {t['Category']} | {t['Action']} | {t['Score']} | {t['Outcome']} | {t['PnL']} |")
