"""
Investment Engine
Produces the final Investment Score by combining Quality, Value, and Risk.
"""

from typing import Dict, Any
from datetime import datetime
from domain.models import EngineResult


class InvestmentEngine:
    """Calculates Investment Score from Business, Valuation, and Risk results."""
    
    def compute_investment_score(self, business_result: EngineResult, valuation_result: EngineResult, risk_result: EngineResult) -> EngineResult:
        breakdown = {}
        reasons = []
        warnings = []
        
        # 1. Quality (Business Score)
        quality = business_result.value if (business_result and business_result.value is not None) else 0.0
        if business_result and business_result.value is None:
            warnings.append("Business Score was None (no scorable metrics); treating Quality as 0.0 for this synthesis.")
        breakdown["quality"] = quality
        
        # 2. Value (Valuation Attractiveness)
        # Higher margin of safety = better value
        # A margin of safety of 0% means fairly valued (1.0x). 
        # MoS of 20% means attractive (1.2x).
        valuation_mult = 1.0
        if valuation_result:
            mos = valuation_result.breakdown.get("margin_of_safety")
            if mos is not None:
                valuation_mult = 1.0 + max(-0.5, mos)
                
        breakdown["valuation_mult"] = valuation_mult
        
        # 3. Risk Adjustment (Risk Score)
        # Risk score is 0 to 100, where higher is more risk.
        # So risk_adjustment scales from 1.0 (no risk) to 0.0 (max risk).
        risk = risk_result.value if (risk_result and risk_result.value is not None) else 0.0
        if risk_result and risk_result.value is None:
            warnings.append("Risk Score was None (no scorable dimensions); treating Risk as 0.0 (no adjustment) for this synthesis.")
        risk_adj = max(0.0, 1.0 - (risk / 100.0))
        breakdown["risk_adj"] = risk_adj
        
        # Overall Confidence
        confidence = 1.0
        if business_result: confidence = min(confidence, business_result.confidence)
        if valuation_result: confidence = min(confidence, valuation_result.confidence)
        if risk_result: confidence = min(confidence, risk_result.confidence)
        
        # Calculate final score
        # Base score is Quality, scaled by Value and Risk Adjustment
        investment_score = quality * valuation_mult * risk_adj
        
        # Quality Gate: average/poor business quality caps the max Investment Score
        if quality < 50.0:
            if investment_score > 35.0:
                investment_score = 35.0
                reasons.append("Investment Score capped at 35.0 due to Quality Gate (Business Score < 50)")
        elif quality < 60.0:
            if investment_score > 50.0:
                investment_score = 50.0
                reasons.append("Investment Score capped at 50.0 due to Quality Gate (Business Score < 60)")
                
        # Cap at 100 to maintain 0-100 range
        investment_score = min(100.0, max(0.0, investment_score))
        
        reasons.append(f"Quality (Business Score): {quality:.1f}")
        reasons.append(f"Value Multiplier (from MoS): {valuation_mult:.2f}x")
        reasons.append(f"Risk Adjustment: {risk_adj:.2f}x")
        
        # Generate Overall Recommendation
        if investment_score >= 80 and confidence >= 0.8:
            recommendation = "Strong Buy"
        elif investment_score >= 65:
            recommendation = "Buy"
        elif investment_score >= 50:
            recommendation = "Watch"
        elif investment_score >= 35:
            recommendation = "Hold"
        else:
            recommendation = "Avoid"
            
        # Downgrade if confidence is extremely low
        if confidence < 0.5 and recommendation in ["Strong Buy", "Buy"]:
            recommendation = "Watch"
            reasons.append("Recommendation downgraded to Watch due to low confidence.")
            
        breakdown["recommendation"] = recommendation
        reasons.append(f"Overall Recommendation: {recommendation}")
        
        return EngineResult(
            value=investment_score,
            confidence=confidence,
            breakdown=breakdown,
            reasons=reasons,
            method="Orthogonal Synthesis (Quality * Value * Risk)",
            rule_version="inv_v1",
            timestamp=datetime.now(),
            warnings=warnings
        )
