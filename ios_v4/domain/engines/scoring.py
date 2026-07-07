"""
Scoring Engine
Decision Engine that interprets Financial Facts into Business Scores based on YAML rules.
"""

from typing import Dict, Any
from datetime import datetime
from domain.models import EngineResult
from domain.engines.rule_parser import RuleParser


class ScoringEngine:
    """Applies configurable investment policies to objective financial metrics."""

    def __init__(self, rule_parser: RuleParser):
        self.rule_parser = rule_parser

    def compute_business_score(self, financial_result: EngineResult) -> EngineResult:
        """
        Interprets FinancialEngine metrics using rules/scoring.yaml.
        """
        rules = self.rule_parser.get_rules("scoring")
        version = self.rule_parser.get_rule_version("scoring")
        
        b_rules = rules.get("business_score", {})
        weights = b_rules.get("weights", {})
        thresholds = b_rules.get("thresholds", {})
        
        metrics = financial_result.breakdown
        
        score = 0.0
        total_weight_scored = 0.0
        breakdown = {}
        reasons = []
        warnings = []
        
        # 1. ROCE Scoring
        roce = metrics.get("roce")
        roce_weight = weights.get("roce", 0.0)
        if roce is not None:
            t = thresholds.get("roce", {})
            if roce >= t.get("excellent", 0.30):
                points = 100 * roce_weight
                reasons.append("Positive: ROCE exceeds excellent threshold (>30%)")
            elif roce >= t.get("good", 0.20):
                points = 70 * roce_weight
                reasons.append("Positive: ROCE is good (>20%)")
            else:
                points = 0
                reasons.append("Negative: ROCE is poor.")
            score += points
            total_weight_scored += roce_weight
            breakdown["roce_score"] = points
        else:
            warnings.append("ROCE missing; could not score.")

        # 2. ROE Scoring
        roe = metrics.get("roe")
        roe_weight = weights.get("roe", 0.0)
        if roe is not None:
            t = thresholds.get("roe", {})
            if roe >= t.get("excellent", 0.20):
                points = 100 * roe_weight
                reasons.append("Positive: ROE is excellent (>=20%)")
            elif roe >= t.get("good", 0.15):
                points = 70 * roe_weight
                reasons.append("Positive: ROE is good (>=15%)")
            else:
                points = 0
                reasons.append("Negative: ROE is poor.")
            score += points
            total_weight_scored += roe_weight
            breakdown["roe_score"] = points
        else:
            warnings.append("ROE missing; could not score.")

        # 3. Growth Scoring
        growth = metrics.get("revenue_cagr_3y")
        growth_weight = weights.get("growth", 0.0)
        if growth is not None:
            t = thresholds.get("growth", {})
            if growth >= t.get("excellent", 0.15):
                points = 100 * growth_weight
                reasons.append("Positive: Growth is excellent (>=15%)")
            elif growth >= t.get("good", 0.10):
                points = 70 * growth_weight
                reasons.append("Positive: Growth is good (>=10%)")
            else:
                points = 0
                reasons.append("Negative: Growth is poor.")
            score += points
            total_weight_scored += growth_weight
            breakdown["growth_score"] = points
        else:
            warnings.append("Growth missing; could not score.")

        # 4. Margins Scoring
        margin = metrics.get("operating_margin")
        margins_weight = weights.get("margins", 0.0)
        if margin is not None:
            t = thresholds.get("margins", {})
            if margin >= t.get("excellent", 0.20):
                points = 100 * margins_weight
                reasons.append("Positive: Operating Margin is excellent (>=20%)")
            elif margin >= t.get("good", 0.10):
                points = 70 * margins_weight
                reasons.append("Positive: Operating Margin is good (>=10%)")
            else:
                points = 0
                reasons.append("Negative: Operating Margin is poor.")
            score += points
            total_weight_scored += margins_weight
            breakdown["margins_score"] = points
        else:
            warnings.append("Operating Margin missing; could not score.")

        # 5. Debt Scoring
        debt_to_equity = metrics.get("debt_to_equity")
        debt_weight = weights.get("debt", 0.0)
        if debt_to_equity is not None:
            t = thresholds.get("debt_to_equity", {})
            if debt_to_equity <= t.get("excellent", 0.1):
                points = 100 * debt_weight
                reasons.append("Positive: Debt to Equity is excellent (<=0.1x)")
            elif debt_to_equity <= t.get("good", 0.5):
                points = 70 * debt_weight
                reasons.append("Positive: Debt to Equity is manageable (<=0.5x)")
            else:
                points = 0
                reasons.append("Negative: Debt to Equity exceeds configured limit.")
            score += points
            total_weight_scored += debt_weight
            breakdown["debt_score"] = points
        else:
            warnings.append("Debt to Equity missing; could not score.")
            
        # 6. Capital Allocation Scoring
        fcf_conversion = metrics.get("fcf_conversion")
        capital_allocation_weight = weights.get("capital_allocation", 0.0)
        if fcf_conversion is not None:
            t = thresholds.get("capital_allocation", {})
            if fcf_conversion >= t.get("excellent", 1.0):
                points = 100 * capital_allocation_weight
                reasons.append("Positive: FCF Conversion is excellent (100%)")
            elif fcf_conversion >= t.get("good", 0.5):
                points = 70 * capital_allocation_weight
                reasons.append("Positive: FCF Conversion is average (>=50%)")
            else:
                points = 0
                reasons.append("Negative: FCF Conversion is poor.")
            score += points
            total_weight_scored += capital_allocation_weight
            breakdown["capital_allocation_score"] = points
        else:
            warnings.append("FCF Conversion missing; could not score.")

        final_score = None
        confidence = financial_result.confidence
        if total_weight_scored > 0:
            final_score = score / total_weight_scored
            if total_weight_scored < 1.0:
                reasons.append(f"Score prorated. Only {total_weight_scored:.1%} of metric weights were available.")
                confidence *= total_weight_scored # Reduce confidence if data is missing
        else:
            warnings.append("No business metrics were scorable. Score is None.")
            confidence = 0.0

        return EngineResult(
            value=final_score,
            confidence=confidence,
            breakdown=breakdown,
            reasons=reasons,
            method="Configurable YAML Scoring",
            rule_version=version,
            timestamp=datetime.now(),
            warnings=warnings
        )
