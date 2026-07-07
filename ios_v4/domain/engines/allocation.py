"""
Allocation Engine
Applies constraints and proportional sizing for v4.0.
"""

from typing import Dict, Any, List
from datetime import datetime
from domain.models import EngineResult


class AllocationEngine:
    """Calculates target portfolio allocations strictly respecting constraints."""
    
    def __init__(self, max_position_size: float = 0.10, cash_floor: float = 0.05, portfolio_size: float = 1000000.0):
        self.max_position_size = max_position_size
        self.cash_floor = cash_floor
        self.portfolio_size = portfolio_size
        
    def calculate_allocations(self, scoring_results: Dict[str, EngineResult], valuation_results: Dict[str, EngineResult] = None) -> Dict[str, EngineResult]:
        """
        Takes Business scores and Valuation results, returning target Allocations.
        v4.1 uses multiplicative allocation (Quality * Valuation Attractiveness * Confidence)
        subject to max_position_size constraints.
        """
        if valuation_results is None:
            valuation_results = {}
            
        allocations = {}
        
        # Only allocate to companies with a score > 0
        valid_tickers = {t: res for t, res in scoring_results.items() if res.value > 0}
        total_score = 0.0
        
        # First pass multiplicative weighting
        raw_weights = {}
        for t, res in valid_tickers.items():
            business_quality = res.value
            confidence = res.confidence
            
            # Valuation Attractiveness
            valuation_mult = 1.0
            if t in valuation_results:
                val_res = valuation_results[t]
                mos = val_res.breakdown.get("margin_of_safety")
                if mos is not None:
                    # e.g., 20% MoS = 1.2x weight. -20% MoS = 0.8x weight. Floor at 0.5x
                    valuation_mult = 1.0 + max(-0.5, mos)
                    
            weight = business_quality * valuation_mult * confidence
            raw_weights[t] = weight
            total_score += weight
            
        investable_capital = 1.0 - self.cash_floor
        
        if total_score == 0:
            return allocations # 100% Cash

        # Proportional to investable capital
        raw_allocs = {}
        for t, weight in raw_weights.items():
            raw_allocs[t] = (weight / total_score) * investable_capital
            
        # Apply constraints (Capping)
        capped_allocs = {}
        excess = 0.0
        
        for t, alloc in raw_allocs.items():
            if alloc > self.max_position_size:
                excess += (alloc - self.max_position_size)
                capped_allocs[t] = self.max_position_size
            else:
                capped_allocs[t] = alloc
                
        # Redistribute excess proportionally to non-capped positions
        # In a real optimizer, this loops until convergence. Here we'll do 1 iteration.
        non_capped = [t for t, a in capped_allocs.items() if a < self.max_position_size]
        if excess > 0 and non_capped:
            sub_total = sum(raw_weights[t] for t in non_capped)
            for t in non_capped:
                if sub_total > 0:
                    added = (raw_weights[t] / sub_total) * excess
                    capped_allocs[t] = min(capped_allocs[t] + added, self.max_position_size)
        
        for t, final_alloc in capped_allocs.items():
            reasons = [
                f"Multiplicative weighting (Quality, Valuation, Confidence).",
                f"Constrained by Max Size {self.max_position_size:.1%}" if final_alloc >= self.max_position_size else "Below max constraint limits."
            ]
            
            position_size = final_alloc * self.portfolio_size
            
            allocations[t] = EngineResult(
                value=final_alloc,
                confidence=valid_tickers[t].confidence,
                breakdown={
                    "target_allocation": final_alloc,
                    "position_size": position_size
                },
                reasons=reasons,
                method="Proportional Constrained (v4.0)",
                rule_version="alloc_v1",
                timestamp=datetime.now(),
                warnings=[]
            )
            
        return allocations
