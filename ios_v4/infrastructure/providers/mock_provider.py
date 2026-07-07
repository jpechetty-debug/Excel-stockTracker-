"""
Mock Provider
Provides deterministic, offline market data for end-to-end testing.

Field names deliberately mirror the raw yfinance vocabulary (e.g. "Total Revenue",
"Net Income") rather than the pipeline's internal normalized names, since
step_fetch_data.py expects raw-provider-shaped dicts from every registered
MarketDataProvider. This keeps `--provider mock` usable as a realistic offline
stand-in for the full pipeline (CI/CD, demos, manual smoke tests) rather than
only for isolated unit tests.
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
            "volume": 1200000,
            "forward_pe": 19.5,
            "trailing_pe": 20.1,
            "roe": 0.22,
            "shares_outstanding": 47393364.0,
            "trailing_eps": 5.50,
            "payout_ratio": 0.30,
            "dividend_yield": 0.015,
        }

    def get_income_statement(self, ticker: str) -> Dict[str, Any]:
        return {
            "Total Revenue": 1000000000.0,
            "Net Income": 150000000.0,
            "Operating Income": 200000000.0,
            "Basic EPS": 5.50,
            "Diluted EPS": 5.40,
            "Basic Average Shares": 47393364.0,
            # 3 years of revenue history, oldest -> newest, for CAGR calculation.
            "revenue_history": [
                {"date": "2023-03-31", "value": 800000000.0},
                {"date": "2024-03-31", "value": 890000000.0},
                {"date": "2025-03-31", "value": 1000000000.0},
            ],
        }

    def get_balance_sheet(self, ticker: str) -> Dict[str, Any]:
        return {
            "Total Assets": 2500000000.0,
            "Total Liabilities": 1000000000.0,
            "Stockholders Equity": 1500000000.0,
            "Total Equity Gross Minority Interest": 1500000000.0,
            "Current Liabilities": 400000000.0,
            "Total Debt": 300000000.0,
            "Minority Interest": 0.0,
            "Preferred Stock": 0.0,
            "Cash And Cash Equivalents": 250000000.0,
        }

    def get_cash_flow(self, ticker: str) -> Dict[str, Any]:
        return {
            "Operating Cash Flow": 200000000.0,
            "Free Cash Flow": 120000000.0,
        }

    def get_corporate_actions(self, ticker: str) -> Dict[str, Any]:
        return {
            "dividends": [0.50, 0.50, 0.50, 0.55],
            "splits": []
        }
