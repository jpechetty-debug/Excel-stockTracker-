"""
Allocation Engine
Applies constraints and proportional sizing for v4.0.
"""

from typing import Dict, Any, List
from datetime import datetime
from domain.models import EngineResult


class AllocationEngine:
    """Calculates target portfolio allocations strictly respecting constraints."""
    
    def __init__(self, max_position_size: float = 0.10, cash_floor: float = 0.05):
        self.max_position_size = max_position_size
        self.cash_floor = cash_floor
        
    def calculate_allocations(self, scoring_results: Dict[str, EngineResult]) -> Dict[str, EngineResult]:
        """
        Takes Business/Investment scores for multiple tickers and returns an Allocation target.
        v4.0 uses proportional allocation subject to max_position_size constraint.
        """
        allocations = {}
        total_score = 0.0
        
        # Only allocate to companies with a score > 0
        valid_tickers = {t: res for t, res in scoring_results.items() if res.value > 0}
        
        for t, res in valid_tickers.items():
            total_score += res.value
            
        investable_capital = 1.0 - self.cash_floor
        
        if total_score == 0:
            return allocations # 100% Cash

        # First pass proportional
        raw_allocs = {}
        for t, res in valid_tickers.items():
            raw_allocs[t] = (res.value / total_score) * investable_capital
            
        # Apply constraints (Capping)
        capped_allocs = {}
        excess = 0.0
        
        for t, alloc in raw_allocs.items():
            if alloc > self.max_position_size:
                excess += (alloc - self.max_position_size)
                capped_allocs[t] = self.max_position_size
            else:
                capped_allocs[t] = alloc
                
        # Redistribute excess proportionally to non-capped positions (simplified for v4.0)
        # In a real optimizer, this loops until convergence. Here we'll do 1 iteration.
        non_capped = [t for t, a in capped_allocs.items() if a < self.max_position_size]
        if excess > 0 and non_capped:
            sub_total = sum(valid_tickers[t].value for t in non_capped)
            for t in non_capped:
                added = (valid_tickers[t].value / sub_total) * excess
                capped_allocs[t] = min(capped_allocs[t] + added, self.max_position_size)
        
        for t, final_alloc in capped_allocs.items():
            reasons = [
                f"Proportional score raw target.",
                f"Constrained by Max Size {self.max_position_size:.1%}" if final_alloc >= self.max_position_size else "Below max constraint limits."
            ]
            
            allocations[t] = EngineResult(
                value=final_alloc,
                confidence=valid_tickers[t].confidence,
                breakdown={"target": final_alloc},
                reasons=reasons,
                method="Proportional Constrained (v4.0)",
                rule_version="alloc_v1",
                timestamp=datetime.now(),
                warnings=[]
            )
            
        return allocations
