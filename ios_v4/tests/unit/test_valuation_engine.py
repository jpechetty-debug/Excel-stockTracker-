"""
Unit tests for ValuationEngine.

History:
  1. Fixed the confidence divisor (was /3.0 for only 2 implemented models).
  2. Fixed `if dcf_val:` / `if graham_val:` truthiness checks that would have
     silently dropped a legitimately-zero valuation.
  3. Added Relative P/E and Owner Earnings as two additional, independent
     valuation models (previously only DCF + Graham were implemented, despite
     rules/valuation.yaml describing all four), and switched the blend from an
     unweighted average to the configured weights (dcf 40% / relative_pe 20% /
     graham 20% / owner_earnings 20%, renormalized over whichever models are
     actually available). This was a real calibration bug, not just a
     refactor: the Graham Number is a book-value-based formula that
     structurally penalizes high-ROE, asset-light compounders (low BVPS
     relative to earnings power) as "overvalued" almost by construction.
     Averaged 50/50 with DCF, it was driving Margin of Safety to figures like
     -2100% for businesses with excellent Business Scores. Confidence is now
     len(models)/4
"""
from typing import Dict, Any
from decimal import Decimal
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

# Profile chosen so growth_rate > discount_rate (11% default), the exact
# condition that would otherwise silently exclude Relative P/E and Owner
# Earnings for the highest-ROE companies -- precisely the ones the fix targets.
ASSET_LIGHT_HIGH_ROE_DATA = {
    "eps": 50.0,
    "bvps": 90.0,
    "fcf": 250_000_000.0,
    "shares_outstanding": 5_000_000.0,
    "roe": 0.36,
    "payout_ratio": 0.60,
}


def test_confidence_is_full_when_all_four_models_available():
    engine = ValuationEngine()
    result = engine.calculate_valuation(FULL_DATA, current_price=45.0)

    for key in ("dcf_value", "relative_pe_value", "graham_value", "owner_earnings_value"):
        assert key in result.breakdown, f"expected {key} in breakdown"
    assert result.confidence == pytest.approx(1.0)


def test_confidence_is_half_when_dcf_and_owner_earnings_unavailable():
    """
    Missing fcf/shares removes DCF and Owner Earnings (both require FCF).
    Graham only needs eps+bvps, and Relative P/E gracefully falls back to a
    conservative 25% payout assumption when payout_ratio is missing, so both
    remain available -> confidence = 2/4 = 0.5.
    """
    data = dict(FULL_DATA)
    data["fcf"] = None
    data["shares_outstanding"] = None

    engine = ValuationEngine()
    result = engine.calculate_valuation(data, current_price=45.0)

    assert "dcf_value" not in result.breakdown
    assert "owner_earnings_value" not in result.breakdown
    assert "graham_value" in result.breakdown
    assert "relative_pe_value" in result.breakdown
    assert result.confidence == pytest.approx(0.5)


def test_zero_dcf_value_is_not_dropped(monkeypatch):
    """A DCF value of exactly 0.0 is a legitimate (if unusual) result and must
    not be treated as 'missing' by a truthiness check."""
    engine = ValuationEngine()
    monkeypatch.setattr(engine, "calculate_dcf", lambda *a, **k: Decimal('0'))

    result = engine.calculate_valuation(FULL_DATA, current_price=45.0)

    assert "dcf_value" in result.breakdown
    assert result.breakdown["dcf_value"] == 0.0


def test_zero_graham_value_is_not_dropped(monkeypatch):
    """Same guard, for the Graham Number."""
    engine = ValuationEngine()
    monkeypatch.setattr(engine, "calculate_graham", lambda *a, **k: Decimal('0'))

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


def test_high_growth_company_still_populates_relative_pe_and_owner_earnings():
    """
    Regression test for a bug introduced (and caught) while building this fix:
    calculate_relative_pe / calculate_owner_earnings_value are single-stage
    Gordon Growth formulas that require growth_rate < discount_rate. Feeding
    them the company's near-term SGR growth_rate directly (up to 25% by
    default) meant any high-growth company -- exactly the ones this fix is
    for -- would fail that guard and silently drop both new models. The
    engine must instead cap the growth rate fed into these two perpetuity
    formulas to a sustainable spread below the discount rate, the same way
    DCF already uses a separate terminal_growth for its own perpetuity stage.
    """
    engine = ValuationEngine()
    result = engine.calculate_valuation(ASSET_LIGHT_HIGH_ROE_DATA, current_price=3200.0)

    assert result.breakdown["growth_rate_used"] > 0.11, "test fixture should exceed the default discount rate"
    assert "relative_pe_value" in result.breakdown
    assert "owner_earnings_value" in result.breakdown
    assert result.confidence == pytest.approx(1.0)


def test_asset_light_high_roe_company_no_longer_dominated_by_graham():
    """
    The core calibration fix: for a high-ROE, asset-light profile (low BVPS
    relative to EPS), Graham Number alone reads as deeply "undervalued-looking
    cheap" in absolute terms but far below DCF/relative_pe/owner_earnings --
    i.e. it's the outlier, not the anchor. With only DCF+Graham averaged
    50/50 (the old behavior), the blended value is pulled hard toward
    Graham's book-value-anchored number. With four models at configured
    weights, Graham's 20% weight can no longer single-handedly crater the
    blend the way an unconditional 2-model average did.
    """
    engine = ValuationEngine()
    result = engine.calculate_valuation(ASSET_LIGHT_HIGH_ROE_DATA, current_price=3200.0)

    graham_only_blend = (result.breakdown["dcf_value"] + result.breakdown["graham_value"]) / 2
    four_model_blend = result.breakdown["intrinsic_value"]

    assert four_model_blend > graham_only_blend, (
        "four-model weighted blend should value the asset-light compounder "
        "higher than an unconditional DCF+Graham average would have"
    )


def test_weights_are_configurable_and_renormalize_over_available_models():
    """If a model is unavailable, remaining models should keep their relative
    weight to each other rather than being diluted by the missing one."""
    engine = ValuationEngine({"weights": {"dcf": 0.5, "relative_pe": 0.5, "graham": 0.0, "owner_earnings": 0.0}})
    data = dict(FULL_DATA)
    data["bvps"] = None  # force Graham to be unavailable

    result = engine.calculate_valuation(data, current_price=45.0)
    assert "graham_value" not in result.breakdown
    # With graham/owner_earnings weighted at 0 and unavailable/zero-weighted,
    # remaining dcf/relative_pe should renormalize to a straight 50/50 average.
    expected = (result.breakdown["dcf_value"] + result.breakdown["relative_pe_value"]) / 2
    assert result.breakdown["intrinsic_value"] == pytest.approx(expected, rel=1e-6)
