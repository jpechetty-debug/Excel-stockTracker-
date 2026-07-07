"""
Mock Provider
Provides deterministic, offline market data for end-to-end testing.
"""

from typing import Dict, Any
from datetime import datetime
from infrastructure.providers.base import MarketDataProvider, ProviderHealth
from infrastructure.providers.registry import ProviderRegistry


@ProviderRegistry.register("mock")
class MockProvider(MarketDataProvider):
    """
    Offline data provider returning hardcoded static dictionaries.
    Extremely useful for CI/CD and predictable tests.
    """
    
    @property
    def name(self) -> str:
        return "mock"
        
    def health(self) -> ProviderHealth:
        return ProviderHealth(
            status="OK",
            provider_version="mock 1.0",
            latency_ms=1,
            cache_hit_rate=1.0,
            oldest_cached_data=datetime.now(),
            latest_refresh=datetime.now(),
            last_error=None
        )

    def get_quote(self, ticker: str) -> Dict[str, Any]:
        return {
            "current_price": 105.50,
            "previous_close": 104.00,
            "market_cap": 5000000000.0,
            "volume": 1200000
        }

    def get_income_statement(self, ticker: str) -> Dict[str, Any]:
        return {
            "revenue": 1000000000.0,
            "net_income": 150000000.0,
            "eps": 5.50
        }

    def get_balance_sheet(self, ticker: str) -> Dict[str, Any]:
        return {
            "total_assets": 2500000000.0,
            "total_liabilities": 1000000000.0,
            "total_equity": 1500000000.0
        }

    def get_cash_flow(self, ticker: str) -> Dict[str, Any]:
        return {
            "operating_cash_flow": 200000000.0,
            "free_cash_flow": 120000000.0
        }

    def get_corporate_actions(self, ticker: str) -> Dict[str, Any]:
        return {
            "dividends": [0.50, 0.50, 0.50, 0.55],
            "splits": []
        }
