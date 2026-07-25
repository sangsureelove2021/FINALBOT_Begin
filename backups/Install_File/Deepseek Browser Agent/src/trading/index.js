/**
 * Binary Options Trading Bot - Main Entry Point
 * RSI Strategy: Buy CALL when RSI < 30, Buy PUT when RSI > 70
 * Assets: EUR/USD, GBP/USD
 * Expiry: 5 minutes
 * Risk: 2% per trade
 */

const fs = require('fs').promises;
const path = require('path');
const { RSIStrategy } = require('./strategy');
const { BrokerConnector } = require('./broker');
const { RiskManager } = require('./risk');
const { TradeLogger } = require('./logger');
const { Scheduler } = require('./scheduler');
const config = require('./config');

class TradingBot {
  constructor(options = {}) {
    this.config = { ...config, ...options };
    this.isRunning = false;
    this.strategy = new RSIStrategy(this.config);
    this.broker = new BrokerConnector(this.config);
    this.riskManager = new RiskManager(this.config);
    this.logger = new TradeLogger(this.config);
    this.scheduler = new Scheduler(this.config);
    
    // Stats tracking
    this.stats = {
      totalTrades: 0,
      wins: 0,
      losses: 0,
      totalProfit: 0,
      winRate: 0,
      consecutiveLosses: 0,
      maxConsecutiveLosses: 0
    };
  }

  /**
   * Initialize the bot
   */
  async initialize() {
    try {
      console.log('🤖 Initializing Trading Bot...');
      console.log(`📊 Strategy: RSI (Overbought > 70, Oversold < 30)`);
      console.log(`💹 Assets: ${this.config.assets.join(', ')}`);
      console.log(`⏱️ Expiry: ${this.config.expiryMinutes} minutes`);
      console.log(`💰 Risk per trade: ${this.config.riskPerTrade}%`);
      
      await this.broker.connect();
      await this.logger.initialize();
      
      console.log('✅ Bot initialized successfully');
      return true;
    } catch (error) {
      console.error('❌ Initialization failed:', error.message);
      throw error;
    }
  }

  /**
   * Start the trading bot
   */
  async start() {
    if (this.isRunning) {
      console.log('⚠️ Bot is already running');
      return;
    }

    try {
      await this.initialize();
      this.isRunning = true;
      console.log('🚀 Trading bot started');
      console.log(`📡 Checking signals every ${this.config.checkInterval} seconds`);
      
      // Schedule regular checks
      this.scheduler.schedule(
        async () => await this.runCycle(),
        this.config.checkInterval * 1000
      );
      
      // Run initial cycle immediately
      await this.runCycle();
      
    } catch (error) {
      console.error('❌ Failed to start bot:', error.message);
      this.stop();
    }
  }

  /**
   * Stop the trading bot
   */
  stop() {
    this.isRunning = false;
    this.scheduler.stop();
    this.broker.disconnect();
    console.log('🛑 Trading bot stopped');
  }

  /**
   * Run one trading cycle
   */
  async runCycle() {
    if (!this.isRunning) return;
    
    try {
      console.log(`\n📈 [${new Date().toISOString()}] Checking signals...`);
      
      // Check each asset
      for (const asset of this.config.assets) {
        try {
          await this.processAsset(asset);
        } catch (error) {
          console.error(`❌ Error processing ${asset}:`, error.message);
        }
      }
      
      // Update stats display
      this.displayStats();
      
    } catch (error) {
      console.error('❌ Cycle error:', error.message);
    }
  }

  /**
   * Process a single asset
   */
  async processAsset(asset) {
    // Get current price data
    const priceData = await this.broker.getPriceData(asset);
    if (!priceData) {
      console.log(`⚠️ No price data for ${asset}`);
      return;
    }

    // Generate signal
    const signal = this.strategy.generateSignal(asset, priceData);
    
    if (!signal) {
      console.log(`⏸️ No signal for ${asset} (RSI: ${priceData.rsi?.toFixed(2) || 'N/A'})`);
      return;
    }

    console.log(`🎯 Signal detected for ${asset}: ${signal.type} (RSI: ${signal.rsi.toFixed(2)})`);

    // Check risk limits
    const riskCheck = this.riskManager.canTrade();
    if (!riskCheck.allowed) {
      console.log(`⛔ Risk limit reached: ${riskCheck.reason}`);
      return;
    }

    // Calculate position size
    const amount = this.riskManager.calculatePositionSize(this.stats);
    
    // Execute trade
    const trade = await this.broker.executeTrade({
      asset,
      type: signal.type,
      amount,
      expiryMinutes: this.config.expiryMinutes,
      entryPrice: priceData.price,
      rsi: signal.rsi,
      signal: signal
    });

    // Log trade
    await this.logger.logTrade(trade);
    this.updateStats(trade);

    console.log(`✅ Trade executed: ${asset} ${trade.type} ${trade.amount} expiry ${trade.expiryMinutes}m`);
  }

  /**
   * Update statistics after a trade
   */
  updateStats(trade) {
    this.stats.totalTrades++;
    
    if (trade.result === 'win') {
      this.stats.wins++;
      this.stats.totalProfit += trade.profit || 0;
      this.stats.consecutiveLosses = 0;
    } else if (trade.result === 'loss') {
      this.stats.losses++;
      this.stats.totalProfit -= trade.amount || 0;
      this.stats.consecutiveLosses++;
      if (this.stats.consecutiveLosses > this.stats.maxConsecutiveLosses) {
        this.stats.maxConsecutiveLosses = this.stats.consecutiveLosses;
      }
    }
    
    this.stats.winRate = this.stats.totalTrades > 0 
      ? (this.stats.wins / this.stats.totalTrades) * 100 
      : 0;
  }

  /**
   * Display current statistics
   */
  displayStats() {
    console.log(`\n📊 Stats: Trades=${this.stats.totalTrades} | ` +
                `Wins=${this.stats.wins} | Losses=${this.stats.losses} | ` +
                `WinRate=${this.stats.winRate.toFixed(1)}% | ` +
                `Profit=${this.stats.totalProfit.toFixed(2)} | ` +
                `ConsecutiveLosses=${this.stats.consecutiveLosses}`);
  }

  /**
   * Get current status
   */
  getStatus() {
    return {
      isRunning: this.isRunning,
      config: this.config,
      stats: this.stats,
      lastCheck: new Date().toISOString()
    };
  }
}

// CLI entry point
if (require.main === module) {
  const bot = new TradingBot();
  
  // Handle graceful shutdown
  process.on('SIGINT', () => {
    console.log('\n⚠️ Received SIGINT. Shutting down...');
    bot.stop();
    process.exit(0);
  });
  
  process.on('SIGTERM', () => {
    console.log('\n⚠️ Received SIGTERM. Shutting down...');
    bot.stop();
    process.exit(0);
  });
  
  bot.start().catch(error => {
    console.error('❌ Fatal error:', error);
    process.exit(1);
  });
}

module.exports = { TradingBot };
