"""
Unit tests for ValuationEngine, added when:
  1. Fixing the confidence divisor (was /3.0 for only 2 implemented models).
  2. Fixing `if dcf_val:` / `if graham_val:` truthiness checks that would have
     silently dropped a legitimately-zero valuation.
"""
import pytest
from domain.engines.valuation import ValuationEngine


FULL_DATA = {
    "eps": 5.0,
    "bvps": 20.0,
    "fcf": 150.0,
    "shares_outstanding": 40.0,
    "roe": 0.20,
    "payout_ratio": 0.30,
}


def test_confidence_is_full_when_both_models_available():
    """With both DCF and Graham computed, confidence should be 1.0, not ~0.67."""
    engine = ValuationEngine()
    result = engine.calculate_valuation(FULL_DATA, current_price=45.0)

    assert "dcf_value" in result.breakdown
    assert "graham_value" in result.breakdown
    assert result.confidence == pytest.approx(1.0)


def test_confidence_is_half_when_only_graham_available():
    """Missing DCF inputs (no fcf/shares) should leave confidence at 0.5, not 0.33."""
    data = dict(FULL_DATA)
    data["fcf"] = None
    data["shares_outstanding"] = None

    engine = ValuationEngine()
    result = engine.calculate_valuation(data, current_price=45.0)

    assert "dcf_value" not in result.breakdown
    assert "graham_value" in result.breakdown
    assert result.confidence == pytest.approx(0.5)


def test_zero_dcf_value_is_not_dropped(monkeypatch):
    """A DCF value of exactly 0.0 is a legitimate (if unusual) result and must
    not be treated as 'missing' by a truthiness check."""
    engine = ValuationEngine()
    monkeypatch.setattr(engine, "calculate_dcf", lambda *a, **k: 0.0)

    result = engine.calculate_valuation(FULL_DATA, current_price=45.0)

    assert "dcf_value" in result.breakdown
    assert result.breakdown["dcf_value"] == 0.0


def test_zero_graham_value_is_not_dropped(monkeypatch):
    """Same guard, for the Graham Number."""
    engine = ValuationEngine()
    monkeypatch.setattr(engine, "calculate_graham", lambda *a, **k: 0.0)

    result = engine.calculate_valuation(FULL_DATA, current_price=45.0)

    assert "graham_value" in result.breakdown
    assert result.breakdown["graham_value"] == 0.0


def test_no_models_available_yields_zero_confidence_and_status():
    data = {"eps": None, "bvps": None, "fcf": None, "shares_outstanding": None}
    engine = ValuationEngine()
    result = engine.calculate_valuation(data, current_price=45.0)

    assert result.confidence == pytest.approx(0.0)
    status = result.breakdown.get("valuation_status", "")
    assert status.startswith("Invalid Inputs") or status.startswith("Missing Inputs")
