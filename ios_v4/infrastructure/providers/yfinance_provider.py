"""
YFinance Provider
Integrates the yfinance library using network resilience wrappers (retries/rate limits).
"""

from typing import Dict, Any
from datetime import datetime
import yfinance as yf
from infrastructure.providers.base import MarketDataProvider, ProviderHealth
from infrastructure.providers.registry import ProviderRegistry
from infrastructure.network.session import SessionManager
from infrastructure.network.rate_limiter import RateLimiter
from infrastructure.network.retry import api_retry_policy
from infrastructure.logging.logger import logger


@ProviderRegistry.register("yfinance")
class YFinanceProvider(MarketDataProvider):
    """
    yfinance implementation wrapper.
    Utilizes global SessionManager and RateLimiter.
    """
    
    def __init__(self):
        self.session_manager = SessionManager()
        # yfinance can be strict, default to 1 request per second
        self.rate_limiter = RateLimiter(requests_per_second=1.0)
        self._last_latency = 0
        self._cache_hits = 0
        self._total_requests = 0
        self._last_error = None
        
    @property
    def name(self) -> str:
        return "yfinance"

    def health(self) -> ProviderHealth:
        hit_rate = (self._cache_hits / self._total_requests) if self._total_requests > 0 else 1.0
        return ProviderHealth(
            status="OK" if not self._last_error else "DEGRADED",
            provider_version=yf.__version__,
            latency_ms=self._last_latency,
            cache_hit_rate=hit_rate,
            oldest_cached_data=None, # Inferred by cache layer
            latest_refresh=datetime.now(),
            last_error=self._last_error
        )

    def _get_ticker_obj(self, ticker: str) -> yf.Ticker:
        """Helper to get a yf.Ticker."""
        return yf.Ticker(ticker)

    @api_retry_policy
    def get_quote(self, ticker: str) -> Dict[str, Any]:
        """Fetches standard quote and profile fields."""
        self.rate_limiter.wait()
        start = datetime.now()
        try:
            t = self._get_ticker_obj(ticker)
            info = t.info
            self._total_requests += 1
            self._last_latency = int((datetime.now() - start).total_seconds() * 1000)
            
            return {
                "current_price": info.get("currentPrice"),
                "previous_close": info.get("previousClose"),
                "market_cap": info.get("marketCap"),
                "volume": info.get("volume"),
                "forward_pe": info.get("forwardPE"),
                "trailing_pe": info.get("trailingPE"),
                "roe": info.get("returnOnEquity")
            }
        except Exception as e:
            self._last_error = str(e)
            logger.error(f"YFinance error getting quote for {ticker}: {e}")
            raise

    @api_retry_policy
    def get_income_statement(self, ticker: str) -> Dict[str, Any]:
        self.rate_limiter.wait()
        try:
            t = self._get_ticker_obj(ticker)
            inc = t.income_stmt
            self._total_requests += 1
            if inc is None or inc.empty:
                return {}
            # Returning the most recent year's column roughly as a dict
            latest = inc.iloc[:, 0].to_dict()
            return latest
        except Exception as e:
            self._last_error = str(e)
            logger.error(f"YFinance error getting income stmt for {ticker}: {e}")
            raise

    @api_retry_policy
    def get_balance_sheet(self, ticker: str) -> Dict[str, Any]:
        self.rate_limiter.wait()
        try:
            t = self._get_ticker_obj(ticker)
            bs = t.balance_sheet
            self._total_requests += 1
            if bs is None or bs.empty:
                return {}
            latest = bs.iloc[:, 0].to_dict()
            return latest
        except Exception as e:
            self._last_error = str(e)
            logger.error(f"YFinance error getting balance sheet for {ticker}: {e}")
            raise

    @api_retry_policy
    def get_cash_flow(self, ticker: str) -> Dict[str, Any]:
        self.rate_limiter.wait()
        try:
            t = self._get_ticker_obj(ticker)
            cf = t.cashflow
            self._total_requests += 1
            if cf is None or cf.empty:
                return {}
            latest = cf.iloc[:, 0].to_dict()
            return latest
        except Exception as e:
            self._last_error = str(e)
            logger.error(f"YFinance error getting cashflow for {ticker}: {e}")
            raise

    @api_retry_policy
    def get_corporate_actions(self, ticker: str) -> Dict[str, Any]:
        self.rate_limiter.wait()
        try:
            t = self._get_ticker_obj(ticker)
            actions = t.actions
            self._total_requests += 1
            if actions is None or actions.empty:
                return {}
            # Returning as standard json dicts
            return actions.reset_index().to_dict(orient="records")
        except Exception as e:
            self._last_error = str(e)
            logger.error(f"YFinance error getting corporate actions for {ticker}: {e}")
            raise
