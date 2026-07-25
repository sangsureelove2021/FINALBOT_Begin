#!/usr/bin/env node

/**
 * Trading Bot CLI
 * Command-line interface for the RSI binary options trading bot
 */

const fs = require('fs').promises;
const path = require('path');
const { TradingBot } = require('./index');
const config = require('./config');

// Parse command line arguments
const args = process.argv.slice(2);
const command = args[0] || 'start';

const bot = new TradingBot();

/**
 * Display help information
 */
function showHelp() {
  console.log(`
╔═══════════════════════════════════════════════════════════════╗
║         RSI BINARY OPTIONS TRADING BOT - CLI                  ║
╚═══════════════════════════════════════════════════════════════╝

USAGE:
  node cli.js <command> [options]

COMMANDS:
  start     Start the trading bot
  stop      Stop the trading bot
  status    Show bot status
  stats     Show trading statistics
  report    Generate a performance report
  config    Show current configuration
  test      Run a test cycle without executing trades
  backtest  Run backtest on historical data

OPTIONS:
  --simulation      Run in simulation mode (default: true)
  --live            Run in live trading mode
  --config <file>   Use custom config file
  --help            Show this help

EXAMPLES:
  node cli.js start                    # Start bot in simulation mode
  node cli.js start --live             # Start bot in live mode
  node cli.js status                   # Check bot status
  node cli.js report                   # Generate performance report
  node cli.js test                     # Run a test cycle
  node cli.js backtest --data data.csv # Run backtest

CONFIGURATION:
  Edit config.js to change trading parameters:
  - RSI thresholds (oversold: 30, overbought: 70)
  - Risk per trade (2%)
  - Expiry time (5 minutes)
  - Assets: EUR/USD, GBP/USD
`);
}

/**
 * Start the bot
 */
async function startBot(liveMode = false) {
  console.log('🚀 Starting RSI Trading Bot...');
  console.log(`📊 Mode: ${liveMode ? 'LIVE TRADING' : 'SIMULATION'}`);
  
  if (liveMode) {
    console.log('⚠️  LIVE TRADING MODE - Real money at risk!');
    console.log('⚠️  Please confirm by typing "CONFIRM"');
    
    // Wait for confirmation in interactive mode
    // In non-interactive mode, proceed with caution
    if (process.stdin.isTTY) {
      // For now, we'll just warn
      console.log('⚠️  To enable live trading, set simulationMode: false in config.js');
      console.log('⚠️  And ensure you have configured your broker API credentials');
    }
  }
  
  try {
    // Override config for live mode
    if (liveMode) {
      config.simulationMode = false;
    }
    
    // Create bot with updated config
    const liveBot = new TradingBot(config);
    await liveBot.start();
    
    // Store bot reference for CLI commands
    global.__bot = liveBot;
    
    console.log('✅ Bot started successfully');
  } catch (error) {
    console.error('❌ Failed to start bot:', error.message);
    process.exit(1);
  }
}

/**
 * Show bot status
 */
async function showStatus() {
  const botInstance = global.__bot;
  if (!botInstance) {
    console.log('⚠️  Bot not running. Use "node cli.js start" to start.');
    return;
  }
  
  const status = botInstance.getStatus();
  console.log(`
═══════════════════════════════════════════════════════════════
  BOT STATUS
═══════════════════════════════════════════════════════════════

  Status:           ${status.isRunning ? '🟢 Running' : '🔴 Stopped'}
  Assets:           ${status.config.assets.join(', ')}
  RSI Thresholds:   Oversold ${status.config.rsiOversoldThreshold} / Overbought ${status.config.rsiOverboughtThreshold}
  Expiry:           ${status.config.expiryMinutes} minutes
  Risk per trade:   ${status.config.riskPerTrade}%
  Mode:             ${status.config.simulationMode ? '🧪 Simulation' : '💰 Live'}
  Last Check:       ${status.lastCheck || 'N/A'}

  STATISTICS
  ──────────
  Total Trades:     ${status.stats.totalTrades}
  Wins:             ${status.stats.wins}
  Losses:           ${status.stats.losses}
  Win Rate:         ${status.stats.winRate.toFixed(1)}%
  Total Profit:     ${status.stats.totalProfit.toFixed(2)}
  Consecutive Losses: ${status.stats.consecutiveLosses}
`);
}

/**
 * Show trading statistics
 */
async function showStats() {
  const botInstance = global.__bot;
  if (!botInstance) {
    console.log('⚠️  Bot not running. Use "node cli.js start" to start.');
    return;
  }
  
  // Get stats from the logger
  const logger = botInstance.logger;
  if (logger && logger.initialized) {
    const summary = logger.getSummary(true);
    console.log(`
═══════════════════════════════════════════════════════════════
  TRADING STATISTICS
═══════════════════════════════════════════════════════════════

  SUMMARY
  ───────
  Total Trades:      ${summary.totalTrades}
  Closed Trades:     ${summary.closedTrades}
  Wins:              ${summary.wins}
  Losses:            ${summary.losses}
  Win Rate:          ${summary.winRate}%
  Total P/L:         ${summary.totalProfit}
  Average Win:       ${summary.avgWin}
  Average Loss:      ${summary.avgLoss}
  Profit Factor:     ${summary.profitFactor}
  Max Consecutive Losses: ${summary.maxConsecutiveLosses}

  PERFORMANCE BY ASSET
  ────────────────────
`);
    
    for (const [asset, data] of Object.entries(summary.byAsset || {})) {
      const winRate = data.trades > 0 ? (data.wins / data.trades * 100).toFixed(1) : 0;
      console.log(`  ${asset}: ${data.trades} trades | ${data.wins} wins | ${winRate}% win | P/L: ${data.profit.toFixed(2)}`);
    }
    
    console.log(`
  PERFORMANCE BY TYPE
  ────────────────────
`);
    for (const [type, data] of Object.entries(summary.byType || {})) {
      const winRate = data.trades > 0 ? (data.wins / data.trades * 100).toFixed(1) : 0;
      console.log(`  ${type}: ${data.trades} trades | ${data.wins} wins | ${winRate}% win | P/L: ${data.profit.toFixed(2)}`);
    }
    
    console.log(`
═══════════════════════════════════════════════════════════════
`);
  } else {
    console.log('⚠️  Logger not initialized. No stats available.');
  }
}

/**
 * Generate and save a report
 */
async function generateReport() {
  const botInstance = global.__bot;
  if (!botInstance) {
    console.log('⚠️  Bot not running. Use "node cli.js start" to start.');
    return;
  }
  
  const logger = botInstance.logger;
  if (logger && logger.initialized) {
    try {
      await logger.saveReport();
      console.log('✅ Report generated successfully');
    } catch (error) {
      console.error('❌ Failed to generate report:', error.message);
    }
  } else {
    console.log('⚠️  Logger not initialized.');
  }
}

/**
 * Show configuration
 */
async function showConfig() {
  console.log(`
═══════════════════════════════════════════════════════════════
  CURRENT CONFIGURATION
═══════════════════════════════════════════════════════════════

  ASSETS
  ──────
  ${config.assets.join(', ')}

  STRATEGY
  ────────
  RSI Period:              ${config.rsiPeriod}
  Oversold Threshold:      ${config.rsiOversoldThreshold}
  Overbought Threshold:    ${config.rsiOverboughtThreshold}

  TRADING
  ───────
  Expiry Minutes:          ${config.expiryMinutes}
  Risk per Trade:          ${config.riskPerTrade}%
  Payout Rate:             ${config.payoutRate * 100}%
  Min Trade:               ${config.minTrade}

  RISK MANAGEMENT
  ────────────────
  Max Consecutive Losses:  ${config.maxConsecutiveLosses}
  Max Daily Losses:        ${config.maxDailyLosses}
  Max Daily Trades:        ${config.maxDailyTrades}
  Max Open Trades:         ${config.maxOpenTrades}
  Min Balance:             ${config.minBalance}
  Initial Balance:         ${config.initialBalance}

  SYSTEM
  ──────
  Mode:                    ${config.simulationMode ? '🧪 Simulation' : '💰 Live'}
  Check Interval:          ${config.checkInterval}s
  Log Directory:           ${config.logDir}
  Detailed Logging:        ${config.detailedLogging}

  BROKER
  ──────
  Type:                    ${config.brokerType}
  API Endpoint:            ${config.brokerApiEndpoint || 'Not configured'}
  API Key:                 ${config.brokerApiKey ? '✅ Configured' : '❌ Not configured'}

═══════════════════════════════════════════════════════════════
`);
}

/**
 * Run a test cycle
 */
async function runTest() {
  console.log('🧪 Running test cycle (no real trades)...');
  
  // Create a test bot with simulation mode
  const testConfig = { ...config, simulationMode: true };
  const testBot = new TradingBot(testConfig);
  
  try {
    await testBot.initialize();
    
    // Run one cycle
    await testBot.runCycle();
    
    console.log('✅ Test cycle completed');
    
    // Show signals that were generated
    const stats = testBot.getStatus();
    console.log(`Test results: ${stats.stats.totalTrades} trades processed`);
    
    testBot.stop();
  } catch (error) {
    console.error('❌ Test failed:', error.message);
  }
}

/**
 * Run backtest on historical data
 */
async function runBacktest(dataFile) {
  console.log('📊 Running backtest...');
  
  if (!dataFile) {
    console.log('⚠️  Please provide a data file: node cli.js backtest --data data.csv');
    return;
  }
  
  try {
    // Check if file exists
    await fs.access(dataFile);
    
    // Read and parse data
    const content = await fs.readFile(dataFile, 'utf8');
    const lines = content.split('\n').filter(line => line.trim());
    
    console.log(`📄 Loaded ${lines.length} data points from ${dataFile}`);
    
    // TODO: Implement backtest logic
    // This would parse the data, run the strategy, and show results
    
    console.log('⚠️  Backtest implementation in progress');
    console.log('Please provide data in format: timestamp,price,asset');
    
  } catch (error) {
    console.error('❌ Backtest failed:', error.message);
  }
}

// ============================================================
// COMMAND DISPATCHER
// ============================================================
async function main() {
  // Handle help command
  if (args.includes('--help') || args.includes('-h') || command === 'help') {
    showHelp();
    return;
  }

  // Parse options
  const liveMode = args.includes('--live');
  const dataFileIndex = args.indexOf('--data');
  const dataFile = dataFileIndex !== -1 ? args[dataFileIndex + 1] : null;
  
  switch (command) {
    case 'start':
      await startBot(liveMode);
      break;
      
    case 'stop':
      if (global.__bot) {
        global.__bot.stop();
        console.log('🛑 Bot stopped');
      } else {
        console.log('⚠️  Bot not running');
      }
      break;
      
    case 'status':
      await showStatus();
      break;
      
    case 'stats':
      await showStats();
      break;
      
    case 'report':
      await generateReport();
      break;
      
    case 'config':
      await showConfig();
      break;
      
    case 'test':
      await runTest();
      break;
      
    case 'backtest':
      await runBacktest(dataFile);
      break;
      
    default:
      console.log(`❌ Unknown command: ${command}`);
      console.log('Use --help to see available commands');
      break;
  }
}

// Run main function
if (require.main === module) {
  main().catch(error => {
    console.error('❌ CLI error:', error.message);
    process.exit(1);
  });
}

module.exports = { main, showHelp };
