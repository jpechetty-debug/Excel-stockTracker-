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
                    
                    # EPS
                    eps = None
                    if "Basic EPS" in inc:
                        eps = inc["Basic EPS"]
                    elif "Diluted EPS" in inc:
                        eps = inc["Diluted EPS"]
                        
                    # Shares Outstanding
                    shares_outstanding = None
                    if "Basic Average Shares" in inc:
                        shares_outstanding = inc["Basic Average Shares"]
                    elif market_cap and current_price:
                        shares_outstanding = market_cap / current_price
                        
                    # BVPS
                    total_equity = bs.get("Total Equity Gross Minority Interest", bs.get("Stockholders Equity"))
                    bvps = None
                    if total_equity and shares_outstanding:
                        bvps = total_equity / shares_outstanding
                        
                    # FCF
                    fcf = cf.get("Free Cash Flow")
                    
                    revenue = inc.get("Total Revenue")
                    net_income = inc.get("Net Income")
                    operating_income = inc.get("Operating Income")
                    
                    total_assets = bs.get("Total Assets")
                    current_liabilities = bs.get("Current Liabilities")
                    total_debt = bs.get("Total Debt")
                    
                    merged = {
                        "price": current_price,
                        "market_cap": market_cap,
                        "eps": eps,
                        "bvps": bvps,
                        "fcf": fcf,
                        "shares_outstanding": shares_outstanding,
                        "dividend_yield": quote.get("dividendYield"),
                        "pe": quote.get("trailing_pe") or quote.get("forward_pe"),
                        "roe": quote.get("roe"),
                        
                        "revenue": revenue,
                        "net_income": net_income,
                        "operating_income": operating_income,
                        "total_equity": total_equity,
                        "total_assets": total_assets,
                        "current_liabilities": current_liabilities,
                        "total_debt": total_debt
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
