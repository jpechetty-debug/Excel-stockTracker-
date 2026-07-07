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
            breakdown["roce_score"] = points
        else:
            warnings.append("ROCE missing; could not score.")

        # 2. Debt Scoring
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
            breakdown["debt_score"] = points
        else:
            warnings.append("Debt to Equity missing; could not score.")

        return EngineResult(
            value=score,
            confidence=financial_result.confidence,
            breakdown=breakdown,
            reasons=reasons,
            method="Configurable YAML Scoring",
            rule_version=version,
            timestamp=datetime.now(),
            warnings=warnings
        )
