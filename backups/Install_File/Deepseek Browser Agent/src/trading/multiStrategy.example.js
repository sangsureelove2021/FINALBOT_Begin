/**
 * MultiStrategy Example Usage
 * 
 * This file demonstrates how to use the MultiStrategy class
 * for real-world trading signal generation.
 * 
 * Run with: node src/trading/multiStrategy.example.js
 */

const { MultiStrategy } = require('./multiStrategy');

/**
 * Example 1: Basic setup with default configuration
 */
function exampleBasicSetup() {
  console.log('\n📊 Example 1: Basic Setup');
  console.log('─'.repeat(50));
  
  // Create strategy with default config
  const strategy = new MultiStrategy({
    expiryMinutes: 5
  });
  
  console.log('✅ Strategy created with default config');
  console.log(`   RSI Period: ${strategy.period}`);
  console.log(`   MACD: ${strategy.macdFast}/${strategy.macdSlow}/${strategy.macdSignal}`);
  console.log(`   Min Signal Strength: ${strategy.minSignalStrength}%`);
  
  return strategy;
}

/**
 * Example 2: Custom configuration for aggressive trading
 */
function exampleAggressiveConfig() {
  console.log('\n📊 Example 2: Aggressive Trading Configuration');
  console.log('─'.repeat(50));
  
  const strategy = new MultiStrategy({
    rsiPeriod: 10,
    rsiOversoldThreshold: 25,
    rsiOverboughtThreshold: 75,
    macdFastPeriod: 8,
    macdSlowPeriod: 20,
    macdSignalPeriod: 6,
    smaPeriod: 15,
    emaPeriod: 30,
    minSignalStrength: 50,
    positionSizeBase: 3,
    maxPositionSize: 15,
    signalCooldownMs: 30000, // 30 seconds
    expiryMinutes: 3
  });
  
  console.log('✅ Aggressive strategy configured');
  console.log(`   RSI: ${strategy.oversoldThreshold}/${strategy.overboughtThreshold}`);
  console.log(`   Position Size: ${strategy.positionSizeBase}%-${strategy.maxPositionSize}%`);
  console.log(`   Cooldown: ${strategy.signalCooldownMs/1000}s`);
  
  return strategy;
}

/**
 * Example 3: Generate signals from price data
 */
function exampleSignalGeneration() {
  console.log('\n📊 Example 3: Generating Trading Signals');
  console.log('─'.repeat(50));
  
  const strategy = new MultiStrategy({
    minSignalStrength: 40,
    expiryMinutes: 5
  });
  
  // Simulate price data for EUR/USD
  const eurUsdPrices = [
    1.1050, 1.1052, 1.1048, 1.1055, 1.1060, 1.1058, 1.1063, 1.1070,
    1.1065, 1.1072, 1.1080, 1.1075, 1.1082, 1.1090, 1.1085, 1.1095,
    1.1100, 1.1098, 1.1105, 1.1112, 1.1108, 1.1115, 1.1120, 1.1118,
    1.1125, 1.1130, 1.1128, 1.1135, 1.1140, 1.1138, 1.1145, 1.1150,
    1.1148, 1.1155, 1.1160, 1.1158, 1.1165, 1.1170, 1.1168, 1.1175,
    1.1180, 1.1178, 1.1185, 1.1190, 1.1188, 1.1195, 1.1200, 1.1198,
    1.1205, 1.1210, 1.1208, 1.1215, 1.1220, 1.1218, 1.1225, 1.1230,
    1.1228, 1.1235, 1.1240, 1.1238, 1.1245, 1.1250, 1.1248, 1.1255
  ];
  
  const priceData = {
    prices: eurUsdPrices,
    price: eurUsdPrices[eurUsdPrices.length - 1]
  };
  
  console.log('📈 Processing EUR/USD price data...');
  console.log(`   Current Price: ${priceData.price}`);
  console.log(`   Data Points: ${priceData.prices.length}`);
  
  // Generate signal
  const signal = strategy.generateSignal('EUR/USD', priceData);
  
  if (signal) {
    console.log('\n🎯 SIGNAL GENERATED:');
    console.log(`   Asset: ${signal.asset}`);
    console.log(`   Type: ${signal.type}`);
    console.log(`   Strength: ${signal.strength}%`);
    console.log(`   Position Size: ${signal.positionSize}%`);
    console.log(`   Price: ${signal.price}`);
    console.log(`   RSI: ${signal.rsi}`);
    console.log(`   Reasons: ${signal.reasons.join('; ')}`);
  } else {
    console.log('\nℹ️  No signal generated - waiting for stronger conditions');
  }
  
  return signal;
}

/**
 * Example 4: Multiple assets with different signals
 */
function exampleMultipleAssets() {
  console.log('\n📊 Example 4: Multi-Asset Trading');
  console.log('─'.repeat(50));
  
  const strategy = new MultiStrategy({
    minSignalStrength: 50,
    signalCooldownMs: 60000, // 1 minute
    expiryMinutes: 5
  });
  
  // Asset configurations
  const assets = [
    { 
      name: 'BTC/USD', 
      basePrice: 30000,
      volatility: 500,
      trend: 'bullish'
    },
    { 
      name: 'ETH/USD', 
      basePrice: 2000,
      volatility: 50,
      trend: 'bearish'
    },
    { 
      name: 'GBP/USD', 
      basePrice: 1.30,
      volatility: 0.015,
      trend: 'neutral'
    }
  ];
  
  console.log('📊 Analyzing multiple assets...\n');
  
  let signalsGenerated = 0;
  
  assets.forEach(asset => {
    // Generate synthetic price data
    const prices = [asset.basePrice];
    const trend = asset.trend === 'bullish' ? 0.5 : asset.trend === 'bearish' ? -0.5 : 0;
    
    for (let i = 1; i < 60; i++) {
      const change = trend + (Math.random() - 0.5) * asset.volatility * 0.1;
      const newPrice = Math.max(0.01, prices[i - 1] + change);
      prices.push(Math.round(newPrice * 10000) / 10000);
    }
    
    const priceData = {
      prices: prices,
      price: prices[prices.length - 1]
    };
    
    // Generate signal
    const signal = strategy.generateSignal(asset.name, priceData);
    
    if (signal) {
      signalsGenerated++;
      console.log(`✅ ${asset.name}: ${signal.type} signal (strength: ${signal.strength}%, size: ${signal.positionSize}%)`);
    } else {
      console.log(`⏳ ${asset.name}: No signal - ${asset.trend} trend`);
    }
  });
  
  console.log(`\n📈 Total signals generated: ${signalsGenerated}/${assets.length}`);
  return signalsGenerated;
}

/**
 * Example 5: Risk management with position sizing
 */
function exampleRiskManagement() {
  console.log('\n📊 Example 5: Risk Management & Position Sizing');
  console.log('─'.repeat(50));
  
  const strategy = new MultiStrategy({
    positionSizeBase: 2,
    maxPositionSize: 10,
    minSignalStrength: 30
  });
  
  const riskScenarios = [
    { strength: 30, confidence: 'low' },
    { strength: 50, confidence: 'medium' },
    { strength: 70, confidence: 'high' },
    { strength: 90, confidence: 'very high' }
  ];
  
  console.log('📊 Position Sizing Based on Signal Strength:\n');
  console.log('   Strength | Position Size | Confidence');
  console.log('   ' + '─'.repeat(40));
  
  riskScenarios.forEach(scenario => {
    const size = strategy.calculatePositionSize(scenario.strength);
    console.log(`   ${scenario.strength.toString().padStart(8)}% | ${size.toString().padStart(12)}% | ${scenario.confidence}`);
  });
  
  console.log('\n📊 Risk Management Rules:');
  console.log('   • Base position: 2% of capital');
  console.log('   • Max position: 10% of capital');
  console.log('   • Stop-loss: 2% per trade');
  console.log('   • Daily loss limit: 5% of capital');
  
  return strategy;
}

/**
 * Example 6: Get detailed analysis for decision making
 */
function exampleDetailedAnalysis() {
  console.log('\n📊 Example 6: Detailed Market Analysis');
  console.log('─'.repeat(50));
  
  const strategy = new MultiStrategy({});
  
  // Generate trending price data
  const prices = [100, 101, 102, 103, 104, 103.5, 104.5, 105, 106, 105.5,
    106.5, 107, 108, 107.5, 108.5, 109, 110, 109.5, 110.5, 111,
    112, 111.5, 112.5, 113, 114, 113.5, 114.5, 115, 116, 115.5,
    116.5, 117, 118, 117.5, 118.5, 119, 120, 119.5, 120.5, 121,
    122, 121.5, 122.5, 123, 124, 123.5, 124.5, 125, 126, 125.5];
  
  const analysis = strategy.getDetailedAnalysis('AAPL', prices);
  
  console.log(`📈 Analysis for ${analysis.asset}`);
  console.log(`   Timestamp: ${analysis.timestamp}`);
  console.log('\n   Indicators:');
  console.log(`   • RSI: ${analysis.indicators.rsi}`);
  console.log(`   • MACD: ${analysis.indicators.macd ? analysis.indicators.macd.macd : 'N/A'}`);
  console.log(`   • Signal: ${analysis.indicators.macd ? analysis.indicators.macd.signal : 'N/A'}`);
  console.log(`   • SMA: ${analysis.indicators.sma}`);
  console.log(`   • EMA: ${analysis.indicators.ema}`);
  console.log(`   • Trend: ${analysis.indicators.trend}`);
  console.log(`   • Price: ${analysis.indicators.price}`);
  
  console.log('\n   Signals:');
  analysis.signals.forEach(signal => {
    console.log(`   • ${signal}`);
  });
  
  console.log(`\n   Market Condition: ${analysis.marketCondition}`);
  console.log(`   Signal Count: ${analysis.signalCount}`);
  
  console.log('\n   Analysis Summary:');
  console.log(`   ${analysis.analysis.summary}`);
  console.log(`   Recommendation: ${analysis.analysis.recommendation.recommendation}`);
  console.log(`   Confidence: ${analysis.analysis.recommendation.confidence}%`);
  
  return analysis;
}

/**
 * Example 7: Real-time monitoring simulation
 */
function exampleRealTimeMonitoring() {
  console.log('\n📊 Example 7: Real-Time Monitoring Simulation');
  console.log('─'.repeat(50));
  
  const strategy = new MultiStrategy({
    minSignalStrength: 45,
    signalCooldownMs: 2000
  });
  
  console.log('🔄 Simulating real-time price updates...\n');
  
  // Simulate price updates
  let currentPrice = 1.1200;
  const updates = 10;
  
  for (let i = 0; i < updates; i++) {
    // Random walk
    const change = (Math.random() - 0.5) * 0.002;
    currentPrice = Math.round((currentPrice + change) * 10000) / 10000;
    
    // Build price history
    const prices = [];
    let price = currentPrice - 0.02;
    for (let j = 0; j < 60; j++) {
      price = Math.round((price + (Math.random() - 0.5) * 0.0008) * 10000) / 10000;
      prices.push(price);
    }
    prices.push(currentPrice);
    
    const priceData = {
      prices: prices,
      price: currentPrice
    };
    
    const signal = strategy.generateSignal('EUR/USD', priceData);
    
    if (signal) {
      console.log(`📍 Update ${i+1}: Price ${currentPrice} → ${signal.type} signal (${signal.strength}%)`);
    } else {
      console.log(`📍 Update ${i+1}: Price ${currentPrice} → No signal`);
    }
    
    // Small delay (removed for performance)
  }
  
  return strategy;
}

/**
 * Main execution
 */
function main() {
  console.log('🚀 MultiStrategy Example Suite\n');
  console.log('='.repeat(60));
  
  try {
    exampleBasicSetup();
    exampleAggressiveConfig();
    exampleSignalGeneration();
    exampleMultipleAssets();
    exampleRiskManagement();
    exampleDetailedAnalysis();
    exampleRealTimeMonitoring();
    
    console.log('\n' + '='.repeat(60));
    console.log('✅ All examples completed successfully!');
    console.log('\n📝 Key Takeaways:');
    console.log('   • MultiStrategy combines RSI, MACD, and trend analysis');
    console.log('   • Signals are validated with minimum strength thresholds');
    console.log('   • Position sizing adjusts based on signal confidence');
    console.log('   • Cooldown periods prevent overtrading');
    console.log('   • Detailed analysis provides actionable insights');
  } catch (err) {
    console.error(`\n❌ Error: ${err.message}`);
    if (err.stack) console.error(err.stack);
    process.exit(1);
  }
  
  console.log('\n💡 To integrate with your trading system:');
  console.log('   const { MultiStrategy } = require("./multiStrategy");');
  console.log('   const strategy = new MultiStrategy({ ...config });');
  console.log('   const signal = strategy.generateSignal(asset, priceData);');
}

// Run if this file is executed directly
if (require.main === module) {
  main();
}

module.exports = {
  exampleBasicSetup,
  exampleAggressiveConfig,
  exampleSignalGeneration,
  exampleMultipleAssets,
  exampleRiskManagement,
  exampleDetailedAnalysis,
  exampleRealTimeMonitoring
};
