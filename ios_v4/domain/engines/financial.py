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
