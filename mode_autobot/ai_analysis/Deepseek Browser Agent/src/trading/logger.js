/**
 * Trade Logger Module
 * Logs trades, performance, and generates reports
 */

const fs = require('fs').promises;
const path = require('path');

class TradeLogger {
  constructor(config) {
    this.config = config;
    this.logDir = config.logDir || path.join(process.cwd(), 'logs', 'trading');
    this.trades = [];
    this.initialized = false;
    this.cache = {
      summary: null,
      lastUpdate: 0
    };
  }

  /**
   * Initialize logger
   */
  async initialize() {
    if (this.initialized) return;
    
    try {
      // Create log directory
      await fs.mkdir(this.logDir, { recursive: true });
      
      // Load existing trades
      await this.loadTrades();
      
      this.initialized = true;
      console.log(`📁 Log directory: ${this.logDir}`);
    } catch (error) {
      console.error('❌ Logger initialization failed:', error.message);
      throw error;
    }
  }

  /**
   * Get today's log file path
   * @returns {string} Log file path
   */
  getLogFilePath() {
    const date = new Date().toISOString().split('T')[0];
    return path.join(this.logDir, `trades_${date}.json`);
  }

  /**
   * Load trades from log file
   */
  async loadTrades() {
    const filePath = this.getLogFilePath();
    try {
      const data = await fs.readFile(filePath, 'utf8');
      const parsed = JSON.parse(data);
      this.trades = parsed.trades || [];
      this.cache.summary = parsed.summary || null;
    } catch (error) {
      if (error.code === 'ENOENT') {
        // File doesn't exist yet
        this.trades = [];
        this.cache.summary = null;
      } else {
        console.error('⚠️ Error loading trades:', error.message);
        this.trades = [];
      }
    }
  }

  /**
   * Log a trade
   * @param {object} trade - Trade object
   */
  async logTrade(trade) {
    if (!this.initialized) {
      await this.initialize();
    }

    // Add trade to memory
    const logEntry = {
      ...trade,
      loggedAt: new Date().toISOString()
    };
    
    this.trades.push(logEntry);
    
    // Save to file
    await this.saveTrades();
    
    // Also log to console
    this.logToConsole(logEntry);
  }

  /**
   * Save trades to file
   */
  async saveTrades() {
    const filePath = this.getLogFilePath();
    const data = {
      trades: this.trades,
      summary: this.generateSummary(),
      updatedAt: new Date().toISOString(),
      config: {
        riskPerTrade: this.config.riskPerTrade,
        expiryMinutes: this.config.expiryMinutes,
        assets: this.config.assets
      }
    };
    
    try {
      await fs.writeFile(filePath, JSON.stringify(data, null, 2), 'utf8');
    } catch (error) {
      console.error('❌ Error saving trades:', error.message);
    }
  }

  /**
   * Log trade to console
   * @param {object} trade - Trade object
   */
  logToConsole(trade) {
    const timestamp = new Date(trade.timestamp).toLocaleTimeString();
    const status = trade.result ? trade.result.toUpperCase() : 'PENDING';
    const profit = trade.profit ? (trade.profit > 0 ? '+' : '') + trade.profit.toFixed(2) : '...';
    
    console.log(`
┌─────────────────────────────────────────────
│ 📊 TRADE #${trade.id} ${timestamp}
│ Asset: ${trade.asset} | Type: ${trade.type} | RSI: ${trade.rsi?.toFixed(2) || 'N/A'}
│ Amount: ${trade.amount} | Expiry: ${trade.expiryMinutes}m
│ Status: ${status} | P/L: ${profit}
└─────────────────────────────────────────────
    `);
  }

  /**
   * Generate summary statistics
   * @returns {object} Summary statistics
   */
  generateSummary() {
    const totalTrades = this.trades.length;
    const closedTrades = this.trades.filter(t => t.status === 'closed');
    const wins = closedTrades.filter(t => t.result === 'win');
    const losses = closedTrades.filter(t => t.result === 'loss');
    
    const totalProfit = closedTrades.reduce((sum, t) => sum + (t.profit || 0), 0);
    const avgWin = wins.length > 0 ? wins.reduce((sum, t) => sum + (t.profit || 0), 0) / wins.length : 0;
    const avgLoss = losses.length > 0 ? losses.reduce((sum, t) => sum + Math.abs(t.profit || 0), 0) / losses.length : 0;
    const winRate = closedTrades.length > 0 ? (wins.length / closedTrades.length) * 100 : 0;
    
    // P/L by asset
    const byAsset = {};
    for (const trade of closedTrades) {
      if (!byAsset[trade.asset]) {
        byAsset[trade.asset] = { trades: 0, wins: 0, losses: 0, profit: 0 };
      }
      byAsset[trade.asset].trades++;
      if (trade.result === 'win') {
        byAsset[trade.asset].wins++;
        byAsset[trade.asset].profit += trade.profit || 0;
      } else {
        byAsset[trade.asset].losses++;
        byAsset[trade.asset].profit -= trade.amount || 0;
      }
    }
    
    // P/L by signal type
    const byType = {
      CALL: { trades: 0, wins: 0, profit: 0 },
      PUT: { trades: 0, wins: 0, profit: 0 }
    };
    for (const trade of closedTrades) {
      const type = trade.type || 'UNKNOWN';
      if (!byType[type]) byType[type] = { trades: 0, wins: 0, profit: 0 };
      byType[type].trades++;
      if (trade.result === 'win') {
        byType[type].wins++;
        byType[type].profit += trade.profit || 0;
      } else {
        byType[type].profit -= trade.amount || 0;
      }
    }
    
    // Consecutive losses streak
    let maxConsecutiveLosses = 0;
    let currentStreak = 0;
    for (const trade of closedTrades) {
      if (trade.result === 'loss') {
        currentStreak++;
        if (currentStreak > maxConsecutiveLosses) {
          maxConsecutiveLosses = currentStreak;
        }
      } else {
        currentStreak = 0;
      }
    }
    
    return {
      totalTrades,
      closedTrades: closedTrades.length,
      wins: wins.length,
      losses: losses.length,
      winRate: Math.round(winRate * 100) / 100,
      totalProfit: Math.round(totalProfit * 100) / 100,
      avgWin: Math.round(avgWin * 100) / 100,
      avgLoss: Math.round(avgLoss * 100) / 100,
      profitFactor: avgLoss > 0 ? Math.round((avgWin * wins.length) / (avgLoss * losses.length) * 100) / 100 : 0,
      maxConsecutiveLosses,
      byAsset,
      byType,
      lastTrade: closedTrades.length > 0 ? closedTrades[closedTrades.length - 1] : null
    };
  }

  /**
   * Get current summary
   * @param {boolean} refresh - Force refresh
   * @returns {object} Summary statistics
   */
  getSummary(refresh = false) {
    if (refresh || !this.cache.summary || Date.now() - this.cache.lastUpdate > 60000) {
      this.cache.summary = this.generateSummary();
      this.cache.lastUpdate = Date.now();
    }
    return this.cache.summary;
  }

  /**
   * Export trades to CSV format
   * @returns {string} CSV content
   */
  exportCSV() {
    const headers = ['ID', 'Timestamp', 'Asset', 'Type', 'Amount', 'Expiry', 'Entry Price', 'Exit Price', 'RSI', 'Result', 'P/L', 'Status'];
    const rows = this.trades.map(t => [
      t.id,
      new Date(t.timestamp).toISOString(),
      t.asset,
      t.type,
      t.amount,
      t.expiryMinutes,
      t.entryPrice || t.price || 'N/A',
      t.exitPrice || 'N/A',
      t.rsi || 'N/A',
      t.result || 'N/A',
      t.profit || 0,
      t.status
    ]);
    
    return [headers, ...rows].map(row => row.join(',')).join('\n');
  }

  /**
   * Export trades to JSON format
   * @returns {string} JSON content
   */
  exportJSON() {
    return JSON.stringify({
      summary: this.getSummary(true),
      trades: this.trades,
      generatedAt: new Date().toISOString()
    }, null, 2);
  }

  /**
   * Generate a performance report
   * @returns {string} Report text
   */
  generateReport() {
    const summary = this.getSummary(true);
    const report = `
═══════════════════════════════════════════════════════
  📈 TRADING PERFORMANCE REPORT
  Generated: ${new Date().toISOString()}
═══════════════════════════════════════════════════════

  SUMMARY STATISTICS
  ──────────────────
  Total Trades:      ${summary.totalTrades}
  Closed Trades:     ${summary.closedTrades}
  Wins:              ${summary.wins}
  Losses:            ${summary.losses}
  Win Rate:          ${summary.winRate}%
  Total P/L:         ${summary.totalProfit.toFixed(2)}
  Average Win:       ${summary.avgWin.toFixed(2)}
  Average Loss:      ${summary.avgLoss.toFixed(2)}
  Profit Factor:     ${summary.profitFactor}
  Max Consecutive Losses: ${summary.maxConsecutiveLosses}

  PERFORMANCE BY ASSET
  ────────────────────
`;
    let byAssetReport = '';
    for (const [asset, data] of Object.entries(summary.byAsset || {})) {
      const winRate = data.trades > 0 ? (data.wins / data.trades * 100).toFixed(1) : 0;
      byAssetReport += `  ${asset}: ${data.trades} trades | ${data.wins} wins | ${winRate}% win | P/L: ${data.profit.toFixed(2)}\n`;
    }
    
    let byTypeReport = '\n  PERFORMANCE BY TYPE\n  ────────────────────\n';
    for (const [type, data] of Object.entries(summary.byType || {})) {
      const winRate = data.trades > 0 ? (data.wins / data.trades * 100).toFixed(1) : 0;
      byTypeReport += `  ${type}: ${data.trades} trades | ${data.wins} wins | ${winRate}% win | P/L: ${data.profit.toFixed(2)}\n`;
    }
    
    return report + byAssetReport + byTypeReport + '\n═══════════════════════════════════════════════════════\n';
  }

  /**
   * Save report to file
   * @param {string} filename - Report filename
   */
  async saveReport(filename = null) {
    if (!filename) {
      const date = new Date().toISOString().split('T')[0];
      filename = `report_${date}.txt`;
    }
    
    const filePath = path.join(this.logDir, filename);
    const report = this.generateReport();
    
    await fs.writeFile(filePath, report, 'utf8');
    console.log(`📄 Report saved: ${filePath}`);
    return filePath;
  }

  /**
   * Get all trades
   * @param {object} filters - Filter criteria
   * @returns {object[]} Filtered trades
   */
  getTrades(filters = {}) {
    let result = this.trades;
    
    if (filters.asset) {
      result = result.filter(t => t.asset === filters.asset);
    }
    if (filters.type) {
      result = result.filter(t => t.type === filters.type);
    }
    if (filters.result) {
      result = result.filter(t => t.result === filters.result);
    }
    if (filters.status) {
      result = result.filter(t => t.status === filters.status);
    }
    if (filters.startDate) {
      result = result.filter(t => t.timestamp >= filters.startDate);
    }
    if (filters.endDate) {
      result = result.filter(t => t.timestamp <= filters.endDate);
    }
    
    return result;
  }

  /**
   * Clear today's log
   */
  async clearToday() {
    this.trades = [];
    this.cache.summary = null;
    await this.saveTrades();
    console.log('🗑️ Today\'s trades cleared');
  }

  /**
   * Get log file paths for all days
   * @returns {string[]} Array of log file paths
   */
  async getLogFiles() {
    try {
      const files = await fs.readdir(this.logDir);
      return files.filter(f => f.startsWith('trades_') && f.endsWith('.json'));
    } catch (error) {
      return [];
    }
  }
}

module.exports = { TradeLogger };
