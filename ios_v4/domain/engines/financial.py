"""
Financial Calculation Engine
Produces objective facts regarding business quality (Growth, Margins, Return on Capital).
Strictly completely decoupled from Price and Scoring.
"""

from typing import Dict, Any, Optional, List
from decimal import Decimal
from datetime import datetime, timezone
from domain.models import EngineResult


class FinancialEngine:
    """Calculates objective financial quality metrics."""
    
    @staticmethod
    def _safe_divide(num: Decimal, den: Decimal) -> Optional[Decimal]:
        if den is None or num is None or den == Decimal('0'):
            return None
        return num / den

    @staticmethod
    def calculate_cagr(start_val: Decimal, end_val: Decimal, years: Decimal) -> Optional[Decimal]:
        """Calculates Compound Annual Growth Rate."""
        if not start_val or not end_val or start_val <= 0 or end_val <= 0 or years <= 0:
            return None
        return Decimal(str(float(end_val / start_val) ** float(Decimal('1') / Decimal(str(years))) - 1))

    @staticmethod
    def _revenue_cagr_from_history(revenue_history: Optional[List[Dict[str, Any]]]) -> "tuple[Optional[Decimal], Optional[str]]":
        """
        Computes revenue CAGR from a list of {date, value} entries (oldest to newest).
        Returns (cagr, warning_message). warning_message is None on success.
        """
        if not revenue_history or len(revenue_history) < 2:
            return None, "Revenue history unavailable or too short; CAGR not calculated."

        # Entries are pre-sorted oldest -> newest by the provider, but sort defensively.
        ordered = sorted(revenue_history, key=lambda item: item["date"])
        start_entry, end_entry = ordered[0], ordered[-1]

        try:
            start_date = datetime.fromisoformat(str(start_entry["date"]))
            end_date = datetime.fromisoformat(str(end_entry["date"]))
            years = (end_date - start_date).days / 365.25
        except (ValueError, TypeError, KeyError):
            # Fall back to assuming one reporting period per year if dates are unparsable.
            years = len(ordered) - 1

        if years <= 0:
            return None, "Revenue history spans zero or negative years; CAGR not calculated."

        cagr = FinancialEngine.calculate_cagr(start_entry["value"], end_entry["value"], years)
        if cagr is None:
            return None, "Revenue history present but CAGR inputs were invalid (non-positive revenue)."
        return cagr, None


    def calculate_metrics(self, data: Dict[str, Any]) -> EngineResult:
        """
        Takes raw standardized company financial data and calculates quality metrics.
        Returns an EngineResult.
        """
        breakdown = {}
        reasons = []
        warnings = []
        
        # 1. Margins
        revenue = data.get("revenue")
        net_income = data.get("net_income")
        operating_income = data.get("operating_income")
        
        net_margin = self._safe_divide(net_income, revenue)
        if net_margin is not None:
            breakdown["net_margin"] = net_margin
            reasons.append(f"Net Margin calculated at {net_margin:.1%}")
            
        op_margin = self._safe_divide(operating_income, revenue)
        if op_margin is not None:
            breakdown["operating_margin"] = op_margin
            reasons.append(f"Operating Margin calculated at {op_margin:.1%}")

        # 2. Return on Capital
        equity = data.get("total_equity")
        total_assets = data.get("total_assets")
        current_liabilities = data.get("current_liabilities")
        
        roe = self._safe_divide(net_income, equity)
        if roe is not None:
            breakdown["roe"] = roe
            reasons.append(f"ROE calculated at {roe:.1%}")
            
        if operating_income and total_assets and current_liabilities:
            capital_employed = total_assets - current_liabilities
            roce = self._safe_divide(operating_income, capital_employed)
            if roce is not None:
                breakdown["roce"] = roce
                reasons.append(f"ROCE calculated at {roce:.1%}")

        # 3. Debt Health
        total_debt = data.get("total_debt")
        debt_to_equity = self._safe_divide(total_debt, equity)
        if debt_to_equity is not None:
            breakdown["debt_to_equity"] = debt_to_equity
            reasons.append(f"Debt to Equity calculated at {debt_to_equity:.2f}x")

        # 4. Enterprise Value & Yields
        market_cap = data.get("market_cap")
        minority_interest = data.get("minority_interest", Decimal('0'))
        preferred_equity = data.get("preferred_equity", Decimal('0'))
        cash = data.get("cash_and_equivalents", Decimal('0'))
        fcf = data.get("fcf")
        
        enterprise_value = None
        if market_cap is not None:
            total_debt_val = total_debt or Decimal('0')
            minority_interest = minority_interest or Decimal('0')
            preferred_equity = preferred_equity or Decimal('0')
            cash = cash or Decimal('0')
            enterprise_value = market_cap + total_debt_val + minority_interest + preferred_equity - cash

        if enterprise_value is not None:
            if operating_income and operating_income > Decimal('0'):
                ev_ebit = enterprise_value / operating_income
                breakdown["ev_ebit"] = ev_ebit
                reasons.append(f"EV/EBIT calculated at {ev_ebit:.2f}x (using full Enterprise Value)")
            else:
                warnings.append("Operating income (EBIT) is non-positive or missing; skipping EV/EBIT.")
                
            if fcf is not None:
                fcf_yield = fcf / enterprise_value
                breakdown["fcf_yield"] = fcf_yield
                reasons.append(f"FCF Yield (Enterprise) calculated at {fcf_yield:.1%}")
        else:
            warnings.append("Insufficient data to calculate Enterprise Value.")
            
        # 5. Additional Metrics
        if fcf is not None and revenue and revenue > Decimal('0'):
            fcf_margin = fcf / revenue
            breakdown["fcf_margin"] = fcf_margin
            reasons.append(f"FCF Margin calculated at {fcf_margin:.1%}")
            
        if fcf is not None and net_income and net_income > Decimal('0'):
            fcf_conversion = fcf / net_income
            # Bound conversion between 0 and 1 as requested
            fcf_conversion = max(Decimal('0'), min(fcf_conversion, Decimal('1')))
            breakdown["fcf_conversion"] = fcf_conversion
            reasons.append(f"FCF Conversion calculated at {fcf_conversion:.1%} (bounded 0-1)")
            
        eps = data.get("eps")
        current_price = data.get("price")
        if eps is not None and current_price and current_price > Decimal('0'):
            earnings_yield = eps / current_price
            breakdown["earnings_yield"] = earnings_yield
            reasons.append(f"Earnings Yield calculated at {earnings_yield:.1%}")

        # Revenue CAGR (real calculation using multi-year revenue history when available)
        revenue_history = data.get("revenue_history")
        cagr, cagr_warning = self._revenue_cagr_from_history(revenue_history)
        if cagr is not None:
            breakdown["revenue_cagr_3y"] = cagr
            years_covered = len(revenue_history) - 1 if revenue_history else 0
            reasons.append(f"Revenue CAGR calculated at {cagr:.1%} across {years_covered} year(s) of reported history")
        else:
            warnings.append(cagr_warning or "Revenue CAGR could not be calculated.")

        confidence = 1.0 if len(breakdown) >= 5 else (len(breakdown) / 5)
        
        return EngineResult(
            value=0.0, # Not applicable for FinancialEngine (returns breakdown)
            confidence=confidence,
            breakdown=breakdown,
            reasons=reasons,
            method="Standard Financial Calculation",
            rule_version="core_v1",
            timestamp=datetime.now(timezone.utc),
            warnings=warnings
        )
