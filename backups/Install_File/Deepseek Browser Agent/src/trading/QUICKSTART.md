# 🚀 Quick Start Guide - RSI Trading Bot

## 5-Minute Setup

### 1. Navigate to the trading directory

```bash
cd src/trading
```

### 2. Start the bot in simulation mode

```bash
node cli.js start
```

That's it! The bot will start monitoring EUR/USD and GBP/USD for RSI signals.

---

## Common Commands

| Command | Description |
|---------|-------------|
| `node cli.js start` | Start bot (simulation mode) |
| `node cli.js start --live` | Start bot (live trading) |
| `node cli.js status` | Check bot status |
| `node cli.js stats` | View trading statistics |
| `node cli.js report` | Generate performance report |
| `node cli.js test` | Run a test cycle |
| `node cli.js config` | Show current configuration |
| `node cli.js stop` | Stop the bot |

---

## Using npm scripts (from project root)

| Command | Description |
|---------|-------------|
| `npm run trade` | Start bot |
| `npm run trade:dev` | Start bot (simulation) |
| `npm run trade:status` | Check status |
| `npm run trade:stats` | View stats |
| `npm run trade:report` | Generate report |
| `npm run trade:test` | Run test |
| `npm run trade:config` | Show config |
| `npm run trade:stop` | Stop bot |

---

## Configuration Quick Reference

Edit `config.js` to customize:

```javascript
// Change RSI thresholds
rsiOversoldThreshold: 30,  // Default: 30
rsiOverboughtThreshold: 70, // Default: 70

// Change risk per trade
riskPerTrade: 2, // Default: 2% of balance

// Change expiry time
expiryMinutes: 5, // Default: 5 minutes

// Add more assets
assets: ['EUR/USD', 'GBP/USD', 'USD/JPY'],

// Enable live trading
simulationMode: false, // Set to false for real trading
```

---

## Monitoring Your Trades

### Check trade logs

```bash
cat logs/trading/trades_$(date +%Y-%m-%d).json
```

### View performance report

```bash
node cli.js report
```

---

## Next Steps

1. **Test in simulation mode** - Run for a few days to verify signals
2. **Adjust parameters** - Fine-tune RSI thresholds and risk
3. **Enable live trading** - Configure broker API and set `simulationMode: false`
4. **Monitor performance** - Check stats and generate reports regularly

---

## Troubleshooting

### Bot won't start
- Check Node.js version: `node --version` (requires >=18.0.0)
- Verify all files exist in the trading directory

### No signals generated
- Check RSI thresholds in config
- Ensure price data is being received
- Increase `checkInterval` if too frequent

### Live trading not working
- Verify `simulationMode: false`
- Check broker API credentials in config
- Ensure broker account has sufficient balance

---

## Need Help?

- Check the full README.md for detailed documentation
- Review config.js for all available settings
- Check the logs directory for error messages

---

**Happy Trading! 📈**
