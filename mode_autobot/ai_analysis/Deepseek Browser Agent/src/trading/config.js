/**
 * Trading Bot Configuration
 * All settings for the RSI-based binary options trading bot
 */

module.exports = {
  // ============================================================
  // ASSETS TO TRADE
  // ============================================================
  assets: ['EUR/USD', 'GBP/USD'],

  // ============================================================
  // STRATEGY PARAMETERS
  // ============================================================
  // RSI Period (number of candles for calculation)
  rsiPeriod: 14,
  
  // RSI Oversold threshold (buy CALL when RSI < this value)
  rsiOversoldThreshold: 30,
  
  // RSI Overbought threshold (buy PUT when RSI > this value)
  rsiOverboughtThreshold: 70,

  // ============================================================
  // TRADE PARAMETERS
  // ============================================================
  // Expiry time in minutes
  expiryMinutes: 5,
  
  // Risk per trade as % of account balance
  riskPerTrade: 2,
  
  // Minimum trade amount (some brokers have minimums)
  minTrade: 1,
  
  // Payout rate (typical binary options payout: 70-90%)
  payoutRate: 0.85,

  // ============================================================
  // RISK MANAGEMENT
  // ============================================================
  // Maximum consecutive losses before stopping
  maxConsecutiveLosses: 3,
  
  // Maximum daily losses
  maxDailyLosses: 5,
  
  // Maximum daily trades
  maxDailyTrades: 20,
  
  // Maximum open trades at once
  maxOpenTrades: 3,
  
  // Minimum balance required to trade
  minBalance: 100,
  
  // Initial account balance (for simulation)
  initialBalance: 10000,
  
  // Trade cooldown between signals (milliseconds)
  tradeCooldown: 30000, // 30 seconds

  // ============================================================
  // BROKER SETTINGS
  // ============================================================
  // Run in simulation mode (set to false for live trading)
  simulationMode: true,
  
  // Broker type: 'deriv', 'mt5', 'iqoption', 'pocketoption', 'custom'
  brokerType: 'deriv',
  
  // Broker API endpoint (for live trading)
  brokerApiEndpoint: '',
  
  // Broker API key (for live trading)
  brokerApiKey: '',
  
  // Broker account ID (for live trading)
  brokerAccountId: '',

  // ============================================================
  // MONITORING & LOGGING
  // ============================================================
  // Check interval in seconds (how often to check for signals)
  checkInterval: 10,
  
  // Log directory
  logDir: 'logs/trading',
  
  // Enable detailed logging
  detailedLogging: true,
  
  // Enable console output
  consoleOutput: true,
  
  // Save trade logs to file
  saveTradeLogs: true,

  // ============================================================
  // PERFORMANCE OPTIMIZATION
  // ============================================================
  // Enable caching of price data
  enableCaching: true,
  
  // Cache TTL in seconds
  cacheTTL: 5,
  
  // Maximum price history length
  maxPriceHistory: 100,

  // ============================================================
  // NOTIFICATIONS
  // ============================================================
  // Enable notifications
  enableNotifications: false,
  
  // Notification webhook URL (e.g., Discord, Telegram, Slack)
  webhookUrl: '',
  
  // Email notification settings
  email: {
    enabled: false,
    from: '',
    to: '',
    smtpHost: '',
    smtpPort: 587,
    smtpUser: '',
    smtpPass: ''
  },

  // ============================================================
  // ADVANCED SETTINGS
  // ============================================================
  // Enable adaptive risk (adjust risk based on performance)
  adaptiveRisk: false,
  
  // Enable trend filtering (only trade in direction of trend)
  trendFiltering: false,
  
  // Enable multiple timeframe confirmation
  multipleTimeframe: false,
  
  // Secondary timeframe for confirmation (in minutes)
  secondaryTimeframe: 15,
  
  // Enable news filter (avoid trading during high-impact news)
  newsFilter: false,
  
  // News API key for filtering
  newsApiKey: ''
};

/**
 * Create a configuration with custom settings
 * @param {object} customSettings - Custom settings to override
 * @returns {object} Merged configuration
 */
function createConfig(customSettings = {}) {
  const base = require('./config');
  return { ...base, ...customSettings };
}

/**
 * Validate configuration
 * @param {object} config - Configuration to validate
 * @returns {object} { valid: boolean, errors: string[] }
 */
function validateConfig(config) {
  const errors = [];
  
  // Required fields
  if (!config.assets || !Array.isArray(config.assets) || config.assets.length === 0) {
    errors.push('assets must be a non-empty array');
  }
  
  // Numeric validations
  if (config.rsiPeriod < 2 || config.rsiPeriod > 100) {
    errors.push('rsiPeriod must be between 2 and 100');
  }
  
  if (config.rsiOversoldThreshold < 0 || config.rsiOversoldThreshold > 100) {
    errors.push('rsiOversoldThreshold must be between 0 and 100');
  }
  
  if (config.rsiOverboughtThreshold < 0 || config.rsiOverboughtThreshold > 100) {
    errors.push('rsiOverboughtThreshold must be between 0 and 100');
  }
  
  if (config.rsiOversoldThreshold >= config.rsiOverboughtThreshold) {
    errors.push('rsiOversoldThreshold must be less than rsiOverboughtThreshold');
  }
  
  if (config.expiryMinutes < 1 || config.expiryMinutes > 60) {
    errors.push('expiryMinutes must be between 1 and 60');
  }
  
  if (config.riskPerTrade < 0.1 || config.riskPerTrade > 20) {
    errors.push('riskPerTrade must be between 0.1 and 20');
  }
  
  if (config.maxConsecutiveLosses < 1 || config.maxConsecutiveLosses > 20) {
    errors.push('maxConsecutiveLosses must be between 1 and 20');
  }
  
  if (config.checkInterval < 1 || config.checkInterval > 300) {
    errors.push('checkInterval must be between 1 and 300');
  }
  
  return {
    valid: errors.length === 0,
    errors
  };
}

/**
 * Get environment-specific configuration
 * @param {string} env - Environment ('development', 'staging', 'production')
 * @returns {object} Environment-specific config
 */
function getEnvConfig(env = 'development') {
  const base = require('./config');
  
  const envConfigs = {
    development: {
      simulationMode: true,
      detailedLogging: true,
      consoleOutput: true,
      checkInterval: 10
    },
    staging: {
      simulationMode: true,
      detailedLogging: true,
      consoleOutput: true,
      checkInterval: 30
    },
    production: {
      simulationMode: false,
      detailedLogging: false,
      consoleOutput: true,
      checkInterval: 60
    }
  };
  
  return { ...base, ...envConfigs[env] };
}

module.exports = {
  ...module.exports,
  createConfig,
  validateConfig,
  getEnvConfig
};
