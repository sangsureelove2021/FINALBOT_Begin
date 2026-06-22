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
    
    def __init__(self, logs_dir: str = "logs/logs_ai"):
        """
        Args:
            logs_dir: ไดเรกทอรีสำหรับบันทึกไฟล์ log
        """
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache for candle data to avoid repeated fetches
        self._cache = {}
        
        # Initialize CandlePatternAnalyzer if available
        self.pattern_analyzer = None
        if CandlePatternAnalyzer is not None:
            try:
                self.pattern_analyzer = CandlePatternAnalyzer()
            except Exception as e:
                logger.warning(f"Failed to initialize CandlePatternAnalyzer: {e}")
    
    def build_log_data(self,
                       symbol: str,
                       candles_dict: Dict[str, pd.DataFrame],
                       market_state: Dict[str, Any],
                       primary_timeframe: str = 'M5',
                       ai_context: Optional[Any] = None) -> Dict[str, Any]:
        """
        สร้างโครงสร้างข้อมูลตามรูปแบบ ai data.txt (data_A.json)
        
        Args:
            symbol: คู่เงิน เช่น 'EURUSD'
            candles_dict: dict ของ {timeframe: DataFrame} มี timestamp index
            market_state: ข้อมูลสภาวะตลาดที่รับมาจาก Orchestrator
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
        
        # ดึง Indicators สำเร็จรูปจาก IndicatorStore
        from core.indicator_store import store
        payload = store.get_payload(symbol)
        indicators_primary = payload.get('m5', {})
        indicators_detail = payload.get('m1', {})
        
        # ดึง session
        session = self._detect_session()
        
        # แปลง primary_timeframe เป็น string เช่น "M5" -> "5m"
        tf_str = primary_timeframe.lower() if primary_timeframe.startswith('M') else primary_timeframe
        
        # ── M5 block ────────────────────────────────────────────────────
        m5_block = {
            "ema5":       indicators_primary.get('ema5',  0.0),
            "ema10":      indicators_primary.get('ema10', 0.0),
            "ema20":      indicators_primary.get('ema20', 0.0),
            "ema50":      indicators_primary.get('ema50', 0.0),
            "bb_upper":   indicators_primary.get('bb_upper', 0.0),
            "bb_lower":   indicators_primary.get('bb_lower', 0.0),
            "bb_width":   indicators_primary.get('bb_width', 0.0),
            "rsi14":      indicators_primary.get('rsi14', 50.0),
            "macd":       indicators_primary.get('macd', 0.0),
            "macd_signal":indicators_primary.get('macd_signal', 0.0),
            "macd_hist":  indicators_primary.get('macd_hist', 0.0),
            "stoch_k":    indicators_primary.get('stoch_k', 50.0),
            "stoch_d":    indicators_primary.get('stoch_d', 50.0),
            "adx":        indicators_primary.get('adx', 0.0),
            "atr":        indicators_primary.get('atr14', indicators_primary.get('atr', 0.0)),
            "support":    indicators_primary.get('support', 0.0),
            "resistance": indicators_primary.get('resistance', 0.0),
            "pivot":      indicators_primary.get('pivot', 0.0),
            "r1":         indicators_primary.get('r1', 0.0),
            "s1":         indicators_primary.get('s1', 0.0),
        }

        # ── M1 block ────────────────────────────────────────────────────
        m1_block = {
            "ema5":        indicators_detail.get('ema5', 0.0),
            "ema20":       indicators_detail.get('ema20', 0.0),
            "rsi14":       indicators_detail.get('rsi14', 50.0),
            "macd":        indicators_detail.get('macd', 0.0),
            "macd_signal": indicators_detail.get('macd_signal', 0.0),
            "stoch_k":     indicators_detail.get('stoch_k', 50.0),
            "stoch_d":     indicators_detail.get('stoch_d', 50.0),
            "last_candle": indicators_detail.get('last_candle', 'NEUTRAL'),
        }

        # ── analysis block — ดึงจาก market_state (output ของ 5 engines) ─
        analysis_block = {
            "trend_direction":   market_state.get('trend_direction',   'NONE'),
            "trend_type":        market_state.get('trend_type',        'CHOPPY'),
            "trend_strength":    market_state.get('trend_strength',    0),
            "volatility_regime": market_state.get('volatility_label',  'NORMAL').upper(),
            "compression_quality": market_state.get('compression_quality', 0.0),
            "bos_detected":      market_state.get('bos_detected',      False),
            "mtf_alignment":     market_state.get('mtf_alignment',     50),
            "exhaustion_risk":   market_state.get('exhaustion_risk',   50),
        }

        # ── price_action — ดึงจาก IndicatorStore (คำนวณไว้แล้ว) ────────
        price_action = payload.get('price_action') or \
                       self._build_price_action(detail_df, indicators_primary)

        # ── สร้าง log_data ───────────────────────────────────────────────
        log_data = {
            "timestamp":    timestamp,
            "symbol":       symbol,
            "current_price": current_price,
            "session":      session,
            "market_state": market_state.get('state', 'UNKNOWN'),
            "m15_bias":     payload.get('m15', {}).get('bias', 'NEUTRAL'),
            "m5":           m5_block,
            "m1":           m1_block,
            "price_action": price_action,
            "analysis":     analysis_block,
            "triggered_signals": [],
            "signal_count": 0,
        }

        return log_data
    

    
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
        atr = max(indicators.get('atr14', indicators.get('atr', 0.0001)), 0.0001)
        
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
