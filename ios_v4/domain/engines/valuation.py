"""
Valuation Calculation Engine
Produces objective pricing facts (DCF, Graham, Margin of Safety).
Strictly decoupled from Business Scoring.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from domain.models import EngineResult

class ValuationEngine:
    """Calculates objective intrinsic values."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    @staticmethod
    def _safe_divide(num: float, den: float) -> Optional[float]:
        if den is None or num is None or den == 0:
            return None
        return num / den

    def calculate_dcf(self, fcf: float, growth_rate: float, discount_rate: float, terminal_growth: float, shares: float) -> Optional[float]:
        """Simplified 5-year DCF using explicit growth and terminal rates."""
        if None in (fcf, growth_rate, discount_rate, terminal_growth, shares) or shares == 0:
            return None
            
        if discount_rate <= terminal_growth:
            # Invalid parameters for Gordon Growth Model
            return None
        
        # Simplified Terminal Value math
        value = 0
        current_fcf = fcf
        for i in range(1, 6):
            current_fcf *= (1 + growth_rate)
            value += current_fcf / ((1 + discount_rate) ** i)
            
        terminal_value = (current_fcf * (1 + terminal_growth)) / (discount_rate - terminal_growth)
        value += terminal_value / ((1 + discount_rate) ** 5)
        
        return value / shares

    def calculate_graham(self, eps: float, bvps: float) -> Optional[float]:
        """Graham Number: sqrt(22.5 * EPS * BVPS)"""
        if None in (eps, bvps) or eps <= 0 or bvps <= 0:
            return None
        return (22.5 * eps * bvps) ** 0.5

    def calculate_valuation(self, data: Dict[str, Any], current_price: float) -> EngineResult:
        """
        Takes financial facts and calculates a multi-model intrinsic value.
        """
        breakdown = {}
        reasons = []
        warnings = []
        
        eps = data.get("eps")
        bvps = data.get("bvps")
        fcf = data.get("fcf")
        shares = data.get("shares_outstanding")
        
        # 1. Growth Rate Determination
        dcf_config = self.config.get("dcf", {})
        min_growth = dcf_config.get("min_growth", 0.05)
        max_growth = dcf_config.get("max_growth", 0.25)
        discount_rate = dcf_config.get("discount_rate", 0.11)
        terminal_growth = dcf_config.get("terminal_growth", 0.045)
        
        roe = data.get("roe")
        payout_ratio = data.get("payout_ratio")
        
        growth_rate = None
        sgr = None
        if roe is not None and payout_ratio is not None:
            sgr = roe * (1 - payout_ratio)
            
        if sgr is not None:
            growth_rate = sgr
            reasons.append(f"Using SGR ({sgr:.1%}) for DCF growth (ROE: {roe:.1%}, Payout: {payout_ratio:.1%})")
        else:
            # Fallback (Using historical isn't strictly available in standard payload yet, falling back to 10%)
            # Future enhancement: use 3Y CAGR from historical financial endpoints
            growth_rate = 0.10
            reasons.append("Using default 10% for DCF growth (SGR unavailable)")
            
        # Apply caps
        original_growth = growth_rate
        growth_rate = max(min_growth, min(growth_rate, max_growth))
        if growth_rate != original_growth:
            reasons.append(f"Growth rate capped from {original_growth:.1%} to {growth_rate:.1%}")
            
        breakdown["growth_rate_used"] = growth_rate
        
        # 2. DCF
        dcf_val = self.calculate_dcf(fcf, growth_rate, discount_rate, terminal_growth, shares)
        if dcf_val:
            breakdown["dcf_value"] = dcf_val
            reasons.append(f"DCF Value computed at {dcf_val:.2f} (Assumptions: {discount_rate:.1%} discount, {terminal_growth:.1%} terminal)")
        else:
            warnings.append("Insufficient or invalid data for DCF valuation.")

        # 2. Graham Value
        graham_val = self.calculate_graham(eps, bvps)
        if graham_val:
            breakdown["graham_value"] = graham_val
            reasons.append(f"Graham Value computed at {graham_val:.2f}")

        # 3. Blended Intrinsic Value
        # Using simple equal weights for available models
        available_models = [v for k, v in breakdown.items() if "value" in k]
        if available_models:
            blended_value = sum(available_models) / len(available_models)
            reasons.append(f"Blended intrinsic value computed as {blended_value:.2f} using {len(available_models)} models.")
            
            # Handle negative intrinsic values
            if blended_value <= 0:
                breakdown["intrinsic_value"] = None
                breakdown["buy_price"] = None
                reasons.append("Valuation not meaningful (intrinsic value <= 0).")
            else:
                breakdown["intrinsic_value"] = blended_value
                
                # 4. Margin of Safety and Buy Price
                mos_config = self.config.get("margin_of_safety", {})
                target_mos = mos_config.get("default", 0.20)
                
                if current_price and current_price > 0:
                    mos = (blended_value - current_price) / blended_value
                    breakdown["margin_of_safety"] = mos
                    reasons.append(f"Margin of Safety computed at {mos:.1%}")
                    
                buy_price = blended_value * (1 - target_mos)
                breakdown["buy_price"] = buy_price
                reasons.append(f"Buy Price calculated at {buy_price:.2f} (Target MoS: {target_mos:.1%})")
                
                # 5. Implied / Justified P/E
                if eps and eps > 0:
                    justified_pe = blended_value / eps
                    breakdown["justified_pe"] = justified_pe
                    reasons.append(f"Implied P/E from Intrinsic Value computed at {justified_pe:.2f}x")
                
        else:
            blended_value = 0.0
            warnings.append("No valuation models could be calculated.")
            
        # Determine Valuation Status
        valuation_status = "OK"
        if available_models and blended_value <= 0:
            valuation_status = "Negative FCF / DCF Invalid"
        elif not shares or not eps or not bvps or fcf is None:
            valuation_status = "Missing Inputs"
        elif not available_models:
            valuation_status = "Invalid Inputs"
            
        # Expose reasons for missing EV/EBIT
        market_cap = data.get("market_cap")
        total_debt = data.get("total_debt")
        operating_income = data.get("operating_income")
        
        ev_issues = []
        if market_cap is None:
            ev_issues.append("No Market Cap")
        if total_debt is None:
            ev_issues.append("No Debt")
        if not operating_income or operating_income <= 0:
            ev_issues.append("EBIT <= 0")
            
        if ev_issues:
            if valuation_status == "OK":
                valuation_status = f"Missing EV/EBIT ({', '.join(ev_issues)})"
            else:
                valuation_status += f" | Missing EV/EBIT ({', '.join(ev_issues)})"
                
        breakdown["valuation_status"] = valuation_status
            
        # 6. EPS Implied
        pe = data.get("pe")
        if current_price and current_price > 0 and pe and pe > 0:
            eps_implied = current_price / pe
            breakdown["eps_implied"] = eps_implied
            reasons.append(f"EPS Implied computed at {eps_implied:.2f}")

        confidence = len(available_models) / 3.0 # Assuming 3 models max
        
        return EngineResult(
            value=blended_value,
            confidence=min(confidence, 1.0),
            breakdown=breakdown,
            reasons=reasons,
            method="Multi-Model Blended",
            rule_version="val_v1",
            timestamp=datetime.now(),
            warnings=warnings
        )
