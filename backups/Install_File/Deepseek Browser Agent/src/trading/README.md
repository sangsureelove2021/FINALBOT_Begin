# RSI Binary Options Trading Bot

A fully automated binary options trading bot that uses the RSI (Relative Strength Index) indicator to generate trading signals for EUR/USD and GBP/USD with 5-minute expiries.

## 📊 Strategy Overview

- **RSI Oversold (< 30)**: Generate BUY CALL signal (price expected to rise)
- **RSI Overbought (> 70)**: Generate BUY PUT signal (price expected to fall)
- **Assets**: EUR/USD, GBP/USD
- **Expiry**: 5 minutes
- **Risk per trade**: 2% of account balance

## 🚀 Features

- ✅ Fully automated trading with RSI strategy
- ✅ Simulation mode for testing
- ✅ Live trading capability (Deriv/MT5 integration ready)
- ✅ Comprehensive risk management
- ✅ Trade logging and performance tracking
- ✅ Daily statistics and reporting
- ✅ Multiple asset support
- ✅ Configurable parameters
- ✅ Graceful shutdown handling

## 📁 Project Structure

```
src/trading/
├── index.js          # Main bot entry point
├── strategy.js       # RSI strategy implementation
├── broker.js         # Broker connector (Deriv/MT5)
├── risk.js           # Risk management module
├── logger.js         # Trade logging and reporting
├── scheduler.js      # Task scheduler
├── config.js         # Configuration settings
├── cli.js           # Command-line interface
├── package.json     # Package manifest
└── README.md        # This file
```

## 🛠️ Installation

```bash
# Navigate to the trading directory
cd src/trading

# Install dependencies (if any)
npm install
```

## ⚙️ Configuration

Edit `config.js` to customize your trading parameters:

```javascript
module.exports = {
  // Assets to trade
  assets: ['EUR/USD', 'GBP/USD'],
  
  // RSI parameters
  rsiPeriod: 14,
  rsiOversoldThreshold: 30,
  rsiOverboughtThreshold: 70,
  
  // Trade parameters
  expiryMinutes: 5,
  riskPerTrade: 2,
  
  // Risk management
  maxConsecutiveLosses: 3,
  maxDailyLosses: 5,
  maxDailyTrades: 20,
  maxOpenTrades: 3,
  minBalance: 100,
  initialBalance: 10000,
  
  // Mode
  simulationMode: true,  // Set to false for live trading
  
  // Check interval (seconds)
  checkInterval: 10
};
```

## 🚦 Usage

### Start the bot

```bash
# Simulation mode (default)
node cli.js start

# Live trading mode
node cli.js start --live
```

### Check status

```bash
node cli.js status
```

### View statistics

```bash
node cli.js stats
```

### Generate performance report

```bash
node cli.js report
```

### Run a test cycle

```bash
node cli.js test
```

### Show configuration

```bash
node cli.js config
```

### Stop the bot

```bash
node cli.js stop
```

## 📈 Performance Monitoring

The bot automatically logs all trades to `logs/trading/` directory:

- `trades_YYYY-MM-DD.json` - Daily trade logs
- `report_YYYY-MM-DD.txt` - Performance reports

### Statistics tracked

- Total trades and win/loss count
- Win rate percentage
- Total profit/loss
- Average win/loss amounts
- Profit factor
- Maximum consecutive losses
- Performance by asset
- Performance by signal type (CALL/PUT)

## 🔗 Broker Integration

### Deriv (Binary.com)

To integrate with Deriv:

1. Get your API credentials from Deriv
2. Update `broker.js` `executeRealTrade()` method
3. Set `simulationMode: false` in config
4. Configure API endpoint and credentials

### MT5

To integrate with MetaTrader 5:

1. Install MT5 Python bridge or use REST API
2. Update `broker.js` with MT5 connection
3. Configure account details in config

## 🛡️ Risk Management

The bot implements multiple risk management layers:

1. **Position Sizing**: 2% of account balance per trade
2. **Consecutive Loss Protection**: Stops after 3 consecutive losses
3. **Daily Loss Limit**: Stops after 5 daily losses
4. **Daily Trade Limit**: Maximum 20 trades per day
5. **Max Open Trades**: Maximum 3 simultaneous trades
6. **Cooldown**: 30 seconds between trades
7. **Minimum Balance**: Stops if balance falls below $100

## 🧪 Testing

### Simulation Mode

Run the bot in simulation mode to test without risking real money:

```bash
node cli.js start
```

### Backtesting

Run backtests on historical data:

```bash
node cli.js backtest --data data.csv
```

## 📊 Example Output

```
🤖 Initializing Trading Bot...
📊 Strategy: RSI (Overbought > 70, Oversold < 30)
💹 Assets: EUR/USD, GBP/USD
⏱️ Expiry: 5 minutes
💰 Risk per trade: 2%
✅ Bot initialized successfully

📈 [2026-07-04T13:31:27.109Z] Checking signals...
🎯 Signal detected for EUR/USD: CALL (RSI: 28.45)
✅ Trade executed: EUR/USD CALL 200.00 expiry 5m

📊 Stats: Trades=1 | Wins=0 | Losses=0 | WinRate=0.0% | Profit=0.00 | ConsecutiveLosses=0
```

## 🔧 Customization

### Adjust RSI Thresholds

```javascript
// In config.js
rsiOversoldThreshold: 25,  // More aggressive CALL signals
rsiOverboughtThreshold: 75 // More aggressive PUT signals
```

### Change Risk Per Trade

```javascript
// In config.js
riskPerTrade: 1.5  // 1.5% of balance per trade
```

### Add More Assets

```javascript
// In config.js
assets: ['EUR/USD', 'GBP/USD', 'USD/JPY', 'AUD/USD']
```

### Change Expiry Time

```javascript
// In config.js
expiryMinutes: 15  // 15-minute expiries
```

## 🐛 Troubleshooting

### Bot won't start
- Check Node.js version (requires >=18.0.0)
- Verify all files are present
- Check for syntax errors in config.js

### No signals generated
- Ensure RSI period is valid (14 recommended)
- Check price data is being received
- Verify RSI thresholds are not too strict

### Live trading not working
- Verify broker API credentials
- Check API endpoint URL
- Ensure simulationMode is set to false
- Check broker account has sufficient balance

## 📝 License

MIT License - See LICENSE file for details

## ⚠️ Disclaimer

**Trading binary options involves substantial risk of loss. This bot is provided for educational purposes only. Use at your own risk. Past performance does not guarantee future results.**

## 🤝 Contributing

Contributions are welcome! Please submit pull requests or open issues for bugs and feature requests.

## 📧 Support

For support, please open an issue in the repository or contact the development team.

---

**Happy Trading! 📈**
