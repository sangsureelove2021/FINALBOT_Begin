"""
Market Context
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Unified market data object consumed by all intelligence engines.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List
from datetime import datetime, timezone
import pandas as pd


@dataclass
class MarketContext:
    """Unified market context for all engines."""
    
    # Basic info
    symbol: str = ""
    timestamp: Optional[datetime] = None
    timeframe: str = "M5"
    candles: Dict = field(default_factory=dict)
    current_price: float = 0.0
    candle_index: int = 0
    
    # Tier 1: Trend & Structure
    trend: Dict = field(default_factory=dict)  # trend direction, strength
    mtf: Dict = field(default_factory=dict)  # multi-timeframe
    structure: Dict = field(default_factory=dict)  # support, resistance, peaks, troughs
    market_structure: Dict = field(default_factory=dict)  # Market Structure Engine (HH, HL, LL, LH)
    strength: Dict = field(default_factory=dict)  # trend strength metrics
    volatility: Dict = field(default_factory=dict)  # volatility metrics
    liquidity: Dict = field(default_factory=dict)  # liquidity metrics
    
    # Tier 2: Market State
    market_state: str = "UNKNOWN"
    market_volatility: float = 0.0
    noise_level: float = 0.0
    
    # Tier 3: Price Action
    price_action: Dict = field(default_factory=dict)
    
    # Tier 2 extras
    regime_quality: Dict = field(default_factory=dict)

    # Tier 3: Price Action extras
    candle_patterns: Dict = field(default_factory=dict)

    # Tier 4: Detection
    signal_conflict: float = 0.0
    compression: Dict = field(default_factory=dict)
    breakout: Dict = field(default_factory=dict)
    traps: Dict = field(default_factory=dict)        # trap/fakeout detection
    noise: Dict = field(default_factory=dict)        # noise detection
    divergence: Dict = field(default_factory=dict)   # divergence analysis
    anomaly: Dict = field(default_factory=dict)      # anomaly detection

    # Tier 5: Behavior
    transition: Dict = field(default_factory=dict)
    conflict: Dict = field(default_factory=dict)
    efficiency: Dict = field(default_factory=dict)
    persistence: Dict = field(default_factory=dict)
    continuation: Dict = field(default_factory=dict)
    orderflow: Dict = field(default_factory=dict)

    # Tier 5-8: Quality & Synthesis
    quality_score: float = 0.0
    synthesis: Dict = field(default_factory=dict)
    synthesized_context: Dict = field(default_factory=dict)
    move_probability: Dict = field(default_factory=dict)
    signal_quality: Dict = field(default_factory=dict)
    confidence_framework: Dict = field(default_factory=dict)
    explainability: Dict = field(default_factory=dict)
    
    # Scoring
    _scores: Dict = field(default_factory=dict)
    aggregated_score: float = 0.0
    strategy_recommendation: Dict = field(default_factory=dict)
    execution_decision: Dict = field(default_factory=dict)
    
    # Error tracking
    errors: List = field(default_factory=list)
    warnings: List = field(default_factory=list)
    engines_executed: List = field(default_factory=list)
    
    def set_score(self, key: str, value: float) -> None:
        """Set a score."""
        self._scores[key] = value
    
    def get_score(self, key: str) -> float:
        """Get a score."""
        return self._scores.get(key, 0.0)
    
    def has_errors(self) -> bool:
        """Check if context has errors."""
        return len(self.errors) > 0

    def mark_engine_executed(self, engine_name: str) -> None:
        """Record that an engine ran successfully."""
        if engine_name not in self.engines_executed:
            self.engines_executed.append(engine_name)
    
    def add_warning(self, msg: str) -> None:
        """Add a warning."""
        self.warnings.append(msg)
    
    def add_error(self, msg: str) -> None:
        """Add an error."""
        self.errors.append(msg)
    
    
    @classmethod
    def build_from_candles(cls, symbol: str, candles_dict: Dict[str, pd.DataFrame], 
                          engines: List = None, timeframe: str = "M5"):
        """Build MarketContext from multi-timeframe candle data."""
        ctx = cls()
        ctx.symbol = symbol
        ctx.candles = candles_dict
        
        primary_df = candles_dict.get(timeframe)
        if primary_df is None or primary_df.empty:
            ctx.timestamp = None
            ctx.current_price = 0.0
            return ctx
        
        # Convert pandas index (Timestamp) to datetime
        try:
            last_ts = primary_df.index[-1]
            if isinstance(last_ts, str):
                ctx.timestamp = pd.Timestamp(last_ts).to_pydatetime()
            else:
                ctx.timestamp = pd.Timestamp(last_ts).to_pydatetime()
        except Exception as e:
            ctx.timestamp = datetime.now(timezone.utc)
        
        ctx.current_price = float(primary_df['close'].iloc[-1])
        return ctx
