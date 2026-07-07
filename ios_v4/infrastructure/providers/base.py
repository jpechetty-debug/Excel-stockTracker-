"""
Base Provider Protocol
Defines the strict read-only interface that all market data providers must implement.
"""

from typing import Protocol, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

@dataclass(slots=True, frozen=True)
class ProviderHealth:
    """Metadata regarding the provider's operational status."""
    status: str             # e.g., "OK", "DEGRADED", "OFFLINE"
    provider_version: str   # e.g., "yfinance 0.2.31"
    latency_ms: int         # Last recorded latency
    cache_hit_rate: float   # Between 0.0 and 1.0
    oldest_cached_data: datetime | None
    latest_refresh: datetime | None
    last_error: str | None


class MarketDataProvider(Protocol):
    """
    Protocol strictly for retrieving raw market and financial data.
    Providers should NEVER mutate domain models or Excel files directly.
    """
    
    @property
    def name(self) -> str:
        """The canonical name of the provider (e.g., 'yfinance')."""
        ...
        
    def health(self) -> ProviderHealth:
        """Returns the current operational status of the provider."""
        ...

    def get_quote(self, ticker: str) -> Dict[str, Any]:
        """Fetches raw quote data."""
        ...

    def get_income_statement(self, ticker: str) -> Dict[str, Any]:
        """Fetches raw income statement data."""
        ...

    def get_balance_sheet(self, ticker: str) -> Dict[str, Any]:
        """Fetches raw balance sheet data."""
        ...

    def get_cash_flow(self, ticker: str) -> Dict[str, Any]:
        """Fetches raw cash flow statement data."""
        ...

    def get_corporate_actions(self, ticker: str) -> Dict[str, Any]:
        """Fetches raw corporate actions (splits, dividends)."""
        ...
