import pytest
from datetime import datetime, timedelta
import math
from domain.normalizer import DataNormalizer
from domain.exceptions import CacheMissError
from infrastructure.cache.manager import CacheManager
from infrastructure.providers.registry import ProviderRegistry
from infrastructure.providers.mock_provider import MockProvider
from infrastructure.providers.yfinance_provider import YFinanceProvider


def test_normalizer():
    # Value normalization
    assert DataNormalizer.normalize_value(None) is None
    assert DataNormalizer.normalize_value("N/A") is None
    assert DataNormalizer.normalize_value("nan") is None
    assert DataNormalizer.normalize_value(math.nan) is None
    assert DataNormalizer.normalize_value(50.5) == 50.5
    
    # Currency normalization
    assert DataNormalizer.normalize_currency(100.0, "raw") == 100.0
    assert DataNormalizer.normalize_currency(100.0, "m") == 100000000.0
    assert DataNormalizer.normalize_currency(1.5, "billions") == 1500000000.0
    
    # Nested raw data
    raw = {"price": 10.5, "pe": "n/a", "nested": {"val": math.nan}}
    clean = DataNormalizer.process_raw_data(raw)
    assert clean["price"] == 10.5
    assert clean["pe"] is None
    assert clean["nested"]["val"] is None


def test_cache_manager(tmp_path):
    cache = CacheManager(base_dir=tmp_path)
    
    data = {"current_price": 150.0, "provider": "mock"}
    cache.set("quotes", "TEST", data)
    
    # Should retrieve successfully
    retrieved = cache.get("quotes", "TEST")
    assert retrieved["current_price"] == 150.0
    
    # Should throw on miss
    with pytest.raises(CacheMissError):
        cache.get("quotes", "UNKNOWN")


def test_provider_registry():
    provider = ProviderRegistry.get_provider("mock")
    assert isinstance(provider, MockProvider)
    
    # Ensure health is deterministic
    health = provider.health()
    assert health.status == "OK"
    assert health.cache_hit_rate == 1.0


def test_yfinance_provider_instantiation():
    provider = ProviderRegistry.get_provider("yfinance")
    assert provider.name == "yfinance"
    health = provider.health()
    assert health.status == "OK"
