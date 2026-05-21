"""
Portfolio Balancer
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Multi-symbol risk distribution and correlation analysis.
"""

import logging
from typing import Dict, List, Optional
import numpy as np

logger = logging.getLogger(__name__)


class PortfolioBalancer:
    """
    Manage risk distribution across multiple symbols.
    """
    
    def __init__(self, symbols: List[str], total_capital: float = 2000):
        """Initialize balancer."""
        self.symbols = symbols
        self.total_capital = total_capital
        self.symbol_weights = {s: 1.0 / len(symbols) for s in symbols}
        self.correlation_matrix = {}
        self.max_correlation = 0.7
    
    def update_correlation_matrix(self, returns_data: Dict[str, List[float]]):
        """Update symbol correlations from price returns."""
        try:
            if len(returns_data) < 2:
                return
            
            symbols_list = list(returns_data.keys())
            n = len(symbols_list)
            
            # Calculate correlation matrix
            corr_matrix = np.zeros((n, n))
            
            for i, sym1 in enumerate(symbols_list):
                for j, sym2 in enumerate(symbols_list):
                    if i == j:
                        corr_matrix[i][j] = 1.0
                    else:
                        r1 = np.array(returns_data[sym1])
                        r2 = np.array(returns_data[sym2])
                        
                        if len(r1) > 0 and len(r2) > 0:
                            corr = np.corrcoef(r1, r2)[0, 1]
                            corr_matrix[i][j] = max(-1, min(1, corr))
            
            # Store correlation
            self.correlation_matrix = {
                symbols_list[i]: {
                    symbols_list[j]: corr_matrix[i][j]
                    for j in range(n)
                }
                for i in range(n)
            }
            
            logger.info(f"✅ Correlation matrix updated for {n} symbols")
            
        except Exception as e:
            logger.error(f"❌ Correlation update failed: {e}")
    
    def rebalance_weights(self) -> Dict[str, float]:
        """Rebalance symbol weights based on correlation."""
        try:
            if not self.correlation_matrix:
                return self.symbol_weights
            
            # Penalize highly correlated pairs
            adjusted_weights = {s: 1.0 for s in self.symbols}
            
            for sym1 in self.symbols:
                penalty = 0
                for sym2 in self.symbols:
                    if sym1 != sym2:
                        corr = self.correlation_matrix.get(sym1, {}).get(sym2, 0)
                        if abs(corr) > self.max_correlation:
                            penalty += abs(corr) / self.max_correlation
                
                adjusted_weights[sym1] = max(0.5, 1.0 - penalty * 0.1)
            
            # Normalize to sum = 1
            total = sum(adjusted_weights.values())
            self.symbol_weights = {s: w / total for s, w in adjusted_weights.items()}
            
            logger.info(f"✅ Portfolio rebalanced: {self.symbol_weights}")
            return self.symbol_weights
            
        except Exception as e:
            logger.error(f"❌ Rebalancing failed: {e}")
            return self.symbol_weights
    
    def get_capital_allocation(self, symbol: str) -> float:
        """Get capital for symbol."""
        weight = self.symbol_weights.get(symbol, 1.0 / len(self.symbols))
        return self.total_capital * weight
    
    def get_risk_distribution(self) -> Dict[str, float]:
        """Get current risk distribution."""
        return {
            symbol: allocation / self.total_capital * 100
            for symbol, allocation in {
                s: self.get_capital_allocation(s) for s in self.symbols
            }.items()
        }
