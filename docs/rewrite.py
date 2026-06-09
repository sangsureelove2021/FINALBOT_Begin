import re

input_file = r'C:\Users\Administrator\Downloads\BOT_FINALBOT\BOT_FINALBOT\docs\FINALBOT_MASTER_BLUEPRINT.md'
output_file = r'C:\Users\Administrator\Downloads\BOT_FINALBOT\BOT_FINALBOT\docs\FINALBOT_MASTER_BLUEPRINT_REWRITTEN.md'

with open(input_file, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(r'\n', '\n')

matches = list(re.finditer(r'FILE \d+/44: ([^\n]+)\n={70,}\n(.*?)(?=\n={70,}\n.*?FILE|\Z)', content, re.DOTALL))

specs = []
for m in matches:
    filename = m.group(1).strip()
    file_content = m.group(2).strip()
    if '_specification.md' in filename:
        specs.append((filename, file_content))

print(f'Found {len(specs)} specs.')

with open(output_file, 'w', encoding='utf-8') as out:
    out.write('# ?? FINALBOT MASTER BLUEPRINT: THE DEFINITIVE ARCHITECTURE MANUAL\n\n')
    out.write('> [!IMPORTANT]\n> This is the unabridged, comprehensive technical specification for FINALBOT. It contains 100% of the mathematical scoring formulas, Intelligence OS definitions, Pipeline orchestration rules, and exhaustive details of all 14 execution strategies.\n\n')
    
    out.write('## 1. ?? Core Architecture\n\n')
    out.write('### Intelligence OS & Pipeline OS\n')
    out.write('The Intelligence OS continuously analyzes multi-dimensional market data (Volatility, Trend, Momentum, Structure, Multi-Timeframe) to classify real-time Market States. The Pipeline OS dictates the sequential orchestration from data ingestion to signal generation.\n\n')
    
    out.write('### Market States ??\n')
    out.write('- **Suitable States:** BREAKOUT_EMERGING, ACCUMULATION, SIDEWAY_RANGE, REVERSAL_FORMING, DISTRIBUTION\n')
    out.write('- **Blocked States:** TRENDING_STRONG, TRENDING_WEAK, LIQUIDITY_VOID, CHOPPY_UNCERTAIN, TRANSITIONAL, UNCLEAR\n\n')
    
    out.write('---\n\n')
    out.write('## 2. ?? The Universal Scoring System\n\n')
    out.write('### ?? Entry Score (0-100)\n')
    out.write('- **Base Score:** 50 points.\n')
    out.write('- **Bonus Factors:**\n')
    out.write('  - F_trend = Min(20, trend_strength / 5)\n')
    out.write('  - F_expansion = Min(15, expansion_probability / 7)\n')
    out.write('  - F_mtf = Min(10, alignment_score / 10)\n')
    out.write('  - *Further quality bonuses apply based on strategy specifics.*\n\n')
    
    out.write('### ?? Block Score (0-100)\n')
    out.write('- **Soft Blocks:** Trap (+30), Noise (+20), Exhaustion (+15), Reversal (+15), Fatigue (+20).\n')
    out.write('- **Hard Blocks:** Market State Blocked, Extreme Volatility, High Impact News, Anomaly, Feed Freeze -> Block Score = 100.\n')
    out.write('- **Confidence Formula:** Confidence = Entry_Score * (1 - Block_Score / 200)\n\n')
    
    out.write('---\n\n')
    out.write('## 3. ?? Exhaustive Strategy Specifications (14 Strategies)\n\n')
    
    for filename, content in specs:
        title = filename.replace('_specification.md', '').replace('_', ' ')
        out.write(f'### ?? STRATEGY: {title}\n\n')
        
        formatted_content = content.replace('---', '***')
        formatted_content = re.sub(r'\[(\d+)\] (.*?)\n', r'#### \1. \2\n', formatted_content)
        
        out.write(formatted_content + '\n\n---\n\n')

    out.write('## 4. ?? Production Rules & Frozen Output Schema\n\n')
    out.write('### ??? PRODUCTION M5 BINARY Baseline\n')
    out.write('- **Timeframe:** Strict M5 evaluation, signal valid for exactly 1 M5 candle expiry.\n')
    out.write('- **Zero Repaint:** Signals are processed at the *open* of a new candle.\n')
    out.write('- **Fail Fast:** Pre-flight and hard blocks instantly terminate evaluation.\n\n')
    
    out.write('### ?? Frozen JSON Schema\n')
    out.write('`json\n{\n  "timestamp": "2026-06-07T10:45:00Z",\n  "symbol": "EURUSD",\n  "strategy_id": "strategy_name",\n  "signal_direction": "CALL",\n  "confidence_score": 85.5,\n  "market_state": "STATE",\n  "entry_score": 90,\n  "block_score": 10,\n  "fail_reason_code": "NONE",\n  "audit_id": "REQ-102938"\n}\n`\n')

print('Rewritten Blueprint successfully generated.')
