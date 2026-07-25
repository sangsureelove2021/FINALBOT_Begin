"""
Anomaly Detection Module for FINALBOT

Provides real-time anomaly detection with CSV logging without
interrupting normal trading operations.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import logging
import os
from pathlib import Path

from config_setting.config_loader import load_datafeed_settings
from data_feed.csv_writer import get_file_lock

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    Detects anomalies in market data without stopping trading.
    Saves anomalies to CSV files for monitoring.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize with configuration."""
        if config is None:
            config = load_datafeed_settings()
        
        # Load anomaly detection configuration
        anomaly_config = config.get("data_feed", {}).get("anomaly_detector", {})
        
        # Health check thresholds
        self.health_check_config = {
            "response_time_warning": anomaly_config.get("response_time_warning", 7.0),
            "response_time_critical": anomaly_config.get("response_time_critical", 10.0),
            "connection_timeout": anomaly_config.get("connection_timeout", 15.0)
        }
        
        # Anomaly detection thresholds
        self.anomaly_config = {
            "spike_threshold": anomaly_config.get("spike_threshold", 0.3),  # 30% price change
            "zero_volume_threshold": anomaly_config.get("zero_volume_threshold", 0),
            "impossible_candle_threshold": anomaly_config.get("impossible_candle_threshold", 0.001),  # 0.1%
            "spike_window": anomaly_config.get("spike_window", 20),
            "max_consecutive_zero_volume": anomaly_config.get("max_consecutive_zero_volume", 3),
            "max_consecutive_anomalies": anomaly_config.get("max_consecutive_anomalies", 10)
        }
        
        # Initialize counters
        self.counters = {
            "total_calls": 0,
            "response_times": [],
            "spike_count": 0,
            "zero_volume_count": 0,
            "impossible_candle_count": 0,
            "consecutive_anomalies": 0
        }
        
        # CSV logging setup
        self.csv_config = config.get("data_feed", {}).get("csv_manager", {})
        self.csv_base_dir = Path(self.csv_config.get("base_dir", "data_base/csv/iq_option"))
        self.anomaly_dir = self.csv_base_dir / "anomaly_logs"
        self.anomaly_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"[ANOMALY] Initialized with thresholds: {self.anomaly_config}")
    
    def check_health(self, response_time: float, symbol: str) -> Dict[str, Any]:
        """
        Check API health metrics.
        
        Args:
            response_time: API response time in seconds
            symbol: Trading symbol
            
        Returns:
            Dict with health status and alerts
        """
        health_status = {
            "symbol": symbol,
            "response_time": response_time,
            "status": "NORMAL",
            "alerts": []
        }
        
        # Update counter
        self.counters["total_calls"] += 1
        self.counters["response_times"].append(response_time)
        
        # Check response time thresholds
        if response_time > self.health_check_config["response_time_critical"]:
            health_status["status"] = "CRITICAL"
            health_status["alerts"].append(f"CRITICAL: Response time {response_time:.2f}s > {self.health_check_config['response_time_critical']}s")
            logger.error(f"[ANOMALY] CRITICAL response time: {response_time:.2f}s for {symbol}")
        elif response_time > self.health_check_config["response_time_warning"]:
            health_status["status"] = "WARNING"
            health_status["alerts"].append(f"WARNING: Response time {response_time:.2f}s > {self.health_check_config['response_time_warning']}s")
            logger.warning(f"[ANOMALY] WARNING response time: {response_time:.2f}s for {symbol}")
        
        return health_status
    
    def detect_price_spikes(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """
        Detect price spikes in candle data.
        
        Args:
            df: DataFrame with OHLCV data
            symbol: Trading symbol
            
        Returns:
            DataFrame with anomaly flags
        """
        df = df.copy()
        
        # Calculate percentage changes
        df['price_change'] = df['close'].pct_change()
        
        # Calculate rolling volatility
        rolling_std = df['price_change'].rolling(window=self.anomaly_config["spike_window"]).std()
        
        # Detect spikes (price change > threshold * 3 standard deviations)
        df['spike_detected'] = (df['price_change'].abs() > 
                               self.anomaly_config["spike_threshold"] * 3)
        
        # Count spikes
        spike_count = df['spike_detected'].sum()
        if spike_count > 0:
            self.counters["spike_count"] += spike_count
            self.counters["consecutive_anomalies"] += spike_count
            
            spike_alerts = df[df['spike_detected']]
            for idx, spike in spike_alerts.iterrows():
                logger.warning(f"[ANOMALY] Price spike detected: {symbol} {idx} "
                             f"change: {spike['price_change']:.4f}")
            
            # Log to CSV
            self._log_anomalies(spike_alerts, symbol, "spike")
        
        return df
    
    def detect_zero_volume(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """
        Detect zero volume candles.
        
        Args:
            df: DataFrame with OHLCV data
            symbol: Trading symbol
            
        Returns:
            DataFrame with anomaly flags
        """
        df = df.copy()
        
        # Detect zero volume
        df['zero_volume_detected'] = df['volume'] <= self.anomaly_config["zero_volume_threshold"]
        
        # Count consecutive zero volumes
        df['zero_volume_streak'] = (df['zero_volume_detected'] == True).cumsum()
        df['zero_volume_streak'] = df['zero_volume_streak'].where(
            df['zero_volume_detected'], 0
        ).diff().where(lambda x: x == 1).cumsum().fillna(0).astype(int)
        
        # Count zero volumes
        zero_vol_count = df['zero_volume_detected'].sum()
        if zero_vol_count > 0:
            self.counters["zero_volume_count"] += zero_vol_count
            
            # Check for consecutive violations
            max_streak = df['zero_volume_streak'].max()
            if max_streak > self.anomaly_config["max_consecutive_zero_volume"]:
                logger.error(f"[ANOMALY] CONSECUTIVE zero volume: {symbol} streak {max_streak}")
            
            # Log to CSV
            zero_vol_alerts = df[df['zero_volume_detected']]
            self._log_anomalies(zero_vol_alerts, symbol, "zero_volume")
        
        return df
    
    def detect_impossible_candles(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """
        Detect impossible candles (violating OHLC constraints).
        
        Args:
            df: DataFrame with OHLCV data
            symbol: Trading symbol
            
        Returns:
            DataFrame with anomaly flags
        """
        df = df.copy()
        
        # Detect impossible candles
        impossible_conditions = [
            df['high'] < df['low'],      # High < Low
            df['high'] < df['open'],     # High < Open
            df['high'] < df['close'],    # High < Close
            df['low'] > df['open'],      # Low > Open
            df['low'] > df['close'],     # Low > Close
            df[['open', 'high', 'low', 'close']].lt(0).any(axis=1)  # Negative prices
        ]
        
        # Combine all impossible conditions
        df['impossible_candle_detected'] = impossible_conditions[0]
        for condition in impossible_conditions[1:]:
            df['impossible_candle_detected'] = df['impossible_candle_detected'] | condition
        
        # Count impossible candles
        impossible_count = df['impossible_candle_detected'].sum()
        if impossible_count > 0:
            self.counters["impossible_candle_count"] += impossible_count
            self.counters["consecutive_anomalies"] += impossible_count
            
            impossible_alerts = df[df['impossible_candle_detected']]
            for idx, impossible in impossible_alerts.iterrows():
                logger.error(f"[ANOMALY] Impossible candle detected: {symbol} {idx}")
                logger.error(f"[ANOMALY] OHLC: {impossible['open']:.6f}, {impossible['high']:.6f}, "
                           f"{impossible['low']:.6f}, {impossible['close']:.6f}")
            
            # Log to CSV
            self._log_anomalies(impossible_alerts, symbol, "impossible_candle")
        
        return df
    
    def detect_anomalies(self, df: pd.DataFrame, symbol: str, response_time: Optional[float] = None) -> pd.DataFrame:
        """
        Perform complete anomaly detection pipeline.
        
        Args:
            df: DataFrame with OHLCV data
            symbol: Trading symbol
            response_time: API response time for health check
            
        Returns:
            DataFrame with all anomaly flags
        """
        result_df = df.copy()
        
        # Health check if response time provided
        if response_time is not None:
            health_status = self.check_health(response_time, symbol)
            result_df['health_status'] = health_status['status']
        
        # Run all anomaly detectors
        result_df = self.detect_price_spikes(result_df, symbol)
        result_df = self.detect_zero_volume(result_df, symbol)
        result_df = self.detect_impossible_candles(result_df, symbol)
        
        # Combine all anomaly flags
        anomaly_columns = ['spike_detected', 'zero_volume_detected', 'impossible_candle_detected']
        existing_columns = [col for col in anomaly_columns if col in result_df.columns]
        if existing_columns:
            result_df['any_anomaly'] = result_df[existing_columns].any(axis=1)
            
            # Count total anomalies
            total_anomalies = result_df['any_anomaly'].sum()
            if total_anomalies > 0:
                logger.warning(f"[ANOMALY] Total anomalies detected: {symbol} {total_anomalies}")
                
                # Check for excessive anomalies
                if self.counters["consecutive_anomalies"] > self.anomaly_config["max_consecutive_anomalies"]:
                    logger.error(f"[ANOMALY] Excessive anomalies threshold exceeded: "
                               f"{self.counters['consecutive_anomalies']}")
            else:
                self.counters["consecutive_anomalies"] = 0
        
        return result_df
    
    def _log_anomalies(self, anomaly_df: pd.DataFrame, symbol: str, anomaly_type: str) -> None:
        """
        Log anomalies to CSV file.
        
        Args:
            anomaly_df: DataFrame with anomaly data
            symbol: Trading symbol
            anomaly_type: Type of anomaly (spike, zero_volume, impossible_candle)
        """
        try:
            # Create filename with date
            date_str = datetime.now().strftime("%Y_%m_%d")
            filename = f"{symbol}_{anomaly_type}_{date_str}.csv"
            filepath = self.anomaly_dir / filename
            
            # Add logging metadata
            log_df = anomaly_df.copy()
            log_df['anomaly_type'] = anomaly_type
            log_df['log_timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Save to CSV (append if file exists) with per-file thread lock
            file_lock = get_file_lock(str(filepath))
            with file_lock:
                if filepath.exists():
                    log_df.to_csv(filepath, mode='a', header=False, index=True)
                else:
                    log_df.to_csv(filepath, mode='w', header=True, index=True)
                
        except Exception as e:
            logger.error(f"[ANOMALY] Failed to log anomalies: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get anomaly detection statistics.
        
        Returns:
            Dict with statistics
        """
        stats = self.counters.copy()
        
        # Calculate response time statistics
        if stats["response_times"]:
            stats["avg_response_time"] = np.mean(stats["response_times"])
            stats["max_response_time"] = np.max(stats["response_times"])
            stats["min_response_time"] = np.min(stats["response_times"])
        
        return stats
    
    def reset_counters(self) -> None:
        """Reset anomaly counters (for daily reset)."""
        logger.info("[ANOMALY] Resetting anomaly counters")
        self.counters = {
            "total_calls": 0,
            "response_times": [],
            "spike_count": 0,
            "zero_volume_count": 0,
            "impossible_candle_count": 0,
            "consecutive_anomalies": 0
        }