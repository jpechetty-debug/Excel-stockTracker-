"""
Unit tests for UpdatePlanner._values_equivalent, added when replacing the
str(old_val) == str(new_val) comparison (which was prone to false "UPDATED"
statuses from float formatting/precision noise).
"""
from unittest.mock import MagicMock
from datetime import datetime
from infrastructure.excel.planner import UpdatePlanner
from domain.models import CompanyData, Metric, Provenance


def test_identical_floats_are_equivalent():
    assert UpdatePlanner._values_equivalent(10.0, 10.0) is True


def test_float_precision_noise_is_equivalent():
    assert UpdatePlanner._values_equivalent(10.0, 10.0 + 1e-10) is True


def test_string_vs_numeric_representation_is_equivalent():
    # Common case: Excel cell read back as "10" (str) vs freshly computed 10.0 (float)
    assert UpdatePlanner._values_equivalent("10", 10.0) is True


def test_genuinely_different_floats_are_not_equivalent():
    assert UpdatePlanner._values_equivalent(10.0, 10.5) is False


def test_none_handling():
    assert UpdatePlanner._values_equivalent(None, None) is True
    assert UpdatePlanner._values_equivalent(None, 10.0) is False
    assert UpdatePlanner._values_equivalent(10.0, None) is False


def test_non_numeric_strings_fall_back_to_string_equality():
    assert UpdatePlanner._values_equivalent("BUY", "BUY") is True
    assert UpdatePlanner._values_equivalent("BUY", "SELL") is False


def _make_planner(field_col_map):
    config = MagicMock()
    config.column_map = {
        "zones": {"system": [{"field": f, "column": c} for f, c in field_col_map.items()]}
    }
    return UpdatePlanner(config=config)


def _company_with_metric(ticker, field, value):
    prov = Provenance("mock", "mock", datetime.now(), 1.0, "v1", "v1")
    c = CompanyData(ticker=ticker, company_name=ticker)
    c.metrics[field] = Metric(value, prov)
    return c


def test_percent_column_stuck_cell_is_detected_and_corrected():
    """
    Regression test for a real production bug: ExcelWriter multiplies numeric
    values by 100 for any column whose name contains "%" (engines store raw
    fractions internally, e.g. 0.36 for 36% ROE). If a cell was ever written
    un-scaled (or the planner compared pre-scaling), the planner would see the
    freshly-recomputed raw fraction as numerically equal to that stale,
    never-scaled cell value, mark it UNCHANGED, and permanently skip writing
    it -- freezing that one field at the wrong scale forever while every other
    ticker read correctly. This confirms the comparison now accounts for the
    writer's scaling transform.
    """
    planner = _make_planner({"roe": "ROE %"})
    company = _company_with_metric("TEJASNET.NS", "roe", -0.310109284956344)

    # Stuck cell: old value was never multiplied by 100.
    existing = {"TEJASNET.NS": {"roe": -0.310109284956344}}
    plan = planner.create_plan([company], existing)
    action = plan.actions[0]
    assert action.status.name == "UPDATED", "Scale mismatch must be detected and force a corrective write"


def test_percent_column_healthy_steady_state_is_unchanged():
    """Once a % column is correctly scaled, unchanged fundamentals should not
    trigger a spurious rewrite every run."""
    planner = _make_planner({"roe": "ROE %"})
    company = _company_with_metric("CAMS.NS", "roe", 0.3603169934056724)

    existing = {"CAMS.NS": {"roe": 36.03169934056724}}  # already correctly scaled
    plan = planner.create_plan([company], existing)
    action = plan.actions[0]
    assert action.status.name == "UNCHANGED"


def test_non_percent_column_is_not_scaled():
    """Fields whose column name has no "%" must never be multiplied by 100."""
    planner = _make_planner({"price": "Current Price"})
    company = _company_with_metric("X", "price", 100.0)

    unchanged_plan = planner.create_plan([company], {"X": {"price": 100.0}})
    assert unchanged_plan.actions[0].status.name == "UNCHANGED"

    changed_plan = planner.create_plan([company], {"X": {"price": 99.0}})
    assert changed_plan.actions[0].status.name == "UPDATED"
