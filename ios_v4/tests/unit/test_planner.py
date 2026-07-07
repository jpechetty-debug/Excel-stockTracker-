"""
Unit tests for UpdatePlanner._values_equivalent, added when replacing the
str(old_val) == str(new_val) comparison (which was prone to false "UPDATED"
statuses from float formatting/precision noise).
"""
from infrastructure.excel.planner import UpdatePlanner


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
