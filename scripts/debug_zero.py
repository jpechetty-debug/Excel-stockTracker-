"""
Ad-hoc debug script used while investigating a zeroed-out metrics bug.
Moved out of the ios_v4/ package (was in ios_v4/scratch/) so it no longer
ships as part of the installable application. Run with:
    python scripts/debug_zero.py
from the repository root.
"""
import sys
from pathlib import Path

# Allow running this script directly from the repo root without installing
# ios_v4 as a package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ios_v4"))

import yaml
from infrastructure.providers.yfinance_provider import YFinanceProvider
from domain.engines.financial import FinancialEngine
from domain.engines.scoring import ScoringEngine

def main():
    ticker = "LT.NS"
    provider = YFinanceProvider()
    print(f"Fetching data for {ticker}...")
    quote = provider.get_quote(ticker)
    inc = provider.get_income_statement(ticker)
    bal = provider.get_balance_sheet(ticker)
    cf = provider.get_cash_flow(ticker)
    
    # Just mock the pipeline step fetch_data behavior
    def is_valid(val):
        if val is None:
            return False
        if isinstance(val, float) and val != val: # Check for NaN
            return False
        return True
        
    current_price = quote.get("current_price")
    market_cap = quote.get("market_cap")
    
    total_debt = bal.get("Total Debt")
    if not is_valid(total_debt):
        total_debt = bal.get("Ordinary Shares Number", 0) # Fallback? No, debt is debt.
        
    stockholders_equity = bal.get("Stockholders Equity")
    debt_to_equity = None
    if is_valid(total_debt) and is_valid(stockholders_equity) and stockholders_equity > 0:
        debt_to_equity = total_debt / stockholders_equity

    ebit = inc.get("EBIT")
    capital_employed = None
    if is_valid(total_debt) and is_valid(stockholders_equity):
        capital_employed = total_debt + stockholders_equity
    roce = None
    if is_valid(ebit) and is_valid(capital_employed) and capital_employed > 0:
        roce = ebit / capital_employed
        
    shares_outstanding = quote.get("shares_outstanding")
    if not is_valid(shares_outstanding):
        shares_outstanding = inc.get("Basic Average Shares")
        
    market_data = {
        "price": current_price,
        "market_cap": market_cap,
        "total_debt": total_debt,
        "stockholders_equity": stockholders_equity,
        "debt_to_equity": debt_to_equity,
        "ebit": ebit,
        "capital_employed": capital_employed,
        "roce": roce,
        "shares_outstanding": shares_outstanding
    }
    
    print("Market Data parsed:")
    for k, v in market_data.items():
        print(f"  {k}: {v}")
    
    # Financial engine
    financial_engine = FinancialEngine()
    fin_result = financial_engine.calculate_metrics(market_data)
    
    print("\n--- Financial Metrics ---")
    for k, v in fin_result.breakdown.items():
        print(f"{k}: {v}")
        
    print("\n--- Financial Warnings ---")
    for w in fin_result.reasons:
        print(w)
        
    # Scoring engine
    rules_path = Path(__file__).resolve().parent.parent / "ios_v4" / "rules" / "scoring.yaml"
    with open(rules_path, "r", encoding="utf-8") as f:
        scoring_config = yaml.safe_load(f)
        
    class DummyParser:
        def __init__(self, config):
            self.config = config
        def get_rules(self, cat):
            return self.config.get("rules", {})
        def get_rule_version(self, cat):
            return "1.0"
            
    parser = DummyParser(scoring_config)
    scoring_engine = ScoringEngine(parser)
    score_result = scoring_engine.compute_business_score(fin_result)
    
    print("\n--- Scoring Result ---")
    print(f"Score: {score_result.value}")
    print(f"Confidence: {score_result.confidence}")
    print("\nBreakdown:")
    for k, v in score_result.breakdown.items():
        print(f"{k}: {v}")
    print("\nReasons:")
    for r in score_result.reasons:
        print(r)

if __name__ == "__main__":
    main()
