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
        # REMOVED as a Risk Score dimension (was previously weighted 40% per
        # scoring.yaml). InvestmentEngine already applies a valuation_mult derived
        # from this exact margin_of_safety figure. Keeping it here too meant every
        # stock's valuation was penalized twice in the same final Investment Score
        # - once directly, once via an inflated Risk Score - which is what drove
        # almost the entire universe into "Avoid" regardless of quality.
        #
        # A softer/continuous curve here does NOT fix this: real DCF-based MoS
        # values for expensive quality names (e.g. CAMS at -166%, Cummins at
        # -487%) still saturate any reasonable risk curve at its max, so the
        # double-count persists no matter the curve shape. Risk Score should
        # measure risk orthogonal to "is it expensive right now" - financial
        # risk here, and ideally business/liquidity/market risk dimensions if
        # you add them later. If you want valuation reflected in Risk Score too,
        # dial back valuation_mult in investment.py instead of double-applying
        # the same signal here.
        v_metrics = valuation_result.breakdown
        mos = v_metrics.get("margin_of_safety")
        if mos is None:
            warnings.append("Missing MoS (valuation dimension intentionally excluded from Risk Score - see investment.py valuation_mult).")

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
