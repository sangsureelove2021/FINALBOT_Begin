/**
 * RSI Strategy Module
 * Generates trading signals based on RSI overbought/oversold conditions
 * Buy CALL when RSI < 30 (oversold)
 * Buy PUT when RSI > 70 (overbought)
 */

class RSIStrategy {
  constructor(config) {
    this.config = config;
    this.oversoldThreshold = config.rsiOversoldThreshold || 30;
    this.overboughtThreshold = config.rsiOverboughtThreshold || 70;
    this.period = config.rsiPeriod || 14;
    this.signalHistory = {};
    this.lastSignals = {};
  }

  /**
   * Calculate RSI from price data
   * @param {number[]} prices - Array of closing prices
   * @param {number} period - RSI period (default: 14)
   * @returns {number} RSI value
   */
  calculateRSI(prices, period = this.period) {
    if (!prices || prices.length < period + 1) {
      return null;
    }

    const changes = [];
    for (let i = 1; i < prices.length; i++) {
      changes.push(prices[i] - prices[i - 1]);
    }

    // Get the last 'period' changes
    const recentChanges = changes.slice(-period);
    
    let gains = 0;
    let losses = 0;

    for (const change of recentChanges) {
      if (change > 0) {
        gains += change;
      } else {
        losses += Math.abs(change);
      }
    }

    const avgGain = gains / period;
    const avgLoss = losses / period;

    if (avgLoss === 0) {
      return 100;
    }

    const rs = avgGain / avgLoss;
    const rsi = 100 - (100 / (1 + rs));

    return Math.round(rsi * 100) / 100;
  }

  /**
   * Generate a trading signal based on RSI
   * @param {string} asset - Asset symbol
   * @param {object} priceData - Price data with prices array and current price
   * @returns {object|null} Signal object or null if no signal
   */
  generateSignal(asset, priceData) {
    // Ensure we have enough price data
    if (!priceData.prices || priceData.prices.length < this.period + 1) {
      console.log(`⚠️ ${asset}: Insufficient price data for RSI calculation`);
      return null;
    }

    // Calculate RSI
    const rsi = this.calculateRSI(priceData.prices);
    if (rsi === null) {
      return null;
    }

    const currentPrice = priceData.price || priceData.prices[priceData.prices.length - 1];
    
    // Check for signal conditions
    let signalType = null;
    let signalStrength = 'neutral';

    // Oversold: RSI < 30 → Buy CALL (price expected to rise)
    if (rsi <= this.oversoldThreshold) {
      signalType = 'CALL';
      signalStrength = rsi <= 25 ? 'strong' : 'normal';
    }
    // Overbought: RSI > 70 → Buy PUT (price expected to fall)
    else if (rsi >= this.overboughtThreshold) {
      signalType = 'PUT';
      signalStrength = rsi >= 75 ? 'strong' : 'normal';
    }

    // No signal
    if (!signalType) {
      return null;
    }

    // Check if this signal already triggered recently (avoid duplicates)
    const lastSignal = this.lastSignals[asset];
    if (lastSignal) {
      const timeSinceLastSignal = Date.now() - lastSignal.timestamp;
      // Don't generate same signal type within cooldown period (30 seconds)
      if (lastSignal.type === signalType && timeSinceLastSignal < 30000) {
        return null;
      }
      // Don't generate opposite signal until signal has expired
      // We want to wait at least 2 minutes before reversing
      if (lastSignal.type !== signalType && timeSinceLastSignal < 120000) {
        return null;
      }
    }

    // Additional confirmation: check RSI direction
    // For CALL signals, we want to see RSI starting to rise from oversold
    // For PUT signals, we want to see RSI starting to fall from overbought
    const recentRSI = this.calculateRecentRSITrend(priceData.prices);
    if (recentRSI !== null) {
      const trend = this.getRSITrend(recentRSI);
      
      // Confirmation logic
      if (signalType === 'CALL' && trend === 'falling' && rsi < 35) {
        // Still acceptable if RSI is very low, but maybe wait for stabilization
        console.log(`⏳ ${asset}: RSI ${rsi} oversold but still falling, waiting for stabilization`);
        // Allow if extremely oversold (RSI < 25)
        if (rsi > 25) {
          return null;
        }
      }
      
      if (signalType === 'PUT' && trend === 'rising' && rsi > 65) {
        console.log(`⏳ ${asset}: RSI ${rsi} overbought but still rising, waiting for stabilization`);
        if (rsi < 75) {
          return null;
        }
      }
    }

    // Create signal object
    const signal = {
      asset,
      type: signalType,
      rsi,
      price: currentPrice,
      strength: signalStrength,
      timestamp: Date.now(),
      expiryMinutes: this.config.expiryMinutes || 5,
      entryPrice: currentPrice
    };

    // Store last signal
    this.lastSignals[asset] = {
      type: signalType,
      rsi,
      timestamp: Date.now(),
      price: currentPrice
    };

    // Log signal
    console.log(`📊 ${asset}: RSI=${rsi.toFixed(2)} → ${signalType} (${signalStrength})`);

    return signal;
  }

  /**
   * Calculate recent RSI trend
   * @param {number[]} prices - Price data
   * @param {number} lookback - Number of periods to check
   * @returns {number[]} Recent RSI values
   */
  calculateRecentRSITrend(prices, lookback = 3) {
    if (!prices || prices.length < this.period + lookback) {
      return null;
    }

    const rsiValues = [];
    for (let i = 0; i < lookback; i++) {
      const startIdx = prices.length - this.period - lookback + i;
      const endIdx = startIdx + this.period + 1;
      const slice = prices.slice(startIdx, endIdx);
      const rsi = this.calculateRSI(slice);
      if (rsi !== null) {
        rsiValues.push(rsi);
      }
    }

    return rsiValues.length >= 2 ? rsiValues : null;
  }

  /**
   * Determine RSI trend direction
   * @param {number[]} rsiValues - Array of RSI values
   * @returns {string} 'rising', 'falling', or 'neutral'
   */
  getRSITrend(rsiValues) {
    if (!rsiValues || rsiValues.length < 2) {
      return 'neutral';
    }

    const first = rsiValues[0];
    const last = rsiValues[rsiValues.length - 1];
    const diff = last - first;

    if (diff > 1) return 'rising';
    if (diff < -1) return 'falling';
    return 'neutral';
  }

  /**
   * Get detailed RSI analysis for an asset
   * @param {number[]} prices - Price data
   * @returns {object} Detailed RSI analysis
   */
  analyze(prices) {
    const rsi = this.calculateRSI(prices);
    if (rsi === null) {
      return { error: 'Insufficient data' };
    }

    const trend = this.calculateRecentRSITrend(prices);
    const direction = trend ? this.getRSITrend(trend) : 'neutral';

    let signal = 'neutral';
    if (rsi <= this.oversoldThreshold) {
      signal = 'oversold (BUY CALL)';
    } else if (rsi >= this.overboughtThreshold) {
      signal = 'overbought (BUY PUT)';
    }

    return {
      rsi,
      direction,
      signal,
      oversoldThreshold: this.oversoldThreshold,
      overboughtThreshold: this.overboughtThreshold,
      trend: direction,
      price: prices[prices.length - 1]
    };
  }

  /**
   * Reset signal history for an asset
   * @param {string} asset - Asset symbol
   */
  resetHistory(asset) {
    if (asset) {
      delete this.lastSignals[asset];
    } else {
      this.lastSignals = {};
    }
  }

  /**
   * Set custom thresholds
   * @param {number} oversold - Oversold threshold (default: 30)
   * @param {number} overbought - Overbought threshold (default: 70)
   */
  setThresholds(oversold, overbought) {
    this.oversoldThreshold = oversold || 30;
    this.overboughtThreshold = overbought || 70;
  }

  /**
   * Get current strategy configuration
   * @returns {object} Strategy config
   */
  getConfig() {
    return {
      oversoldThreshold: this.oversoldThreshold,
      overboughtThreshold: this.overboughtThreshold,
      period: this.period
    };
  }
}

module.exports = { RSIStrategy };
