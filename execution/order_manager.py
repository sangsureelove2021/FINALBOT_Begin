"""
Order Manager
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Manage active orders, track P&L, handle results.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Trade:
    """Represents a single trade."""
    order_id: str
    symbol: str
    direction: str  # 'CALL' or 'PUT'
    amount: float
    entry_price: float
    entry_time: datetime
    expiry: str  # 'M1', 'M5', etc.
    status: str  # 'pending', 'closed', 'error'
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    pnl: float = 0.0  # Profit/Loss in THB
    pnl_percent: float = 0.0
    notes: str = ""


class OrderManager:
    """
    Manage all active and closed trades.
    
    Responsibilities:
    - Track open positions
    - Record closures and P&L
    - Generate daily/weekly reports
    - Enforce rules (max concurrent, etc.)
    """
    
    def __init__(self, max_concurrent: int = 5):
        """
        Initialize manager.
        
        Args:
            max_concurrent: Max open trades at once
        """
        self.max_concurrent = max_concurrent
        self.active_trades: Dict[str, Trade] = {}  # {order_id: Trade}
        self.closed_trades: List[Trade] = []
        self.session_start = datetime.utcnow()
    
    def add_trade(self, order_id: str, symbol: str, direction: str,
                  amount: float, entry_price: float, 
                  expiry: str = 'M5') -> bool:
        """
        Register a new trade.
        
        Args:
            order_id: Unique order identifier
            symbol: Trading pair
            direction: 'CALL' or 'PUT'
            amount: Trade size
            entry_price: Entry price
            expiry: Expiration timeframe
        
        Returns:
            True if added, False if would exceed limit
        """
        if len(self.active_trades) >= self.max_concurrent:
            logger.warning(f"⚠️ Cannot add trade: max concurrent ({self.max_concurrent}) reached")
            return False
        
        if order_id in self.active_trades:
            logger.warning(f"⚠️ Trade {order_id} already exists")
            return False
        
        trade = Trade(
            order_id=order_id,
            symbol=symbol,
            direction=direction,
            amount=amount,
            entry_price=entry_price,
            entry_time=datetime.utcnow(),
            expiry=expiry,
            status='pending'
        )
        
        self.active_trades[order_id] = trade
        logger.info(f"📊 Trade opened: {order_id} | {direction} {amount:.0f}x {symbol} @ {entry_price}")
        return True
    
    def close_trade(self, order_id: str, exit_price: float, 
                   pnl: float = 0.0, notes: str = "") -> Optional[Trade]:
        """
        Close a trade and calculate P&L.
        
        Args:
            order_id: Order to close
            exit_price: Price at exit
            pnl: Profit/Loss (THB)
            notes: Reason for closing
        
        Returns:
            Closed Trade object or None if not found
        """
        if order_id not in self.active_trades:
            logger.warning(f"❌ Trade {order_id} not found")
            return None
        
        trade = self.active_trades[order_id]
        trade.exit_price = exit_price
        trade.exit_time = datetime.utcnow()
        trade.pnl = pnl
        trade.status = 'closed'
        trade.notes = notes
        
        # Calculate P&L percentage
        if trade.entry_price != 0:
            if trade.direction == 'CALL':
                trade.pnl_percent = ((exit_price - trade.entry_price) / trade.entry_price) * 100
            else:  # PUT
                trade.pnl_percent = ((trade.entry_price - exit_price) / trade.entry_price) * 100
        
        # Move to closed
        del self.active_trades[order_id]
        self.closed_trades.append(trade)
        
        status_icon = "✅ WIN" if pnl > 0 else "❌ LOSS"
        logger.info(f"{status_icon}: {order_id} | {trade.symbol} | P&L: {pnl:.2f} THB ({trade.pnl_percent:+.2f}%)")
        
        return trade
    
    def get_active_trades(self, symbol: Optional[str] = None) -> List[Trade]:
        """Get list of active trades."""
        trades = list(self.active_trades.values())
        if symbol:
            trades = [t for t in trades if t.symbol == symbol]
        return trades
    
    def get_closed_trades(self, symbol: Optional[str] = None) -> List[Trade]:
        """Get list of closed trades."""
        trades = self.closed_trades.copy()
        if symbol:
            trades = [t for t in trades if t.symbol == symbol]
        return trades
    
    def get_stats(self) -> Dict:
        """Get session statistics."""
        if not self.closed_trades:
            return {
                'total_trades': 0,
                'wins': 0,
                'losses': 0,
                'win_rate': 0.0,
                'total_pnl': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'largest_win': 0.0,
                'largest_loss': 0.0,
                'active_trades': len(self.active_trades),
            }
        
        wins = [t.pnl for t in self.closed_trades if t.pnl > 0]
        losses = [t.pnl for t in self.closed_trades if t.pnl <= 0]
        
        return {
            'total_trades': len(self.closed_trades),
            'active_trades': len(self.active_trades),
            'wins': len(wins),
            'losses': len(losses),
            'win_rate': (len(wins) / len(self.closed_trades) * 100) if self.closed_trades else 0.0,
            'total_pnl': sum(t.pnl for t in self.closed_trades),
            'avg_win': sum(wins) / len(wins) if wins else 0.0,
            'avg_loss': sum(losses) / len(losses) if losses else 0.0,
            'largest_win': max(wins) if wins else 0.0,
            'largest_loss': min(losses) if losses else 0.0,
            'session_duration': str(datetime.utcnow() - self.session_start),
        }
    
    def print_summary(self) -> None:
        """Print session summary."""
        stats = self.get_stats()
        logger.info("\n" + "="*60)
        logger.info("📊 SESSION SUMMARY")
        logger.info("="*60)
        logger.info(f"Total Trades: {stats['total_trades']}")
        logger.info(f"Active Trades: {stats['active_trades']}")
        logger.info(f"Wins: {stats['wins']} | Losses: {stats['losses']} | Win Rate: {stats['win_rate']:.1f}%")
        logger.info(f"Total P&L: {stats['total_pnl']:+.2f} THB")
        logger.info(f"Avg Win: {stats['avg_win']:+.2f} | Avg Loss: {stats['avg_loss']:+.2f}")
        logger.info(f"Largest Win: {stats['largest_win']:+.2f} | Largest Loss: {stats['largest_loss']:+.2f}")
        logger.info(f"Session Duration: {stats['session_duration']}")
        logger.info("="*60 + "\n")
