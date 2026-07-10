"""
Unit tests for StepFetchData.

History:
  - Fixed a field-name mismatch bug: column_map.yaml maps the "Current Price"
    and "Previous Close" Excel columns to field names "current_price" and
    "previous_close" respectively. The merged dict built by _fetch_one only
    ever set a key called "price" (used internally by the valuation engine)
    and never set "current_price" at all, and never set "previous_close"
    either. This meant company.metrics["current_price"] was never populated
    for ANY company on ANY pipeline run -- the "Current Price" column was
    permanently frozen at whatever value happened to be in the cell before
    this bug was introduced (stale for existing rows, blank for newly added
    ones). The underlying valuation math was unaffected (it reads "price"
    directly), but a human auditing the sheet had no reliable way to see
    what price the engine actually used.
"""
import sys
import types
import tempfile

# loguru isn't installed in every environment this runs in; stub it before
# importing anything that transitively imports infrastructure.logging.logger.
if "loguru" not in sys.modules:
    fake_loguru = types.ModuleType("loguru")

    class _FakeLogger:
        def __getattr__(self, name):
            return lambda *a, **k: None

        def add(self, *a, **k):
            pass

    fake_loguru.logger = _FakeLogger()
    sys.modules["loguru"] = fake_loguru

import pytest
from pipeline.context import ExecutionContext
from pipeline.steps.step_fetch_data import StepFetchData
from domain.models import CompanyData
from infrastructure.providers.registry import ProviderRegistry


class _FakeProvider:
    exchange_suffix = None

    def __init__(self, current_price=752.0, previous_close=748.5):
        self._current_price = current_price
        self._previous_close = previous_close

    def get_quote(self, ticker):
        return {
            "current_price": self._current_price,
            "previous_close": self._previous_close,
            "market_cap": 1_000_000_000.0,
            "trailing_pe": 41.1,
            "roe": 0.36,
            "shares_outstanding": 1_000_000.0,
            "trailing_eps": 18.0,
            "payout_ratio": 0.3,
            "dividend_yield": 0.01,
        }

    def get_income_statement(self, ticker):
        return {"Total Revenue": 1e8, "Net Income": 1e7, "Operating Income": 1.2e7}

    def get_balance_sheet(self, ticker):
        return {"Stockholders Equity": 5e7, "Total Assets": 8e7, "Current Liabilities": 1e7, "Total Debt": 5e6}

    def get_cash_flow(self, ticker):
        return {"Free Cash Flow": 8e6}


def _run_fetch(provider_name, provider):
    ProviderRegistry._providers[provider_name] = lambda: provider

    with tempfile.TemporaryDirectory():
        ctx = ExecutionContext(provider_name=provider_name, threads=1)
        ctx.config = {"cache": {"enabled": False}, "application": {}, "market": {}}
        ctx.artifacts.raw_companies = [CompanyData(ticker="TEST.NS", company_name="Test Co")]
        step = StepFetchData()
        assert step.validate(ctx) is True
        ok = step.execute(ctx)
        assert ok is True
        return ctx.artifacts.market_data["TEST.NS"]


def test_current_price_field_is_populated():
    """Regression test: 'current_price' must be a real key in the merged dict,
    matching what column_map.yaml expects for the 'Current Price' column."""
    data = _run_fetch("fetch_test_current_price", _FakeProvider(current_price=752.0))
    assert "current_price" in data
    assert data["current_price"] == pytest.approx(752.0)


def test_previous_close_field_is_populated():
    """Regression test: 'previous_close' must be a real key in the merged dict,
    matching what column_map.yaml expects for the 'Previous Close' column."""
    data = _run_fetch("fetch_test_previous_close", _FakeProvider(previous_close=748.5))
    assert "previous_close" in data
    assert data["previous_close"] == pytest.approx(748.5)


def test_current_price_matches_internal_price_field():
    """'current_price' (display) and 'price' (used internally by the valuation
    engine) must never silently diverge -- they should be the same validated
    number, just exposed under both names for different consumers."""
    data = _run_fetch("fetch_test_consistency", _FakeProvider(current_price=752.0))
    assert data["current_price"] == data["price"]


def test_invalid_previous_close_is_rejected_not_passed_through_raw():
    """previous_close should go through the same DataValidator.validate_price
    gate as current_price (e.g. reject a negative/garbage value) rather than
    being passed straight from the provider unvalidated."""
    data = _run_fetch("fetch_test_invalid_prev_close", _FakeProvider(previous_close=-5.0))
    assert data["previous_close"] is None
