import math
from pipeline.context import ExecutionContext, Severity
from pipeline.runner import PipelineStep
from infrastructure.providers.registry import ProviderRegistry


class StepFetchData:
    
    @property
    def name(self) -> str:
        return "Fetch Market Data (Batch)"
        
    def validate(self, context: ExecutionContext) -> bool:
        if not context.artifacts.raw_companies:
            context.log("No companies loaded. Skipping fetch.", Severity.WARNING)
            return False
        return True
        
    def execute(self, context: ExecutionContext) -> bool:
        try:
            provider = ProviderRegistry.get_provider(context.provider_name)
            
            # Inject exchange suffix if available in config
            exchange = context.config.get("market", {}).get("exchange")
            if exchange and hasattr(provider, "exchange_suffix"):
                provider.exchange_suffix = exchange
            
            companies = context.artifacts.raw_companies
            total = len(companies)
            
            # We'll need some basic mapping for yfinance fields
            for idx, comp in enumerate(companies):
                ticker = comp.ticker
                if not ticker:
                    continue
                    
                context.reporter.report_progress(f"Fetching {ticker} [{idx+1}/{total}]...")
                
                try:
                    quote = provider.get_quote(ticker)
                    inc = provider.get_income_statement(ticker)
                    bs = provider.get_balance_sheet(ticker)
                    cf = provider.get_cash_flow(ticker)
                    
                    # Safely extract values (yfinance keys can vary)
                    current_price = quote.get("current_price")
                    market_cap = quote.get("market_cap")
                    
                    # Helper to check nan
                    def is_valid(val):
                        if val is None:
                            return False
                        if isinstance(val, float) and math.isnan(val):
                            return False
                        return True

                    # EPS
                    eps = quote.get("trailing_eps")
                    if not is_valid(eps):
                        if is_valid(inc.get("Basic EPS")):
                            eps = inc["Basic EPS"]
                        elif is_valid(inc.get("Diluted EPS")):
                            eps = inc["Diluted EPS"]
                        else:
                            eps = None
                            
                    # Shares Outstanding
                    shares_outstanding = quote.get("shares_outstanding")
                    shares_source = None
                    if not is_valid(shares_outstanding):
                        if is_valid(inc.get("Basic Average Shares")):
                            shares_outstanding = inc["Basic Average Shares"]
                            shares_source = "reported (income statement)"
                        elif is_valid(market_cap) and is_valid(current_price) and current_price > 0:
                            shares_outstanding = market_cap / current_price
                            shares_source = "estimated (market_cap / price)"
                        else:
                            shares_outstanding = None
                            shares_source = "missing"
                    else:
                        shares_source = "reported (quote)"
                            
                    # Payout Ratio
                    payout_ratio = quote.get("payout_ratio")
                    if not is_valid(payout_ratio):
                        payout_ratio = None

                    # BVPS
                    total_equity = bs.get("Total Equity Gross Minority Interest", bs.get("Stockholders Equity"))
                    bvps = None
                    if is_valid(total_equity) and is_valid(shares_outstanding) and shares_outstanding > 0:
                        bvps = total_equity / shares_outstanding
                        
                    # FCF
                    fcf = cf.get("Free Cash Flow")
                    
                    revenue = inc.get("Total Revenue")
                    net_income = inc.get("Net Income")
                    operating_income = inc.get("Operating Income")
                    
                    total_assets = bs.get("Total Assets")
                    current_liabilities = bs.get("Current Liabilities")
                    total_debt = bs.get("Total Debt")
                    
                    minority_interest = bs.get("Minority Interest", 0.0)
                    preferred_equity = bs.get("Preferred Stock", bs.get("Preferred Stock Equity", 0.0))
                    cash_and_equivalents = bs.get("Cash And Cash Equivalents", bs.get("Cash", 0.0))
                    
                    merged = {
                        "price": current_price,
                        "market_cap": market_cap,
                        "eps": eps,
                        "bvps": bvps,
                        "fcf": fcf,
                        "shares_outstanding": shares_outstanding,
                        "shares_source": shares_source,
                        "payout_ratio": payout_ratio,
                        "dividend_yield": quote.get("dividendYield"),
                        "pe": quote.get("trailing_pe") or quote.get("forward_pe"),
                        "roe": quote.get("roe"),
                        
                        "revenue": revenue,
                        "net_income": net_income,
                        "operating_income": operating_income,
                        "total_equity": total_equity,
                        "total_assets": total_assets,
                        "current_liabilities": current_liabilities,
                        "total_debt": total_debt,
                        "minority_interest": minority_interest,
                        "preferred_equity": preferred_equity,
                        "cash_and_equivalents": cash_and_equivalents
                    }
                    
                    context.api_calls += 4
                    context.artifacts.market_data[ticker] = merged
                    
                except Exception as e:
                    context.log(f"Failed to fetch {ticker}: {str(e)}", Severity.WARNING)
                    # We continue on WARNING
                    
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
            context.log(f"Fetched data for {len(context.artifacts.market_data)} companies.", Severity.INFO)
            return True
            
        except Exception as e:
            context.log(f"Fatal error fetching data: {str(e)}", Severity.FATAL)
            return False
            
    def rollback(self, context: ExecutionContext) -> None:
        context.artifacts.market_data = {}
