"""
Score Aggregator
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Aggregates multiple scores into a single final score using weights.
"""

from typing import Dict, List, Optional
from core.models.score import Score, ScoreSet


class ScoreAggregator:
    """Aggregates multiple scores using weighted average"""
    
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        Args:
            weights: Dict of {score_name: weight}
        """
        self.default_weights = weights or {}
    
    def aggregate(self, scores: Dict[str, Score], 
                 weights: Optional[Dict[str, float]] = None) -> float:
        """
        Compute weighted average of scores.
        
        Args:
            scores: Dict of {name: Score}
            weights: Optional override weights
        
        Returns:
            Aggregated score 0-100
        """
        if not scores:
            return 0.0
        
        active_weights = weights if weights is not None else self.default_weights
        
        total_weighted = 0.0
        total_weight = 0.0
        
        for name, score in scores.items():
            # Use score's own weight, or override from active_weights, or 1.0
            w = active_weights.get(name, score.weight if score else 1.0)
            
            if score and w > 0:
                total_weighted += score.value * w
                total_weight += w
        
        if total_weight == 0:
            return 0.0
        
        return float(total_weighted / total_weight)
    
    def aggregate_with_penalty(self, scores: Dict[str, Score],
                              penalties: Dict[str, float]) -> float:
        """
        Aggregate scores then apply penalties.
        
        Args:
            scores: Score dict
            penalties: Dict of {name: penalty_amount}
        
        Returns:
            Final score after penalties (0-100)
        """
        base = self.aggregate(scores)
        
        total_penalty = sum(penalties.values())
        final = base - total_penalty
        
        return max(0.0, min(100.0, final))
    
    def create_score_set(self, scores: Dict[str, Score]) -> ScoreSet:
        """Create a ScoreSet from dict of scores"""
        aggregated = self.aggregate(scores)
        total_weight = sum(s.weight for s in scores.values())
        
        return ScoreSet(
            scores=scores,
            aggregated=aggregated,
            total_weight=total_weight,
        )
