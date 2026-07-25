/**
 * Risk Management Module
 * Handles position sizing, risk limits, and trade validation
 */

class RiskManager {
  constructor(config) {
    this.config = config;
    this.riskPerTrade = config.riskPerTrade || 2; // % of balance
    this.maxConsecutiveLosses = config.maxConsecutiveLosses || 3;
    this.maxDailyLosses = config.maxDailyLosses || 5;
    this.maxDailyTrades = config.maxDailyTrades || 20;
    this.minBalance = config.minBalance || 100;
    this.maxOpenTrades = config.maxOpenTrades || 3;
    this.tradeCooldown = config.tradeCooldown || 30000; // 30 seconds between trades
    
    // Daily tracking
    this.dailyStats = {
      trades: 0,
      wins: 0,
      losses: 0,
      profit: 0,
      consecutiveLosses: 0,
      date: this.getDateKey()
    };
    
    this.lastTradeTime = 0;
    this.openTradeCount = 0;
    this.balance = config.initialBalance || 10000;
  }

  /**
   * Get current date key for daily reset
   * @returns {string} Date key (YYYY-MM-DD)
   */
  getDateKey() {
    return new Date().toISOString().split('T')[0];
  }

  /**
   * Reset daily stats if new day
   */
  resetDailyStats() {
    const today = this.getDateKey();
    if (this.dailyStats.date !== today) {
      this.dailyStats = {
        trades: 0,
        wins: 0,
        losses: 0,
        profit: 0,
        consecutiveLosses: 0,
        date: today
      };
    }
  }

  /**
   * Check if a trade is allowed based on risk rules
   * @param {object} stats - Current trading stats
   * @returns {object} { allowed: boolean, reason: string }
   */
  canTrade(stats = {}) {
    this.resetDailyStats();
    
    // Check balance
    if (this.balance < this.minBalance) {
      return { allowed: false, reason: `Balance ${this.balance} below minimum ${this.minBalance}` };
    }

    // Check daily trade count
    if (this.dailyStats.trades >= this.maxDailyTrades) {
      return { allowed: false, reason: `Daily trades limit reached (${this.maxDailyTrades})` };
    }

    // Check daily losses
    if (this.dailyStats.losses >= this.maxDailyLosses) {
      return { allowed: false, reason: `Daily losses limit reached (${this.maxDailyLosses})` };
    }

    // Check consecutive losses from stats
    const consecutiveLosses = stats.consecutiveLosses || this.dailyStats.consecutiveLosses;
    if (consecutiveLosses >= this.maxConsecutiveLosses) {
      return { 
        allowed: false, 
        reason: `Max consecutive losses reached (${this.maxConsecutiveLosses}). Stopping to prevent further losses.` 
      };
    }

    // Check cooldown between trades
    const now = Date.now();
    if (now - this.lastTradeTime < this.tradeCooldown) {
      const remaining = Math.ceil((this.tradeCooldown - (now - this.lastTradeTime)) / 1000);
      return { allowed: false, reason: `Trade cooldown: ${remaining}s remaining` };
    }

    // Check max open trades
    if (this.openTradeCount >= this.maxOpenTrades) {
      return { allowed: false, reason: `Max open trades reached (${this.maxOpenTrades})` };
    }

    // Check if daily profit is positive and we've already made good profit
    if (this.dailyStats.profit > this.balance * 0.05) {
      // If profit is >5% of balance, be more conservative
      // This is a personal preference - you can adjust
      // return { allowed: false, reason: 'Daily profit target reached' };
    }

    return { allowed: true, reason: 'Trade allowed' };
  }

  /**
   * Calculate position size based on risk per trade
   * @param {object} stats - Current trading stats
   * @param {number} overrideRisk - Optional override risk percentage
   * @returns {number} Position size in currency
   */
  calculatePositionSize(stats = {}, overrideRisk = null) {
    this.resetDailyStats();
    
    // Use risk per trade from config or override
    let riskPercent = overrideRisk || this.riskPerTrade;
    
    // Adjust risk based on consecutive losses (reduce risk after losses)
    const consecutiveLosses = stats.consecutiveLosses || this.dailyStats.consecutiveLosses;
    if (consecutiveLosses > 0) {
      // Reduce risk by 20% per consecutive loss
      const reduction = Math.min(consecutiveLosses * 0.2, 0.8);
      riskPercent = riskPercent * (1 - reduction);
      riskPercent = Math.max(riskPercent, 0.5); // Minimum 0.5% of balance
    }
    
    // Calculate position size
    const size = (this.balance * riskPercent) / 100;
    
    // Round to sensible values
    return Math.round(size * 100) / 100;
  }

  /**
   * Update risk stats after a trade
   * @param {object} trade - Trade result
   */
  updateStats(trade) {
    this.resetDailyStats();
    
    this.dailyStats.trades++;
    this.lastTradeTime = Date.now();
    
    if (trade.result === 'win') {
      this.dailyStats.wins++;
      this.dailyStats.profit += trade.profit || 0;
      this.dailyStats.consecutiveLosses = 0;
    } else if (trade.result === 'loss') {
      this.dailyStats.losses++;
      this.dailyStats.profit -= trade.amount || 0;
      this.dailyStats.consecutiveLosses++;
    }
  }

  /**
   * Update balance
   * @param {number} balance - New balance
   */
  updateBalance(balance) {
    this.balance = balance;
  }

  /**
   * Track open trade count
   * @param {number} count - Number of open trades
   */
  updateOpenTrades(count) {
    this.openTradeCount = count;
  }

  /**
   * Get current risk status
   * @returns {object} Risk status
   */
  getStatus() {
    this.resetDailyStats();
    
    return {
      balance: this.balance,
      riskPerTrade: this.riskPerTrade,
      dailyTrades: this.dailyStats.trades,
      dailyWins: this.dailyStats.wins,
      dailyLosses: this.dailyStats.losses,
      dailyProfit: this.dailyStats.profit,
      consecutiveLosses: this.dailyStats.consecutiveLosses,
      maxDailyTrades: this.maxDailyTrades,
      maxDailyLosses: this.maxDailyLosses,
      maxConsecutiveLosses: this.maxConsecutiveLosses,
      openTrades: this.openTradeCount,
      maxOpenTrades: this.maxOpenTrades,
      lastTradeTime: this.lastTradeTime
    };
  }

  /**
   * Set custom risk parameters
   * @param {object} params - Risk parameters
   */
  setParams(params) {
    if (params.riskPerTrade !== undefined) {
      this.riskPerTrade = params.riskPerTrade;
    }
    if (params.maxConsecutiveLosses !== undefined) {
      this.maxConsecutiveLosses = params.maxConsecutiveLosses;
    }
    if (params.maxDailyLosses !== undefined) {
      this.maxDailyLosses = params.maxDailyLosses;
    }
    if (params.maxDailyTrades !== undefined) {
      this.maxDailyTrades = params.maxDailyTrades;
    }
    if (params.maxOpenTrades !== undefined) {
      this.maxOpenTrades = params.maxOpenTrades;
    }
    if (params.tradeCooldown !== undefined) {
      this.tradeCooldown = params.tradeCooldown;
    }
  }

  /**
   * Check if we should stop trading for the day
   * @returns {boolean} True if should stop
   */
  shouldStopDay() {
    this.resetDailyStats();
    
    // Stop if daily losses exceeded
    if (this.dailyStats.losses >= this.maxDailyLosses) {
      return true;
    }
    
    // Stop if daily trades exceeded
    if (this.dailyStats.trades >= this.maxDailyTrades) {
      return true;
    }
    
    // Stop if consecutive losses exceeded
    if (this.dailyStats.consecutiveLosses >= this.maxConsecutiveLosses) {
      return true;
    }
    
    return false;
  }

  /**
   * Get recommended trade amount
   * @param {object} stats - Current stats
   * @param {number} customRisk - Custom risk percentage
   * @returns {number} Recommended trade amount
   */
  getRecommendedAmount(stats = {}, customRisk = null) {
    const size = this.calculatePositionSize(stats, customRisk);
    
    // Round to nearest 0.01 for forex
    return Math.round(size * 100) / 100;
  }

  /**
   * Validate a trade before execution
   * @param {object} trade - Trade parameters
   * @param {object} stats - Current stats
   * @returns {object} { valid: boolean, issues: string[] }
   */
  validateTrade(trade, stats = {}) {
    const issues = [];
    
    // Check amount
    if (!trade.amount || trade.amount <= 0) {
      issues.push('Invalid trade amount');
    }
    
    // Check if amount exceeds balance
    if (trade.amount > this.balance) {
      issues.push('Trade amount exceeds balance');
    }
    
    // Check if amount is too small
    const minTrade = this.config.minTrade || 1;
    if (trade.amount < minTrade) {
      issues.push(`Trade amount below minimum (${minTrade})`);
    }
    
    // Check asset
    if (!trade.asset) {
      issues.push('Missing asset symbol');
    }
    
    // Check type
    if (!trade.type || !['CALL', 'PUT'].includes(trade.type)) {
      issues.push('Invalid trade type. Must be CALL or PUT');
    }
    
    // Check expiry
    if (!trade.expiryMinutes || trade.expiryMinutes <= 0) {
      issues.push('Invalid expiry time');
    }
    
    // Check risk limits
    const riskCheck = this.canTrade(stats);
    if (!riskCheck.allowed) {
      issues.push(riskCheck.reason);
    }
    
    return {
      valid: issues.length === 0,
      issues
    };
  }
}

module.exports = { RiskManager };
