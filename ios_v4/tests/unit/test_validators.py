import pytest
from domain.validators import DataValidator

def test_validate_pe():
    # Valid positive P/E
    val, conf = DataValidator.validate_pe(15.5)
    assert val == 15.5
    assert conf == 95
    
    # Negative P/E (rejected)
    val, conf = DataValidator.validate_pe(-5.0)
    assert val is None
    assert conf == 0
    
    # Extremely high P/E (warning, reduced confidence)
    val, conf = DataValidator.validate_pe(600.0)
    assert val == 600.0
    assert conf == 80

def test_validate_roe():
    # Valid ROE
    val, conf = DataValidator.validate_roe(15.0)
    assert val == 15.0
    assert conf == 95
    
    # Invalid extreme ROE
    val, conf = DataValidator.validate_roe(500.0)
    assert val is None
    assert conf == 0

def test_assign_confidence():
    assert DataValidator.assign_confidence("yfinance", is_calculated=False) == 95
    assert DataValidator.assign_confidence("yfinance", is_calculated=True) == 80
    assert DataValidator.assign_confidence("official", is_calculated=False) == 100
    assert DataValidator.assign_confidence("unknown", is_calculated=False) == 50
