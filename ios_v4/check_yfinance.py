import json
from infrastructure.providers.yfinance_provider import YFinanceProvider

provider = YFinanceProvider()
provider.exchange_suffix = ".NS" # Or just pass SBIN.NS directly

quote = provider.get_quote("SBIN.NS")
print(json.dumps({
    "sector": quote.get("sector"),
    "industry": quote.get("industry")
}))
