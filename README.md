# 🤖 FINALBOT — Binary Options Trading Bot

**Status:** ✅ PRODUCTION READY

## Quick Start

### 1. Extract & Install
```bash
unzip BOT_FINALBOT.zip
cd BOT_FINALBOT
pip install -r requirements.txt
```

### 2. Run Bot
```bash
python runner.py
```

**That's it!** Bot will start trading EURUSD-OTC immediately.

## Configuration

### Settings
แก้ไฟล์ `config/settings.json` ก่อนรัน

### Modify Trading Pair
แก้ไฟล์ `config/symbols.txt` (หนึ่งบรรทัด = หนึ่งคู่)

## Features

✅ 25 Intelligence Engines (8 Tiers)
✅ Real-time Market Analysis
✅ Automatic Position Sizing (2% risk per trade)
✅ Risk Management (5% daily limit)
✅ Live Order Execution
✅ Performance Monitoring
✅ Trade Logging & Replay

## Files

- `runner.py` — Main bot orchestrator
- `core/` — Intelligence OS + Data layer
- `execution/` — Order execution + Position sizing
- `monitoring/` — Logging + Performance tracking
- `strategy/` — Trading strategies
- `tests/` — Unit + Integration tests

## Logs

```
logs/bot_YYYYMMDD_HHMMSS.log  — Full bot logs
logs/signals_YYYYMMDD.log     — Trade signals only
logs/orders_YYYYMMDD.jsonl    — Order history
```

## Support

All code ready. Just extract, install, run.

