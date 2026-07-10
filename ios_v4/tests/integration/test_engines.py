import pytest
from pathlib import Path
from domain.engines.financial import FinancialEngine
from domain.engines.valuation import ValuationEngine
from domain.engines.rule_parser import RuleParser
from domain.engines.scoring import ScoringEngine
from domain.engines.risk import RiskEngine
from domain.engines.allocation import AllocationEngine
from domain.models import EngineResult


@pytest.fixture
def test_rules_dir(tmp_path):
    """Creates a temporary rules directory to test YAML parsing."""
    rule_dir = tmp_path / "rules"
    rule_dir.mkdir()
    
    scoring_yaml = """
version: "test_v1"
business_score:
  weights:
    roce: 0.50
    debt: 0.50
  thresholds:
    roce:
      excellent: 30.0
      good: 20.0
    debt_to_equity:
      excellent: 0.1
      good: 0.5
risk_score:
  dimensions:
    financial: 0.50
    valuation: 0.50
"""
    (rule_dir / "scoring.yaml").write_text(scoring_yaml)
    return rule_dir


def test_end_to_end_engines(test_rules_dir):
    """
    Simulates a full pipeline from Mock Provider data to Final Allocation.
    Verifies isolation: Calculations happen first, then Decisions.
    """
    # 1. Simulate Normalized Mock Data
    mock_data = {
        "revenue": 1000.0,
        "net_income": 200.0,
        "operating_income": 250.0,
        "total_equity": 800.0,
        "total_assets": 1200.0,
        "current_liabilities": 200.0,
        "total_debt": 50.0,
        "eps": 5.0,
        "bvps": 20.0,
        "fcf": 150.0,
        "shares_outstanding": 40.0,
    }
    current_price = 45.0
    
    # 2. CALCULATION ENGINES (Objective Facts, No YAML Rules Needed)
    fin_eng = FinancialEngine()
    val_eng = ValuationEngine()
    
    fin_res = fin_eng.calculate_metrics(mock_data)
    val_res = val_eng.calculate_valuation(mock_data, current_price)
    
    # Assert Objective Facts
    assert fin_res.breakdown["roe"] == 0.25 # 200/800
    assert fin_res.breakdown["roce"] == 0.25 # 250/(1200-200)
    assert fin_res.breakdown["debt_to_equity"] == 0.0625 # 50/800
    assert "graham_value" in val_res.breakdown
    assert val_res.value > 0 # Blended value
    
    # 3. DECISION ENGINES (Interprets Facts via YAML Rules)
    parser = RuleParser(rule_dir=test_rules_dir)
    score_eng = ScoringEngine(parser)
    risk_eng = RiskEngine(parser)
    alloc_eng = AllocationEngine(max_position_size=0.60, cash_floor=0.05)
    
    # Business Score (ROCE=0.25 is Good, Debt=0.0625 is Excellent)
    score_res = score_eng.compute_business_score(fin_res)
    assert score_res.rule_version == "test_v1"
    assert "roce_score" in score_res.breakdown
    assert "debt_score" in score_res.breakdown
    assert score_res.value > 0 # Total score computed
    
    # Risk Score
    risk_res = risk_eng.compute_risk(fin_res, val_res)
    assert risk_res.value > 0
    
    # Allocation
    # Mocking a second ticker to test proportional sizing
    ticker_b_score = EngineResult(
        value=50.0, confidence=1.0, breakdown={}, reasons=[], 
        method="mock", rule_version="mock", timestamp=fin_res.timestamp, warnings=[]
    )
    ticker_a_score = score_res
    
    alloc_res = alloc_eng.calculate_allocations({"TICKER_A": ticker_a_score, "TICKER_B": ticker_b_score})
    
    # 1.0 - 0.05 cash = 0.95 total allocable
    total_alloc = sum(r.value for r in alloc_res.values())
    assert abs(float(total_alloc) - 0.95) < 0.01
    
    # TICKER_A or B should hit the 60% max_position_size constraint depending on scores
    for t, res in alloc_res.items():
        assert res.value <= 0.60 # Constraint respected!
        assert len(res.reasons) > 0 # Explainable AI reasons attached
