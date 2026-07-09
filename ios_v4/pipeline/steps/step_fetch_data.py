import math
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pipeline.context import ExecutionContext, Severity
from pipeline.runner import PipelineStep
from infrastructure.providers.registry import ProviderRegistry
from infrastructure.cache.manager import CacheManager
from domain.exceptions import CacheMissError
from domain.validators import DataValidator


def _is_valid(val):
    """Helper to check nan/None."""
    if val is None:
        return False
    if isinstance(val, float) and math.isnan(val):
        return False
    return True


def _safe_cache_key(ticker: str) -> str:
    """Sanitizes a ticker into a filesystem-safe cache key."""
    return re.sub(r"[^A-Za-z0-9_.\-]", "_", ticker)


class StepFetchData:

    @property
    def name(self) -> str:
        return "Fetch Market Data (Batch)"

    def validate(self, context: ExecutionContext) -> bool:
        if not context.artifacts.raw_companies:
            context.log("No companies loaded. Skipping fetch.", Severity.WARNING)
            return False
        return True

    def _get_cached_or_fetch(self, cache: "CacheManager | None", data_type: str, key: str, fetch_fn, lock: threading.Lock, stats: dict) -> dict:
        """
        Returns cached data if fresh, otherwise calls fetch_fn() and stores the result.
        Falls back transparently to a live fetch if caching is disabled or unavailable.
        """
        if cache is not None:
            try:
                cached = cache.get(data_type, key)
                with lock:
                    stats["hits"] += 1
                return cached
            except CacheMissError:
                pass

        result = fetch_fn()
        with lock:
            stats["misses"] += 1

        if cache is not None:
            try:
                cache.set(data_type, key, result)
            except Exception as e:
                # Caching is a best-effort optimization; never let a write failure
                # break data collection.
                context_logger_safe_warn(f"Failed to write cache for {data_type}/{key}: {e}")

        return result

    def _fetch_one(self, ticker: str, provider, cache, lock: threading.Lock, stats: dict) -> "tuple[str, dict | None, str | None]":
        """Fetches and normalizes all data for a single ticker. Returns (ticker, merged_dict_or_None, error_or_None)."""
        cache_key = _safe_cache_key(ticker)
        try:
            quote = self._get_cached_or_fetch(cache, "quotes", cache_key, lambda: provider.get_quote(ticker), lock, stats)
            inc = self._get_cached_or_fetch(cache, "financials", cache_key, lambda: provider.get_income_statement(ticker), lock, stats)
            bs = self._get_cached_or_fetch(cache, "balance_sheet", cache_key, lambda: provider.get_balance_sheet(ticker), lock, stats)
            cf = self._get_cached_or_fetch(cache, "cash_flow", cache_key, lambda: provider.get_cash_flow(ticker), lock, stats)

            current_price = quote.get("current_price")
            market_cap = quote.get("market_cap")

            # EPS
            eps = quote.get("trailing_eps")
            if not _is_valid(eps):
                if _is_valid(inc.get("Basic EPS")):
                    eps = inc["Basic EPS"]
                elif _is_valid(inc.get("Diluted EPS")):
                    eps = inc["Diluted EPS"]
                else:
                    eps = None

            # Shares Outstanding
            shares_outstanding = quote.get("shares_outstanding")
            shares_source = None
            if not _is_valid(shares_outstanding):
                if _is_valid(inc.get("Basic Average Shares")):
                    shares_outstanding = inc["Basic Average Shares"]
                    shares_source = "reported (income statement)"
                elif _is_valid(market_cap) and _is_valid(current_price) and current_price > 0:
                    shares_outstanding = market_cap / current_price
                    shares_source = "estimated (market_cap / price)"
                else:
                    shares_outstanding = None
                    shares_source = "missing"
            else:
                shares_source = "reported (quote)"

            # Payout Ratio
            payout_ratio = quote.get("payout_ratio")
            if not _is_valid(payout_ratio):
                payout_ratio = None

            # BVPS
            total_equity = bs.get("Total Equity Gross Minority Interest", bs.get("Stockholders Equity"))
            bvps = None
            if _is_valid(total_equity) and _is_valid(shares_outstanding) and shares_outstanding > 0:
                bvps = total_equity / shares_outstanding

            # FCF
            fcf = cf.get("Free Cash Flow")

            revenue = inc.get("Total Revenue")
            net_income = inc.get("Net Income")
            operating_income = inc.get("Operating Income")
            revenue_history = inc.get("revenue_history")

            total_assets = bs.get("Total Assets")
            current_liabilities = bs.get("Current Liabilities")
            total_debt = bs.get("Total Debt")

            minority_interest = bs.get("Minority Interest", 0.0)
            preferred_equity = bs.get("Preferred Stock", bs.get("Preferred Stock Equity", 0.0))
            cash_and_equivalents = bs.get("Cash And Cash Equivalents", bs.get("Cash", 0.0))

            # --- Quality gates: reject clearly bad values before they reach the engines ---
            price_validated, _ = DataValidator.validate_price(current_price if _is_valid(current_price) else None)
            pe_raw = quote.get("trailing_pe") or quote.get("forward_pe")
            pe_validated, _ = DataValidator.validate_pe(pe_raw if _is_valid(pe_raw) else None)
            roe_validated, _ = DataValidator.validate_roe(quote.get("roe") if _is_valid(quote.get("roe")) else None)

            merged = {
                "price": price_validated,
                "market_cap": market_cap,
                "eps": eps,
                "bvps": bvps,
                "fcf": fcf,
                "shares_outstanding": shares_outstanding,
                "shares_source": shares_source,
                "payout_ratio": payout_ratio,
                "dividend_yield": quote.get("dividend_yield"),
                "pe": pe_validated,
                "roe": roe_validated,

                "revenue": revenue,
                "revenue_history": revenue_history,
                "net_income": net_income,
                "operating_income": operating_income,
                "total_equity": total_equity,
                "total_assets": total_assets,
                "current_liabilities": current_liabilities,
                "total_debt": total_debt,
                "minority_interest": minority_interest,
                "preferred_equity": preferred_equity,
                "cash_and_equivalents": cash_and_equivalents,
                "sector": quote.get("sector"),
                "industry": quote.get("industry"),
                "beta": quote.get("beta"),
                "pb": quote.get("pb")
            }
            return ticker, merged, None

        except Exception as e:
            return ticker, None, str(e)

    def execute(self, context: ExecutionContext) -> bool:
        try:
            provider = ProviderRegistry.get_provider(context.provider_name)

            # Inject exchange suffix if available in config
            exchange = context.config.get("market", {}).get("exchange")
            if exchange and hasattr(provider, "exchange_suffix"):
                provider.exchange_suffix = exchange

            # Wire in the segmented cache (opt-out via config.cache.enabled: false)
            cache_config = context.config.get("cache", {})
            cache = None
            if cache_config.get("enabled", True):
                cache = CacheManager(base_dir=cache_config.get("dir", ".cache"))

            companies = context.artifacts.raw_companies
            total = len(companies)

            # Resolve thread count: explicit CLI flag > settings.yaml > 1 (safe default)
            threads = context.threads
            if not threads:
                threads = context.config.get("application", {}).get("threads", 1)
            threads = max(1, int(threads or 1))

            lock = threading.Lock()
            stats = {"hits": 0, "misses": 0}
            completed = 0

            with ThreadPoolExecutor(max_workers=threads) as executor:
                future_to_ticker = {}
                for comp in companies:
                    if not comp.ticker:
                        continue
                    future = executor.submit(self._fetch_one, comp.ticker, provider, cache, lock, stats)
                    future_to_ticker[future] = comp.ticker

                for future in as_completed(future_to_ticker):
                    ticker = future_to_ticker[future]
                    completed += 1
                    context.reporter.report_progress(f"Fetching {ticker} [{completed}/{total}]...")

                    ticker_result, merged, error = future.result()
                    if error is not None:
                        context.log(f"Failed to fetch {ticker_result}: {error}", Severity.WARNING)
                        continue

                    context.api_calls += 4
                    context.artifacts.market_data[ticker_result] = merged

            context.cache_hits += stats["hits"]
            context.cache_misses += stats["misses"]

            # Record Coverage Stats
            fields_to_track = ["price", "market_cap", "fcf", "pe", "roe"]
            coverage = {f: {"avail": 0, "miss": 0} for f in fields_to_track}
            for t, data in context.artifacts.market_data.items():
                for f in fields_to_track:
                    if data.get(f) is not None:
                        coverage[f]["avail"] += 1
                    else:
                        coverage[f]["miss"] += 1

            context.config["coverage"] = coverage
            context.log(
                f"Fetched data for {len(context.artifacts.market_data)} companies "
                f"({stats['hits']} cache hits, {stats['misses']} live fetches, {threads} thread(s)).",
                Severity.INFO
            )
            return True

        except Exception as e:
            context.log(f"Fatal error fetching data: {str(e)}", Severity.FATAL)
            return False

    def rollback(self, context: ExecutionContext) -> None:
        context.artifacts.market_data = {}


def context_logger_safe_warn(message: str) -> None:
    """Module-level fallback logger used inside closures that don't have direct context access."""
    from infrastructure.logging.logger import logger
    logger.warning(message)
