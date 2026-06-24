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

# Removed engine imports to enforce decoupling

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
        
        # TODO: Accept indicators from Orchestrator in the future
        payload = {}
        indicators_primary = {}
        indicators_detail = {}
        
        # ดึง session
        session = self._detect_session()
        
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

        # ── price_action ───────────────────────────────────────────────
        # TODO: Wait for proper injection of price_action
        price_action = payload.get('price_action', {})

        # ── สร้าง log_data ───────────────────────────────────────────────
        log_data = {
            "timestamp":     timestamp,
            "symbol":        symbol,
            "current_price": current_price,
            "session":       session,
            "market_state":  market_state.get('state', 'UNKNOWN'),
            "tradeable":     market_state.get('tradeable', False),
            "quality_score": market_state.get('quality_score', 0),
            "confidence":    market_state.get('confidence', 0),
            "stability":     market_state.get('stability', 0),
            "description":   market_state.get('description', ''),
            "m15_bias":      payload.get('m15', {}).get('bias', 'NEUTRAL'),
            "m5":            m5_block,
            "m1":            m1_block,
            "price_action":  price_action,
            "analysis":      analysis_block,
            "triggered_signals": [],
            "signal_count":  0,
        }

        return log_data
    

    
    # _build_price_action removed to prevent raw data calculation in logger
    
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
