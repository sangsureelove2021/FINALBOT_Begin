/**
 * Multi-Strategy Signal Generator
 * Combines RSI with MACD and Moving Averages for enhanced trading signals
 * 
 * @module trading/multiStrategy
 * @requires RSIStrategy
 * 
 * Features:
 * - RSI overbought/oversold detection
 * - MACD crossover signals
 * - Moving average trend confirmation
 * - Risk-adjusted position sizing
 * - Signal strength scoring
 * - Cooldown period management
 */

const { RSIStrategy } = require('./strategy');

/**
 * Enhanced trading strategy combining multiple indicators
 */
class MultiStrategy extends RSIStrategy {
  /**
   * Create a multi-strategy instance
   * @param {Object} config - Configuration object
   * @param {number} config.rsiPeriod - RSI calculation period (default: 14)
   * @param {number} config.rsiOversoldThreshold - RSI oversold threshold (default: 30)
   * @param {number} config.rsiOverboughtThreshold - RSI overbought threshold (default: 70)
   * @param {number} config.macdFastPeriod - MACD fast EMA period (default: 12)
   * @param {number} config.macdSlowPeriod - MACD slow EMA period (default: 26)
   * @param {number} config.macdSignalPeriod - MACD signal line period (default: 9)
   * @param {number} config.smaPeriod - Simple Moving Average period (default: 20)
   * @param {number} config.emaPeriod - Exponential Moving Average period (default: 50)
   * @param {number} config.signalCooldownMs - Minimum time between signals in ms (default: 60000)
   * @param {number} config.minSignalStrength - Minimum signal strength to act (0-100) (default: 60)
   * @param {number} config.positionSizeBase - Base position size as percentage of capital (default: 2)
   * @param {number} config.maxPositionSize - Maximum position size percentage (default: 10)
   */
  constructor(config) {
    super(config);
    
    // MACD parameters
    this.macdFast = config.macdFastPeriod || 12;
    this.macdSlow = config.macdSlowPeriod || 26;
    this.macdSignal = config.macdSignalPeriod || 9;
    
    // Moving average parameters
    this.smaPeriod = config.smaPeriod || 20;
    this.emaPeriod = config.emaPeriod || 50;
    
    // Signal cooldown
    this.signalCooldownMs = config.signalCooldownMs || 60000; // 1 minute
    
    // Strength thresholds
    this.minSignalStrength = config.minSignalStrength || 60;
    this.positionSizeBase = config.positionSizeBase || 2;
    this.maxPositionSize = config.maxPositionSize || 10;
    
    // Track signal history for each asset
    this.signalHistory = {};
    this.performancetracking = {};
  }

  /**
   * Calculate MACD (Moving Average Convergence Divergence)
   * @param {number[]} prices - Array of closing prices
   * @param {number} fastPeriod - Fast EMA period
   * @param {number} slowPeriod - Slow EMA period
   * @param {number} signalPeriod - Signal line period
   * @returns {Object|null} MACD result with macd, signal, and histogram values
   */
  calculateMACD(prices, fastPeriod, slowPeriod, signalPeriod) {
    if (!prices || prices.length < slowPeriod + signalPeriod) {
      return null;
    }

    const fastPeriodActual = fastPeriod || this.macdFast;
    const slowPeriodActual = slowPeriod || this.macdSlow;
    const signalPeriodActual = signalPeriod || this.macdSignal;

    // Calculate EMAs
    const fastEMA = this.calculateEMA(prices, fastPeriodActual);
    const slowEMA = this.calculateEMA(prices, slowPeriodActual);

    if (fastEMA === null || slowEMA === null) {
      return null;
    }

    // Calculate MACD line (fast EMA - slow EMA)
    const macdLine = fastEMA - slowEMA;

    // Calculate signal line (EMA of MACD line)
    // For signal line, we need the history of MACD values
    const macdHistory = this.calculateMACDHistory(prices, fastPeriodActual, slowPeriodActual);
    if (!macdHistory || macdHistory.length < signalPeriodActual) {
      return null;
    }

    const signalLine = this.calculateEMA(macdHistory, signalPeriodActual);
    
    if (signalLine === null) {
      return null;
    }

    // Calculate histogram (MACD line - signal line)
    const histogram = macdLine - signalLine;

    return {
      macd: Math.round(macdLine * 10000) / 10000,
      signal: Math.round(signalLine * 10000) / 10000,
      histogram: Math.round(histogram * 10000) / 10000
    };
  }

  /**
   * Calculate MACD history for signal line calculation
   * @param {number[]} prices - Array of closing prices
   * @param {number} fastPeriod - Fast EMA period
   * @param {number} slowPeriod - Slow EMA period
   * @returns {number[]} Array of MACD values
   */
  calculateMACDHistory(prices, fastPeriod, slowPeriod) {
    if (!prices || prices.length < slowPeriod + 1) {
      return null;
    }

    const macdValues = [];
    const fastPeriodActual = fastPeriod || this.macdFast;
    const slowPeriodActual = slowPeriod || this.macdSlow;

    // Start from the point where we have enough data
    for (let i = slowPeriodActual; i < prices.length; i++) {
      const slice = prices.slice(0, i + 1);
      const fastEMA = this.calculateEMA(slice, fastPeriodActual);
      const slowEMA = this.calculateEMA(slice, slowPeriodActual);
      
      if (fastEMA !== null && slowEMA !== null) {
        macdValues.push(fastEMA - slowEMA);
      }
    }

    return macdValues;
  }

  /**
   * Calculate Exponential Moving Average
   * @param {number[]} data - Array of values
   * @param {number} period - EMA period
   * @returns {number|null} EMA value
   */
  calculateEMA(data, period) {
    if (!data || data.length < period) {
      return null;
    }

    const multiplier = 2 / (period + 1);
    let ema = data[0]; // Start with first value

    for (let i = 1; i < data.length; i++) {
      ema = (data[i] - ema) * multiplier + ema;
    }

    return Math.round(ema * 10000) / 10000;
  }

  /**
   * Calculate Simple Moving Average
   * @param {number[]} data - Array of values
   * @param {number} period - SMA period
   * @returns {number|null} SMA value
   */
  calculateSMA(data, period) {
    if (!data || data.length < period) {
      return null;
    }

    const slice = data.slice(-period);
    const sum = slice.reduce((a, b) => a + b, 0);
    return Math.round((sum / period) * 10000) / 10000;
  }

  /**
   * Get the current trend based on moving averages
   * @param {number[]} prices - Array of closing prices
   * @returns {Object} Trend information
   */
  getTrend(prices) {
    const currentPrice = prices[prices.length - 1];
    const sma = this.calculateSMA(prices, this.smaPeriod);
    const ema = this.calculateEMA(prices, this.emaPeriod);

    if (sma === null || ema === null) {
      return { trend: 'neutral', strength: 0 };
    }

    // Determine trend
    let trend = 'neutral';
    let strength = 0;

    if (currentPrice > ema && ema > sma) {
      trend = 'bullish';
      strength = 70;
    } else if (currentPrice < ema && ema < sma) {
      trend = 'bearish';
      strength = 70;
    } else if (currentPrice > ema) {
      trend = 'bullish';
      strength = 40;
    } else if (currentPrice < ema) {
      trend = 'bearish';
      strength = 40;
    }

    return {
      trend,
      strength,
      sma,
      ema,
      price: currentPrice
    };
  }

  /**
   * Check for MACD crossover signals
   * @param {number[]} prices - Array of closing prices
   * @returns {Object|null} MACD signal or null
   */
  checkMACDSignal(prices) {
    if (!prices || prices.length < this.macdSlow + this.macdSignal + 1) {
      return null;
    }

    // Get MACD history
    const macdHistory = this.calculateMACDHistory(prices, this.macdFast, this.macdSlow);
    if (!macdHistory || macdHistory.length < this.macdSignal + 1) {
      return null;
    }

    // Calculate signal line for the last two periods
    const signalValues = [];
    const macdValues = [];

    for (let i = macdHistory.length - this.macdSignal - 1; i < macdHistory.length; i++) {
      const slice = macdHistory.slice(0, i + 1);
      const signal = this.calculateEMA(slice, this.macdSignal);
      if (signal !== null) {
        signalValues.push(signal);
        macdValues.push(macdHistory[i]);
      }
    }

    if (signalValues.length < 2 || macdValues.length < 2) {
      return null;
    }

    // Check for crossover
    const prevMacd = macdValues[macdValues.length - 2];
    const currMacd = macdValues[macdValues.length - 1];
    const prevSignal = signalValues[signalValues.length - 2];
    const currSignal = signalValues[signalValues.length - 1];

    // MACD crossing above signal line (bullish)
    if (prevMacd <= prevSignal && currMacd > currSignal) {
      return { type: 'CALL', macd: currMacd, signal: currSignal, histogram: currMacd - currSignal };
    }
    
    // MACD crossing below signal line (bearish)
    if (prevMacd >= prevSignal && currMacd < currSignal) {
      return { type: 'PUT', macd: currMacd, signal: currSignal, histogram: currMacd - currSignal };
    }

    return null;
  }

  /**
   * Generate trading signal with multi-strategy confirmation
   * @param {string} asset - Asset symbol
   * @param {Object} priceData - Price data with prices and current price
   * @returns {Object|null} Enhanced signal object or null
   */
  generateSignal(asset, priceData) {
    const prices = priceData.prices;
    const currentPrice = priceData.price || prices[prices.length - 1];

    if (!prices || prices.length < Math.max(this.smaPeriod, this.emaPeriod, this.macdSlow + this.macdSignal)) {
      console.log(`⚠️ ${asset}: Insufficient price data for multi-strategy analysis`);
      return null;
    }

    // Calculate all indicators
    const rsi = this.calculateRSI(prices);
    const macd = this.calculateMACD(prices);
    const trend = this.getTrend(prices);
    const macdSignal = this.checkMACDSignal(prices);

    if (rsi === null || macd === null) {
      return null;
    }

    // Initialize signal components
    let signalType = null;
    let signalStrength = 0;
    const reasons = [];

    // ---- RSI Analysis ----
    let rsiSignal = null;
    if (rsi <= this.oversoldThreshold) {
      rsiSignal = 'CALL';
      reasons.push(`RSI oversold (${rsi.toFixed(2)})`);
      signalStrength += 30;
    } else if (rsi >= this.overboughtThreshold) {
      rsiSignal = 'PUT';
      reasons.push(`RSI overbought (${rsi.toFixed(2)})`);
      signalStrength += 30;
    }

    // ---- MACD Analysis ----
    let macdType = null;
    if (macdSignal) {
      macdType = macdSignal.type;
      reasons.push(`MACD crossover (${macdSignal.type})`);
      signalStrength += 40;
    }

    // ---- Trend Analysis ----
    let trendType = null;
    if (trend.trend === 'bullish') {
      trendType = 'CALL';
      reasons.push(`Bullish trend (SMA/EMA)`);
      signalStrength += 20;
    } else if (trend.trend === 'bearish') {
      trendType = 'PUT';
      reasons.push(`Bearish trend (SMA/EMA)`);
      signalStrength += 20;
    }

    // ---- Combine signals ----
    // Need at least RSI or MACD to generate a signal
    if (!rsiSignal && !macdType) {
      return null;
    }

    // Determine final signal type
    if (rsiSignal && macdType && rsiSignal === macdType) {
      // Strong confirmation: both RSI and MACD agree
      signalType = rsiSignal;
      signalStrength += 20; // Bonus for agreement
      reasons.push('Signal alignment: RSI + MACD agree');
    } else if (rsiSignal && !macdType) {
      // Only RSI signal
      signalType = rsiSignal;
    } else if (!rsiSignal && macdType) {
      // Only MACD signal
      signalType = macdType;
      // MACD signal is weaker without RSI confirmation
      signalStrength = Math.min(signalStrength, 50);
    } else {
      // RSI and MACD disagree - wait for confirmation
      return null;
    }

    // Check trend alignment (trend acts as filter)
    if (trendType && signalType === trendType) {
      signalStrength += 15;
      reasons.push('Trend aligns with signal');
    } else if (trendType && signalType !== trendType) {
      // Signal against trend - reduce confidence
      signalStrength -= 15;
      reasons.push('Signal against trend (caution)');
    }

    // Normalize signal strength (0-100)
    signalStrength = Math.max(0, Math.min(100, signalStrength));

    // Check minimum strength threshold
    if (signalStrength < this.minSignalStrength) {
      reasons.push(`Signal strength (${signalStrength}) below threshold (${this.minSignalStrength})`);
      console.log(`📉 ${asset}: Signal rejected - ${reasons.join(', ')}`);
      return null;
    }

    // Check cooldown
    const lastSignal = this.signalHistory[asset];
    if (lastSignal) {
      const timeSinceLastSignal = Date.now() - lastSignal.timestamp;
      if (timeSinceLastSignal < this.signalCooldownMs) {
        console.log(`⏳ ${asset}: Cooldown active (${Math.round(timeSinceLastSignal/1000)}s remaining)`);
        return null;
      }
    }

    // Calculate position size based on signal strength
    const positionSize = this.calculatePositionSize(signalStrength);

    // Create enhanced signal object
    const signal = {
      asset,
      type: signalType,
      rsi: Math.round(rsi * 100) / 100,
      macd,
      price: currentPrice,
      strength: signalStrength,
      positionSize: Math.round(positionSize * 100) / 100,
      reasons: reasons,
      timestamp: Date.now(),
      expiryMinutes: this.config.expiryMinutes || 5,
      entryPrice: currentPrice,
      indicators: {
        rsi,
        macd,
        sma: trend.sma,
        ema: trend.ema,
        trend: trend.trend
      }
    };

    // Log the signal
    console.log(`📊 ${asset}: ${signalType} signal generated`);
    console.log(`   Strength: ${signalStrength}% | Position: ${positionSize}% | RSI: ${rsi.toFixed(2)}`);
    console.log(`   Reasons: ${reasons.join(', ')}`);

    // Store signal history
    this.signalHistory[asset] = {
      type: signalType,
      strength: signalStrength,
      timestamp: Date.now(),
      price: currentPrice
    };

    return signal;
  }

  /**
   * Calculate position size based on signal strength
   * @param {number} signalStrength - Signal strength (0-100)
   * @returns {number} Position size as percentage of capital
   */
  calculatePositionSize(signalStrength) {
    // Linear scaling from base to max based on signal strength
    const normalizedStrength = Math.max(0, Math.min(100, signalStrength));
    const sizeRange = this.maxPositionSize - this.positionSizeBase;
    const size = this.positionSizeBase + (normalizedStrength / 100) * sizeRange;
    
    // Cap at max
    return Math.min(this.maxPositionSize, Math.round(size * 100) / 100);
  }

  /**
   * Get detailed analysis for an asset
   * @param {string} asset - Asset symbol
   * @param {number[]} prices - Price data
   * @returns {Object} Comprehensive analysis
   */
  getDetailedAnalysis(asset, prices) {
    const rsi = this.calculateRSI(prices);
    const macd = this.calculateMACD(prices);
    const trend = this.getTrend(prices);
    const macdSignal = this.checkMACDSignal(prices);
    
    // Determine overall market condition
    let marketCondition = 'neutral';
    let signals = [];

    if (rsi !== null) {
      if (rsi <= this.oversoldThreshold) {
        signals.push('oversold');
        marketCondition = 'oversold';
      } else if (rsi >= this.overboughtThreshold) {
        signals.push('overbought');
        marketCondition = 'overbought';
      }
    }

    if (macdSignal) {
      signals.push(`macd_${macdSignal.type.toLowerCase()}`);
    }

    if (trend.trend !== 'neutral') {
      signals.push(`trend_${trend.trend}`);
    }

    return {
      asset,
      timestamp: new Date().toISOString(),
      indicators: {
        rsi: rsi !== null ? Math.round(rsi * 100) / 100 : null,
        macd: macd,
        sma: trend.sma,
        ema: trend.ema,
        trend: trend.trend,
        price: trend.price
      },
      signals: signals,
      marketCondition,
      signalCount: signals.length,
      analysis: {
        summary: this.generateAnalysisSummary(rsi, macd, trend),
        recommendation: this.generateRecommendation(rsi, macd, trend, macdSignal)
      }
    };
  }

  /**
   * Generate analysis summary
   * @param {number} rsi - RSI value
   * @param {Object} macd - MACD object
   * @param {Object} trend - Trend object
   * @returns {string} Summary text
   */
  generateAnalysisSummary(rsi, macd, trend) {
    const parts = [];
    
    if (rsi !== null) {
      parts.push(`RSI: ${rsi.toFixed(2)}`);
    }
    
    if (macd) {
      parts.push(`MACD: ${macd.macd}`);
    }
    
    if (trend) {
      parts.push(`Trend: ${trend.trend}`);
    }
    
    return parts.join(' | ');
  }

  /**
   * Generate trading recommendation
   * @param {number} rsi - RSI value
   * @param {Object} macd - MACD object
   * @param {Object} trend - Trend object
   * @param {Object} macdSignal - MACD signal
   * @returns {Object} Recommendation
   */
  generateRecommendation(rsi, macd, trend, macdSignal) {
    const score = { bullish: 0, bearish: 0 };

    // RSI contribution
    if (rsi !== null) {
      if (rsi <= this.oversoldThreshold) score.bullish += 2;
      else if (rsi >= this.overboughtThreshold) score.bearish += 2;
      else if (rsi < 40) score.bullish += 1;
      else if (rsi > 60) score.bearish += 1;
    }

    // MACD contribution
    if (macdSignal) {
      if (macdSignal.type === 'CALL') score.bullish += 2;
      else if (macdSignal.type === 'PUT') score.bearish += 2;
    }

    // Trend contribution
    if (trend) {
      if (trend.trend === 'bullish') score.bullish += 2;
      else if (trend.trend === 'bearish') score.bearish += 2;
    }

    const total = score.bullish + score.bearish;
    const confidence = total > 0 ? Math.max(score.bullish, score.bearish) / total : 0;

    let recommendation = 'neutral';
    if (score.bullish > score.bearish && confidence >= 0.4) {
      recommendation = 'buy_call';
    } else if (score.bearish > score.bullish && confidence >= 0.4) {
      recommendation = 'buy_put';
    }

    return {
      recommendation,
      confidence: Math.round(confidence * 100),
      score: { bullish: score.bullish, bearish: score.bearish }
    };
  }

  /**
   * Get strategy configuration
   * @returns {Object} Full strategy config
   */
  getConfig() {
    return {
      ...super.getConfig(),
      macdFast: this.macdFast,
      macdSlow: this.macdSlow,
      macdSignal: this.macdSignal,
      smaPeriod: this.smaPeriod,
      emaPeriod: this.emaPeriod,
      signalCooldownMs: this.signalCooldownMs,
      minSignalStrength: this.minSignalStrength,
      positionSizeBase: this.positionSizeBase,
      maxPositionSize: this.maxPositionSize
    };
  }

  /**
   * Reset signal history
   * @param {string} asset - Asset to reset, or null for all
   */
  resetHistory(asset) {
    if (asset) {
      delete this.signalHistory[asset];
      delete this.performancetracking[asset];
    } else {
      this.signalHistory = {};
      this.performancetracking = {};
    }
  }
}

module.exports = { MultiStrategy };
