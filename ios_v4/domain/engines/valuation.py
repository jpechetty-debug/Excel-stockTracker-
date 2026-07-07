"""
Valuation Calculation Engine
Produces objective pricing facts (DCF, Graham, Margin of Safety).
Strictly decoupled from Business Scoring.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from domain.models import EngineResult


class ValuationEngine:
    """Calculates objective intrinsic values."""

    @staticmethod
    def _safe_divide(num: float, den: float) -> Optional[float]:
        if den is None or num is None or den == 0:
            return None
        return num / den

    def calculate_dcf(self, fcf: float, growth_rate: float, discount_rate: float, shares: float) -> Optional[float]:
        """Extremely simplified 5-year DCF for foundation."""
        if None in (fcf, growth_rate, discount_rate, shares) or shares == 0:
            return None
        
        # Simplified Terminal Value math
        value = 0
        current_fcf = fcf
        for i in range(1, 6):
            current_fcf *= (1 + growth_rate)
            value += current_fcf / ((1 + discount_rate) ** i)
            
        terminal_value = (current_fcf * (1 + 0.02)) / (discount_rate - 0.02)
        value += terminal_value / ((1 + discount_rate) ** 5)
        
        return value / shares

    def calculate_graham(self, eps: float, bvps: float) -> Optional[float]:
        """Graham Number: sqrt(22.5 * EPS * BVPS)"""
        if None in (eps, bvps) or eps <= 0 or bvps <= 0:
            return None
        return (22.5 * eps * bvps) ** 0.5

    def calculate_valuation(self, data: Dict[str, Any], current_price: float) -> EngineResult:
        """
        Takes financial facts and calculates a multi-model intrinsic value.
        """
        breakdown = {}
        reasons = []
        warnings = []
        
        eps = data.get("eps")
        bvps = data.get("bvps")
        fcf = data.get("fcf")
        shares = data.get("shares_outstanding")
        
        # 1. DCF
        # Hardcoding assumptions for Phase 3 scaffolding
        dcf_val = self.calculate_dcf(fcf, 0.10, 0.10, shares)
        if dcf_val:
            breakdown["dcf_value"] = dcf_val
            reasons.append(f"DCF Value computed at {dcf_val:.2f} (Assumptions: 10% discount, 10% growth)")
        else:
            warnings.append("Insufficient data for DCF valuation.")

        # 2. Graham Value
        graham_val = self.calculate_graham(eps, bvps)
        if graham_val:
            breakdown["graham_value"] = graham_val
            reasons.append(f"Graham Value computed at {graham_val:.2f}")

        # 3. Blended Intrinsic Value
        # Using simple equal weights for available models
        available_models = [v for k, v in breakdown.items() if "value" in k]
        if available_models:
            blended_value = sum(available_models) / len(available_models)
            reasons.append(f"Blended intrinsic value computed as {blended_value:.2f} using {len(available_models)} models.")
            
            # 4. Margin of Safety
            if current_price and current_price > 0:
                mos = (blended_value - current_price) / blended_value
                breakdown["margin_of_safety"] = mos
                reasons.append(f"Margin of Safety computed at {mos:.1%}")
        else:
            blended_value = 0.0
            warnings.append("No valuation models could be calculated.")

        confidence = len(available_models) / 3.0 # Assuming 3 models max
        
        return EngineResult(
            value=blended_value,
            confidence=min(confidence, 1.0),
            breakdown=breakdown,
            reasons=reasons,
            method="Multi-Model Blended",
            rule_version="val_v1",
            timestamp=datetime.now(),
            warnings=warnings
        )
