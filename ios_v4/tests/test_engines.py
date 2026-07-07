import pytest
from domain.engines.scoring import ScoringEngine
from domain.engines.risk import RiskEngine
from domain.engines.investment import InvestmentEngine
from domain.engines.allocation import AllocationEngine
from domain.models import EngineResult

from datetime import datetime

class DummyParser:
    def get_scoring_weights(self):
        return {
            "roce": 0.25,
            "roe": 0.20,
            "growth": 0.20,
            "margins": 0.15,
            "debt": 0.10,
            "capital_allocation": 0.10
        }
    def get_scoring_thresholds(self):
        return {
            "roce": {"excellent": 0.30, "good": 0.20, "poor": 0.10},
            "roe": {"excellent": 0.20, "good": 0.15, "poor": 0.10},
            "growth": {"excellent": 0.15, "good": 0.10, "poor": 0.05},
            "margins": {"excellent": 0.20, "good": 0.10, "poor": 0.05},
            "debt_to_equity": {"excellent": 0.1, "good": 0.5, "poor": 1.0},
            "capital_allocation": {"excellent": 1.0, "good": 0.5, "poor": 0.0}
        }
    def get_risk_dimensions(self):
        return {"financial": 0.60, "valuation": 0.40}
    def get_risk_thresholds(self):
        return {}
    def get_rules(self, domain: str):
        if domain == "scoring":
            return {
                "business_score": {
                    "weights": self.get_scoring_weights(),
                    "thresholds": self.get_scoring_thresholds()
                },
                "risk_score": {
                    "dimensions": self.get_risk_dimensions(),
                    "thresholds": self.get_risk_thresholds()
                }
            }
        return {}
    def get_rule_version(self, domain: str):
        return "v1"

def make_result(value=0, breakdown=None):
    return EngineResult(
        value=value, 
        confidence=1.0, 
        breakdown=breakdown or {}, 
        reasons=[], 
        method="test", 
        rule_version="1", 
        timestamp=datetime.now(), 
        warnings=[]
    )

def test_business_score():
    engine = ScoringEngine(rule_parser=DummyParser())
    
    financial_result = make_result(value=0, breakdown={
        "roce": 0.35,              # excellent (100 * 0.25 = 25)
        "roe": 0.16,               # good (70 * 0.20 = 14)
        "revenue_cagr_3y": 0.05,   # poor (0 * 0.20 = 0)
        "operating_margin": 0.25,  # excellent (100 * 0.15 = 15)
        "debt_to_equity": 0.05,    # excellent (100 * 0.10 = 10)
        "fcf_conversion": 0.60     # good (70 * 0.10 = 7)
    })
    
    # Expected score = 25 + 14 + 0 + 15 + 10 + 7 = 71
    rules = engine.rule_parser.get_rules("scoring")
    result = engine.compute_business_score(financial_result)
    assert result.value == 71.0
    
def test_risk_score():
    engine = RiskEngine(rule_parser=DummyParser())
    financial_result = make_result(value=0, breakdown={
        "debt_to_equity": 1.5,
        "fcf_conversion": 0.1
    })
    valuation_result = make_result(value=0, breakdown={
        "margin_of_safety": -0.2
    })
    
    result = engine.compute_risk(financial_result, valuation_result)
    # Just checking it returns a valid score between 0 and 100
    assert 0 <= result.value <= 100
    
def test_investment_score():
    engine = InvestmentEngine()
    b_res = make_result(value=80.0, breakdown={})
    v_res = make_result(value=0, breakdown={"margin_of_safety": 0.20})
    r_res = make_result(value=20.0, breakdown={})
    
    # Value Multiplier = 1.0 + 0.20 = 1.2x
    # Risk Adjustment = 1.0 - (20/100) = 0.8x
    # Investment Score = 80.0 * 1.2 * 0.8 = 76.8
    result = engine.compute_investment_score(b_res, v_res, r_res)
    assert abs(result.value - 76.8) < 0.01
    
def test_allocation():
    engine = AllocationEngine(max_position_size=0.10, cash_floor=0.05)
    
    scores = {
        "A": make_result(value=100.0, breakdown={}),
        "B": make_result(value=50.0, breakdown={}),
        "C": make_result(value=0.0, breakdown={})
    }
    
    allocs = engine.calculate_allocations(scores)
    
    # C should have 0 allocation
    assert "C" not in allocs or allocs["C"].value == 0
    
    # Sum of allocations should be 1.0 - 0.05 (cash) = 0.95
    total = sum(res.value for res in allocs.values())
    # Max sum of allocations for 2 assets is 0.20
    assert abs(total - 0.20) < 0.01
    
    # Weight of A vs B: A = 100, B = 50.
    # Sum of scores = 150
    # A's raw = 100/150 = 66.6% -> capped at 10%
    assert abs(allocs["A"].value - 0.10) < 0.01
