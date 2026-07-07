"""
Risk Engine
Decomposes risk into distinct testable dimensions.
"""

from typing import Dict, Any
from datetime import datetime
from domain.models import EngineResult
from domain.engines.rule_parser import RuleParser


class RiskEngine:
    """Calculates risk across Business, Financial, Valuation, Market, and Liquidity dimensions."""
    
    def __init__(self, rule_parser: RuleParser):
        self.rule_parser = rule_parser

    def compute_risk(self, financial_result: EngineResult, valuation_result: EngineResult) -> EngineResult:
        """
        Calculates a dimensional risk score. Higher score = Higher Risk.
        """
        rules = self.rule_parser.get_rules("scoring")
        version = self.rule_parser.get_rule_version("scoring")
        
        dimensions = rules.get("risk_score", {}).get("dimensions", {})
        
        breakdown = {}
        reasons = []
        warnings = []
        total_risk = 0.0
        total_weight_scored = 0.0
        
        # Financial Risk
        f_metrics = financial_result.breakdown
        dte = f_metrics.get("debt_to_equity")
        financial_weight = dimensions.get("financial", 0.30)
        if dte is not None:
            # Simple linear risk translation for demo
            f_risk = min(dte * 100, 100)
            weighted_f_risk = f_risk * financial_weight
            breakdown["financial"] = weighted_f_risk
            total_risk += weighted_f_risk
            total_weight_scored += financial_weight
            reasons.append(f"Financial risk driven by D/E of {dte:.2f}")
        else:
            warnings.append("Missing D/E for Financial Risk.")

        # Valuation Risk
        v_metrics = valuation_result.breakdown
        mos = v_metrics.get("margin_of_safety")
        valuation_weight = dimensions.get("valuation", 0.20)
        if mos is not None:
            # Negative margin of safety = high risk
            if mos < 0:
                v_risk = 100
                reasons.append("High Valuation Risk: Margin of Safety is negative.")
            else:
                v_risk = 100 - (mos * 100 * 2) # e.g. 50% MoS = 0 risk
                v_risk = max(0, min(v_risk, 100))
                reasons.append(f"Valuation risk evaluated from {mos:.1%} MoS.")
                
            weighted_v_risk = v_risk * valuation_weight
            breakdown["valuation"] = weighted_v_risk
            total_risk += weighted_v_risk
            total_weight_scored += valuation_weight
        else:
            warnings.append("Missing MoS for Valuation Risk.")

        confidence = min(financial_result.confidence, valuation_result.confidence)
        final_risk = None
        if total_weight_scored > 0:
            # Prorate so partial dimension coverage doesn't silently cap the score low,
            # e.g. missing MoS shouldn't make a high-D/E company look artificially safe.
            final_risk = total_risk / total_weight_scored
            if total_weight_scored < 1.0:
                reasons.append(f"Risk score prorated. Only {total_weight_scored:.1%} of dimension weights were available.")
                confidence *= total_weight_scored
        else:
            warnings.append("No risk dimensions were scorable. Risk score is None.")
            confidence = 0.0

        return EngineResult(
            value=final_risk,
            confidence=confidence,
            breakdown=breakdown,
            reasons=reasons,
            method="Dimensional Risk Decomposition",
            rule_version=version,
            timestamp=datetime.now(),
            warnings=warnings
        )
