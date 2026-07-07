"""
Unit tests for FinancialEngine, added when replacing the hardcoded
`revenue_cagr_3y = 0.15` mock with a real calculation from provider-supplied
revenue history.
"""
import pytest
from domain.engines.financial import FinancialEngine


BASE_DATA = {
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


def test_cagr_calculated_from_real_revenue_history():
    """Two data points three years apart should yield a real, non-mocked CAGR."""
    data = dict(BASE_DATA)
    data["revenue_history"] = [
        {"date": "2022-03-31", "value": 700.0},
        {"date": "2025-03-31", "value": 1000.0},
    ]

    engine = FinancialEngine()
    result = engine.calculate_metrics(data)

    expected_cagr = (1000.0 / 700.0) ** (1 / 3) - 1
    assert "revenue_cagr_3y" in result.breakdown
    # rel tolerance is loose because the engine computes elapsed years from actual
    # calendar days (365.25/year), which differs slightly from a naive integer "3".
    assert result.breakdown["revenue_cagr_3y"] == pytest.approx(expected_cagr, rel=1e-3)
    # Must never silently fall back to the old hardcoded 0.15 mock.
    assert result.breakdown["revenue_cagr_3y"] != 0.15


def test_cagr_missing_when_no_history_provided():
    """Without revenue history, no CAGR should be fabricated; a warning should explain why."""
    data = dict(BASE_DATA)  # no "revenue_history" key at all

    engine = FinancialEngine()
    result = engine.calculate_metrics(data)

    assert "revenue_cagr_3y" not in result.breakdown
    assert any("CAGR" in w for w in result.warnings)


def test_cagr_missing_when_history_too_short():
    """A single data point can't produce a CAGR."""
    data = dict(BASE_DATA)
    data["revenue_history"] = [{"date": "2025-03-31", "value": 1000.0}]

    engine = FinancialEngine()
    result = engine.calculate_metrics(data)

    assert "revenue_cagr_3y" not in result.breakdown
    assert any("CAGR" in w for w in result.warnings)


def test_cagr_handles_declining_or_invalid_revenue_gracefully():
    """Non-positive revenue in history should not raise, and should skip CAGR."""
    data = dict(BASE_DATA)
    data["revenue_history"] = [
        {"date": "2022-03-31", "value": -50.0},
        {"date": "2025-03-31", "value": 1000.0},
    ]

    engine = FinancialEngine()
    result = engine.calculate_metrics(data)

    assert "revenue_cagr_3y" not in result.breakdown
    assert any("CAGR" in w for w in result.warnings)


def test_existing_margin_and_return_metrics_unaffected():
    """Sanity check that the CAGR fix didn't disturb unrelated calculations."""
    data = dict(BASE_DATA)
    engine = FinancialEngine()
    result = engine.calculate_metrics(data)

    assert result.breakdown["roe"] == pytest.approx(0.25)
    assert result.breakdown["roce"] == pytest.approx(0.25)
    assert result.breakdown["debt_to_equity"] == pytest.approx(0.0625)
