"""
Trade Logger - บันทึกข้อมูลการเทรดตามรูปแบบ data_A.json

ฟังก์ชัน:
- คำนวณ Indicator ครบชุด (EMA, BB, RSI, MACD, Stochastic, ATR, Support/Resistance, Pivot)
- ใช้ MarketStateClassifier เพื่อจำแนกสภาวะตลาด
- บันทึกข้อมูลลงไฟล์ JSON ใน logs/logs_trade/
- รองรับหลาย Timeframe (M1, M5, M15)
"""

import os
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path

# Import MarketStateClassifier if available
try:
    from core.engines.market_state_classifier import MarketStateClassifier
except ImportError:
    MarketStateClassifier = None

# Import CandlePatternAnalyzer if available
try:
    from core.engines.candle_pattern_analyzer import CandlePatternAnalyzer
except ImportError:
    CandlePatternAnalyzer = None

logger = logging.getLogger("TradeLogger")


class TradeLogger:
    """
    บันทึกข้อมูลการเทรดลงไฟล์ตามรูปแบบ data_A.json
    """
    
    def __init__(self, logs_dir: str = "logs/logs_trade"):
        """
        Args:
            logs_dir: ไดเรกทอรีสำหรับบันทึกไฟล์ log
        """
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize MarketStateClassifier if available
        self.classifier = None
        if MarketStateClassifier is not None:
            try:
                self.classifier = MarketStateClassifier()
                logger.info("MarketStateClassifier initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize MarketStateClassifier: {e}")
                
        # Initialize CandlePatternAnalyzer if available
        self.pattern_analyzer = None
        if CandlePatternAnalyzer is not None:
            try:
                self.pattern_analyzer = CandlePatternAnalyzer()
                logger.info("CandlePatternAnalyzer initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize CandlePatternAnalyzer: {e}")
        
        # Cache for candle data to avoid repeated fetches
        self._cache = {}
    
    def build_log_data(self,
                       symbol: str,
                       candles_dict: Dict[str, pd.DataFrame],
                       primary_timeframe: str = 'M5',
                       ai_context: Optional[Any] = None) -> Dict[str, Any]:
        """
        สร้างโครงสร้างข้อมูลตามรูปแบบ ai data.txt (data_A.json)
        
        Args:
            symbol: คู่เงิน เช่น 'EURUSD'
            candles_dict: dict ของ {timeframe: DataFrame} มี timestamp index
            primary_timeframe: Timeframe หลัก (ใช้สำหรับคำนวณ indicators)
            ai_context: (optional) context จาก AI เพื่อเพิ่มข้อมูลเพิ่มเติม
        
        Returns:
            dict ที่มีโครงสร้างเหมือน ai data.txt
        """
        # เลือก DataFrame หลัก
        primary_df = candles_dict.get(primary_timeframe)
        if primary_df is None or primary_df.empty:
            logger.error(f"No data for primary timeframe {primary_timeframe}")
            return {}
        
        # ใช้ M1 สำหรับ candles รายละเอียด (ถ้ามี) หรือใช้ primary_df
        detail_df = candles_dict.get('M1')
        if detail_df is None or detail_df.empty:
            detail_df = primary_df
        
        # ดึงข้อมูลล่าสุด
        current_price = float(primary_df['close'].iloc[-1])
        timestamp = datetime.now(timezone.utc).isoformat(timespec='seconds')
        
        # คำนวณ Indicators สำหรับ primary (M5) และ detail (M1)
        indicators_primary = self._calculate_indicators(primary_df)
        if detail_df is not primary_df:
            indicators_detail = self._calculate_indicators(detail_df)
        else:
            indicators_detail = indicators_primary
        
        # จำแนกสภาวะตลาดโดยใช้ primary
        market_state = self._get_market_state(primary_df, indicators_primary, ai_context)
        
        # ดึง session
        session = self._detect_session()
        
        # แปลง primary_timeframe เป็น string เช่น "M5" -> "5m"
        tf_str = primary_timeframe.lower() if primary_timeframe.startswith('M') else primary_timeframe
        
        # สร้างโครงสร้างใหม่ (optimized for AI)
        log_data = {
            "timestamp": timestamp,
            "symbol": symbol,
            "current_price": current_price,
            "session": session,
            "timeframe": tf_str,
            "market_state": market_state.get('state', 'UNKNOWN'),
            "m5": indicators_primary,
            "m1": indicators_detail,
            "price_action": self._build_price_action(detail_df, indicators_primary),
            "triggered_signals": [],
            "signal_count": 0
        }
        
        return log_data
    
    def _calculate_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        คำนวณ Indicator ครบชุดจาก DataFrame
        
        Returns:
            dict ของ indicator values
        """
        close = df['close']
        high = df['high']
        low = df['low']
        
        # EMAs
        ema5 = close.ewm(span=5, adjust=False).mean()
        ema10 = close.ewm(span=10, adjust=False).mean()
        ema20 = close.ewm(span=20, adjust=False).mean()
        ema50 = close.ewm(span=50, adjust=False).mean()
        
        # Bollinger Bands (20, 2)
        ma20 = close.rolling(window=20).mean()
        std20 = close.rolling(window=20).std(ddof=0)
        bb_upper = ma20 + 2 * std20
        bb_lower = ma20 - 2 * std20
        
        # RSI (14)
        rsi14 = self._calculate_rsi(close, period=14)
        rsi7 = self._calculate_rsi(close, period=7)
        
        # MACD (12, 26, 9)
        macd_line, signal_line, _ = self._calculate_macd(close)
        
        # Stochastic (14, 3, 3)
        stoch_k, stoch_d = self._calculate_stochastic(high, low, close, k_period=14, d_period=3)
        
        # ATR (14)
        atr = self._calculate_atr(high, low, close, period=14)
        
        # Support/Resistance (local)
        lookback = 20
        local_support = low.iloc[-lookback:].min() if len(low) >= lookback else low.min()
        local_resistance = high.iloc[-lookback:].max() if len(high) >= lookback else high.max()
        
        # Pivot Points (classic)
        pivot = (high.iloc[-1] + low.iloc[-1] + close.iloc[-1]) / 3
        r1 = 2 * pivot - low.iloc[-1]
        s1 = 2 * pivot - high.iloc[-1]
        
        # สร้าง dict
        indicators = {
            "ema5": float(ema5.iloc[-1]) if not pd.isna(ema5.iloc[-1]) else 0.0,
            "ema10": float(ema10.iloc[-1]) if not pd.isna(ema10.iloc[-1]) else 0.0,
            "ema20": float(ema20.iloc[-1]) if not pd.isna(ema20.iloc[-1]) else 0.0,
            "ema50": float(ema50.iloc[-1]) if not pd.isna(ema50.iloc[-1]) else 0.0,
            "bb_upper": float(bb_upper.iloc[-1]) if not pd.isna(bb_upper.iloc[-1]) else 0.0,
            "bb_lower": float(bb_lower.iloc[-1]) if not pd.isna(bb_lower.iloc[-1]) else 0.0,
            "rsi7": float(rsi7.iloc[-1]) if not pd.isna(rsi7.iloc[-1]) else 50.0,
            "rsi14": float(rsi14.iloc[-1]) if not pd.isna(rsi14.iloc[-1]) else 50.0,
            "macd": float(macd_line.iloc[-1]) if not pd.isna(macd_line.iloc[-1]) else 0.0,
            "macd_signal": float(signal_line.iloc[-1]) if not pd.isna(signal_line.iloc[-1]) else 0.0,
            "stoch_k": float(stoch_k.iloc[-1]) if not pd.isna(stoch_k.iloc[-1]) else 50.0,
            "stoch_d": float(stoch_d.iloc[-1]) if not pd.isna(stoch_d.iloc[-1]) else 50.0,
            "support": float(local_support),
            "resistance": float(local_resistance),
            "pivot": float(pivot),
            "r1": float(r1),
            "s1": float(s1),
            "atr": float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else 0.0
        }
        
        # ปัดเศษทศนิยมให้เหลือ 5 ตำแหน่งเพื่อประหยัดพื้นที่และ Token AI
        return {k: round(v, 5) for k, v in indicators.items()}
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """คำนวณ RSI"""
        delta = prices.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, 1e-10)
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
        """คำนวณ MACD"""
        ema_fast = close.ewm(span=fast, adjust=False).mean()
        ema_slow = close.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    def _calculate_stochastic(self, high: pd.Series, low: pd.Series, close: pd.Series,
                             k_period: int = 14, d_period: int = 3) -> tuple:
        """คำนวณ Stochastic Oscillator"""
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        stoch_k = 100 * ((close - lowest_low) / (highest_high - lowest_low).replace(0, 1e-10))
        stoch_d = stoch_k.rolling(window=d_period).mean()
        return stoch_k, stoch_d
    
    def _calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """คำนวณ Average True Range"""
        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr
    
    def _get_market_state(self, df: pd.DataFrame, indicators: Dict[str, Any],
                          ai_context: Optional[Any] = None) -> Dict[str, Any]:
        """
        จำแนกสภาวะตลาด โดยใช้ MarketStateClassifier หรือ fallback
        """
        market_state = {
            'state': 'UNKNOWN',
            'trend_direction': 'NEUTRAL',
            'trend_type': 'neutral',
            'trend_strength': 0.0,
            'patterns': [],
            'atr_percentile': 50.0,
            'volatility_label': 'normal',
            'compression_quality': 0.0,
            'regime': 'ranging'
        }
        
        # ลองใช้ MarketStateClassifier ถ้ามี
        if self.classifier is not None:
            try:
                # เตรียม tier1 data (อย่างง่าย)
                close = df['close']
                high = df['high']
                low = df['low']
                
                ema20 = close.ewm(span=20, adjust=False).mean()
                ema50 = close.ewm(span=50, adjust=False).mean()
                direction = 'UP' if ema20.iloc[-1] > ema50.iloc[-1] else 'DOWN'
                
                # ATR percentile (โดยประมาณ)
                atr = self._calculate_atr(high, low, close, period=14)
                atr_percentile = 50.0  # default
                if len(atr) > 20:
                    atr_mean = float(max(atr.iloc[-20:].mean(), 1e-10))
                    atr_val = float(atr.iloc[-1])
                    if not pd.isna(atr_val) and not pd.isna(atr_mean):
                        atr_pct = (atr_val / atr_mean) * 100
                        atr_percentile = float(min(100, max(0, atr_pct)))
                
                # Trend strength (จาก RSI)
                rsi = self._calculate_rsi(close, period=14)
                rsi_val = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50.0
                strength = abs(rsi_val - 50.0) * 2  # ยิ่งใกล้ 50 ยิ่งต่ำ
                
                # Regime (จาก BB width)
                ma20 = close.rolling(window=20).mean()
                std20 = close.rolling(window=20).std(ddof=0)
                bb_width = (2 * std20) / ma20.replace(0, 1e-10)
                regime = 'ranging' if bb_width.iloc[-1] < 0.01 else 'trending'
                
                tier1 = {
                    'direction': direction,
                    'atr_percentile': atr_percentile,
                    'trend_strength': strength,
                    'strength': strength,
                    'type': 'trend' if regime == 'trending' else 'range',
                    'regime': regime.upper(),
                    'exhaustion_risk': 0.0,
                    'bos_detected': False
                }
                
                # เรียก classifier
                result = self.classifier.analyze(df, tier1=tier1)
                
                if isinstance(result, dict):
                    metrics = result.get('metrics', {})
                    
                    # Call pattern analyzer if available
                    patterns_list = []
                    if self.pattern_analyzer is not None:
                        pat_res = self.pattern_analyzer.analyze(df)
                        if isinstance(pat_res, dict):
                            patterns_list = pat_res.get('patterns_detected', [])
                            
                    # Calculate compression quality (100.0 if detected, else 0.0)
                    comp_quality = 100.0 if metrics.get('compression_detected', False) else 0.0
                    
                    # Determine regime
                    trend_dir = metrics.get('trend_direction', 'NONE')
                    regime_val = 'ranging' if trend_dir == 'NONE' else 'trending'
                    
                    market_state.update({
                        'state': result.get('state', 'UNKNOWN'),
                        'trend_direction': trend_dir,
                        'trend_type': metrics.get('trend_type', 'neutral'),
                        'trend_strength': metrics.get('trend_strength', 0.0),
                        'patterns': patterns_list,
                        'atr_percentile': metrics.get('atr_percentile', 50.0),
                        'volatility_label': metrics.get('volatility_regime', 'normal'),
                        'compression_quality': comp_quality,
                        'regime': regime_val
                    })
            except Exception as e:
                logger.warning(f"MarketStateClassifier failed, using fallback: {e}")
        
        # Fallback: ใช้ indicator อย่างง่าย
        if market_state['state'] == 'UNKNOWN':
            rsi_val = indicators.get('rsi14', 50.0)
            ema20_val = indicators.get('ema20', 0.0)
            ema50_val = indicators.get('ema50', 0.0)
            
            # สภาวะตลาด
            if rsi_val > 70:
                state = 'OVERBOUGHT'
            elif rsi_val < 30:
                state = 'OVERSOLD'
            elif ema20_val > ema50_val:
                state = 'UPTREND'
            elif ema20_val < ema50_val:
                state = 'DOWNTREND'
            else:
                state = 'RANGING'
            
            market_state['state'] = state
            market_state['trend_direction'] = 'UP' if ema20_val > ema50_val else 'DOWN'
            market_state['trend_strength'] = abs(rsi_val - 50.0) * 2  # 0-100
            market_state['regime'] = 'trending' if abs(ema20_val - ema50_val) / max(ema20_val, 1e-10) > 0.001 else 'ranging'
        
        return market_state
    
    def _build_price_action(self, df: pd.DataFrame, indicators: Dict[str, Any]) -> Dict[str, str]:
        """
        Pre-compute Price Action summary for AI consumption.
        Replaces raw candles with 9 meaningful fields.
        """
        if df.empty or len(df) < 20:
            return {
                "pattern": "NONE", "last_candle": "DOJI",
                "body_strength": "WEAK", "rejection_zone": "MID_RANGE",
                "wick_dominance": "LOW_WICK", "momentum_bias": "NEUTRAL",
                "move_quality": "STAGNANT", "trap_alert": "NONE",
                "sr_interaction": "MID_RANGE"
            }
        
        close = df['close']
        current_price = float(close.iloc[-1])
        last = df.iloc[-1]
        body = abs(last['close'] - last['open'])
        total_range = last['high'] - last['low']
        atr = max(indicators.get('atr', 0.0001), 0.0001)
        
        # 1. Pattern (from CandlePatternAnalyzer)
        pattern = "NONE"
        if self.pattern_analyzer is not None:
            try:
                pat_res = self.pattern_analyzer.analyze(df)
                if isinstance(pat_res, dict):
                    patterns = pat_res.get('patterns_detected', [])
                    pattern = patterns[0] if patterns else "NONE"
            except Exception:
                pass
        
        # 2. Last Candle
        if total_range > 0 and body / total_range < 0.1:
            last_candle = "DOJI"
        elif last['close'] > last['open']:
            last_candle = "BULLISH"
        else:
            last_candle = "BEARISH"
        
        # 3. Body Strength
        bodies = (df['close'].tail(10) - df['open'].tail(10)).abs()
        avg_body_pct = float(bodies.mean() / max(current_price, 1e-10) * 100)
        if avg_body_pct > 0.15:
            body_strength = "STRONG"
        elif avg_body_pct > 0.08:
            body_strength = "MODERATE"
        else:
            body_strength = "WEAK"
        
        # 4. Rejection Zone
        support = indicators.get('support', indicators.get('local_support', 0))
        resistance = indicators.get('resistance', indicators.get('local_resistance', 0))
        pivot_val = indicators.get('pivot', 0)
        
        dist_support = abs(current_price - support) / atr if atr > 0 else 999
        dist_resistance = abs(current_price - resistance) / atr if atr > 0 else 999
        dist_pivot = abs(current_price - pivot_val) / atr if atr > 0 else 999
        
        if dist_support < 1.0:
            rejection_zone = "NEAR_SUPPORT"
        elif dist_resistance < 1.0:
            rejection_zone = "NEAR_RESISTANCE"
        elif dist_pivot < 0.5:
            rejection_zone = "AT_PIVOT"
        else:
            rejection_zone = "MID_RANGE"
        
        # 5. Wick Dominance
        recent = df.tail(20)
        r_bodies = (recent['close'] - recent['open']).abs()
        r_ranges = recent['high'] - recent['low']
        r_wicks = r_ranges - r_bodies
        wick_ratio = float(r_wicks.sum() / max(r_bodies.sum(), 1e-10))
        if wick_ratio > 2.0:
            wick_dominance = "HIGH_WICK"
        elif wick_ratio > 1.0:
            wick_dominance = "MODERATE_WICK"
        else:
            wick_dominance = "LOW_WICK"
        
        # 6. Momentum Bias
        recent20 = df.tail(20)
        bullish_count = (recent20['close'] > recent20['open']).sum()
        bearish_count = (recent20['close'] < recent20['open']).sum()
        if bullish_count > bearish_count * 1.5:
            momentum_bias = "BULLISH"
        elif bearish_count > bullish_count * 1.5:
            momentum_bias = "BEARISH"
        else:
            momentum_bias = "NEUTRAL"
        
        # 7. Move Quality
        closes20 = close.tail(20)
        net_move = abs(float(closes20.iloc[-1]) - float(closes20.iloc[0]))
        path_length = float(closes20.diff().abs().sum())
        efficiency = net_move / max(path_length, 1e-10)
        if efficiency > 0.7:
            move_quality = "CLEAN_TRENDING"
        elif efficiency > 0.4:
            move_quality = "NORMAL"
        elif efficiency > 0.2:
            move_quality = "NOISY"
        else:
            move_quality = "CHAOTIC"
        
        # 8. Trap Alert
        trap_alert = "NONE"
        try:
            highs = df['high'].tail(20).values
            lows = df['low'].tail(20).values
            closes_arr = close.tail(20).values
            if len(highs) >= 20:
                prior_high = max(highs[:-3])
                prior_low = min(lows[:-3])
                if max(highs[-3:]) > prior_high and closes_arr[-1] < prior_high:
                    trap_alert = "BULL_TRAP"
                elif min(lows[-3:]) < prior_low and closes_arr[-1] > prior_low:
                    trap_alert = "BEAR_TRAP"
                elif total_range > 0 and body < total_range * 0.4 and total_range > atr * 2:
                    trap_alert = "STOP_HUNT"
        except Exception:
            pass
        
        # 9. S/R Interaction
        price_rising = last['close'] > last['open']
        if dist_support < 1.0 and price_rising:
            sr_interaction = "BOUNCING_OFF_SUPPORT"
        elif dist_resistance < 1.0 and not price_rising:
            sr_interaction = "BOUNCING_OFF_RESISTANCE"
        elif dist_resistance < 0.5 and price_rising:
            sr_interaction = "BREAKING_ABOVE_RESISTANCE"
        elif dist_support < 0.5 and not price_rising:
            sr_interaction = "BREAKING_BELOW_SUPPORT"
        elif dist_pivot < 0.5:
            sr_interaction = "TESTING_PIVOT"
        else:
            sr_interaction = "MID_RANGE"
        
        return {
            "pattern": pattern,
            "last_candle": last_candle,
            "body_strength": body_strength,
            "rejection_zone": rejection_zone,
            "wick_dominance": wick_dominance,
            "momentum_bias": momentum_bias,
            "move_quality": move_quality,
            "trap_alert": trap_alert,
            "sr_interaction": sr_interaction
        }
    
    def _build_candles_list(self, df: pd.DataFrame, count: int = 20) -> List[Dict[str, float]]:
        """
        สร้างรายการ OHLC candles จาก DataFrame
        """
        if df.empty:
            return []
        
        # เลือก count แท่งล่าสุด
        recent = df.iloc[-count:]
        candles = []
        for idx, row in recent.iterrows():
            candles.append({
                "open": round(float(row['open']), 6),
                "high": round(float(row['high']), 6),
                "low": round(float(row['low']), 6),
                "close": round(float(row['close']), 6)
            })
        return candles
    
    def _detect_session(self) -> str:
        """
        ตรวจจับช่วงเวลาการเทรด (session)
        """
        now = datetime.now(timezone.utc)
        hour = now.hour
        minute = now.minute
        
        # ใช้ UTC time
        if 0 <= hour < 8:
            return 'asian'
        elif 8 <= hour < 13:
            return 'london_open'
        elif 13 <= hour < 16:
            return 'london_ny_overlap'
        elif 16 <= hour < 20:
            return 'ny_open'
        else:
            return 'asian'
    
    def save_log(self, log_data: Dict[str, Any]) -> Optional[str]:
        """
        บันทึก log_data ลงไฟล์ JSON ใน logs/logs_trade/
        
        Returns:
            path ของไฟล์ที่บันทึก หรือ None ถ้าล้มเหลว
        """
        if not log_data:
            logger.error("No log data to save")
            return None
        
        symbol = log_data.get('symbol', 'UNKNOWN')
        timestamp = log_data.get('timestamp', datetime.now(timezone.utc).isoformat())
        
        # สร้างชื่อไฟล์: trade_log_YYYYMMDD_HHMMSS_symbol.json
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            filename = f"trade_log_{dt.strftime('%Y%m%d_%H%M%S')}_{symbol}.json"
        except:
            filename = f"trade_log_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{symbol}.json"
        
        filepath = self.logs_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Trade log saved: {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Failed to save trade log: {e}")
            return None
