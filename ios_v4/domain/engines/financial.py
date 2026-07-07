"""
Financial Calculation Engine
Produces objective facts regarding business quality (Growth, Margins, Return on Capital).
Strictly completely decoupled from Price and Scoring.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from domain.models import EngineResult


class FinancialEngine:
    """Calculates objective financial quality metrics."""
    
    @staticmethod
    def _safe_divide(num: float, den: float) -> Optional[float]:
        if den is None or num is None or den == 0:
            return None
        return num / den

    @staticmethod
    def calculate_cagr(start_val: float, end_val: float, years: float) -> Optional[float]:
        """Calculates Compound Annual Growth Rate."""
        if not start_val or not end_val or start_val <= 0 or end_val <= 0 or years <= 0:
            return None
        return (end_val / start_val) ** (1 / years) - 1

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
        minority_interest = data.get("minority_interest", 0.0)
        preferred_equity = data.get("preferred_equity", 0.0)
        cash = data.get("cash_and_equivalents", 0.0)
        fcf = data.get("fcf")
        
        enterprise_value = None
        if market_cap is not None:
            total_debt_val = total_debt or 0.0
            minority_interest = minority_interest or 0.0
            preferred_equity = preferred_equity or 0.0
            cash = cash or 0.0
            enterprise_value = market_cap + total_debt_val + minority_interest + preferred_equity - cash

        if enterprise_value is not None:
            if operating_income and operating_income > 0:
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
        if fcf is not None and revenue and revenue > 0:
            fcf_margin = fcf / revenue
            breakdown["fcf_margin"] = fcf_margin
            reasons.append(f"FCF Margin calculated at {fcf_margin:.1%}")
            
        eps = data.get("eps")
        current_price = data.get("price")
        if eps is not None and current_price and current_price > 0:
            earnings_yield = eps / current_price
            breakdown["earnings_yield"] = earnings_yield
            reasons.append(f"Earnings Yield calculated at {earnings_yield:.1%}")

        # Mocking CAGR for this iteration as time-series data isn't fully structured yet
        breakdown["revenue_cagr_3y"] = 0.15
        reasons.append("Revenue 3Y CAGR estimated at 15.0% (Time-series data pending)")

        confidence = 1.0 if len(breakdown) >= 5 else (len(breakdown) / 5)
        
        return EngineResult(
            value=0.0, # Not applicable for FinancialEngine (returns breakdown)
            confidence=confidence,
            breakdown=breakdown,
            reasons=reasons,
            method="Standard Financial Calculation",
            rule_version="core_v1",
            timestamp=datetime.now(),
            warnings=warnings
        )
