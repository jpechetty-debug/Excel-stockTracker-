"""
Valuation Calculation Engine
Produces objective pricing facts (DCF, Relative P/E, Graham, Owner Earnings).
Strictly decoupled from Business Scoring.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from domain.models import EngineResult

# Base weights when all four models successfully return a value. Mirrors
# rules/valuation.yaml (policies.weights), which previously described this
# 4-model design but was never actually wired into the engine -- the engine
# ran DCF + Graham only, and blended them with an unweighted, unconditional
# average.
#
# That unconditional average was itself the source of a real calibration bug:
# the Graham Number (sqrt(22.5 * EPS * BVPS)) is a book-value-based formula.
# Benjamin Graham designed it for the stable, asset-heavy value stocks in his
# original screens; it has no way to recognize that a high-ROE, asset-light
# compounder (e.g. an RTA/IT-services business with a small balance sheet
# relative to its earnings power) is expensive because it's a great business,
# not because it's a value trap. Averaged 50/50 (or worse, given "graham"
# used to carry equal weight with "dcf" alone) into the blended intrinsic
# value, it single-handedly dragged Margin of Safety to figures like -2100%
# for names like CAMS, Persistent, and Cummins that were otherwise scoring
# 85-97 on Business Score.
#
# Adding two more models -- a book-value-free Relative P/E (Gordon Growth
# justified multiple) and a simpler single-stage Owner Earnings check -- and
# blending all four with configurable weights means no single model's blind
# spot can dominate the result the way an unconditional 2-model average did.
DEFAULT_WEIGHTS = {
    "dcf": 0.40,
    "relative_pe": 0.20,
    "graham": 0.20,
    "owner_earnings": 0.20,
}


class ValuationEngine:
    """Calculates objective intrinsic values."""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        configured_weights = self.config.get("weights") or {}
        self.weights = {**DEFAULT_WEIGHTS, **configured_weights}

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
        """Graham Number: sqrt(22.5 * EPS * BVPS).

        Book-value-based -- appropriate for asset-heavy value stocks, but
        structurally penalizes asset-light/high-ROE compounders with a low
        BVPS relative to earnings power. That's why this model's weight is
        capped at 20% by default rather than driving the blend alone; see
        calculate_relative_pe / calculate_owner_earnings_value for models
        that don't depend on book value.
        """
        if None in (eps, bvps) or eps <= 0 or bvps <= 0:
            return None
        return (22.5 * eps * bvps) ** 0.5

    def calculate_relative_pe(self, eps: float, payout_ratio: Optional[float], growth_rate: float, discount_rate: float) -> Optional[float]:
        """
        Justified P/E from fundamentals (Gordon Growth Model):
            fair_pe = payout_ratio / (discount_rate - growth_rate)
            value = eps * fair_pe

        Uses only earnings, payout policy, and growth -- no book value -- so
        unlike the Graham Number it doesn't read a low BVPS as "expensive"
        for a business that simply doesn't need much capital to compound.
        A conservative default payout of 25% is assumed when the company's
        actual payout ratio is missing or negative/garbage (common for
        growth companies that reinvest most earnings), rather than dropping
        the model entirely.
        """
        if eps is None or eps <= 0 or growth_rate is None or discount_rate is None:
            return None
        if discount_rate <= growth_rate:
            return None

        if payout_ratio is None or payout_ratio < 0 or payout_ratio > 1:
            payout_ratio = 0.25

        fair_pe = payout_ratio / (discount_rate - growth_rate)
        if fair_pe <= 0:
            return None
        return eps * fair_pe

    def calculate_owner_earnings_value(self, fcf: float, shares: float, growth_rate: float, discount_rate: float) -> Optional[float]:
        """
        Single-stage Gordon Growth valuation on owner earnings (approximated
        by Free Cash Flow per share): value = fcf_per_share * (1+g) / (r-g).

        Deliberately simpler than the explicit 5-year calculate_dcf (no
        multi-stage forecast, no separate terminal growth assumption) so it
        acts as an independent sanity check rather than a restatement of the
        same math with the same blind spots.
        """
        if None in (fcf, shares, growth_rate, discount_rate) or shares <= 0 or fcf <= 0:
            return None
        if discount_rate <= growth_rate:
            return None

        fcf_per_share = fcf / shares
        return fcf_per_share * (1 + growth_rate) / (discount_rate - growth_rate)

    def calculate_valuation(self, data: Dict[str, Any], current_price: float) -> EngineResult:
        """
        Takes financial facts and calculates a multi-model, weighted-blended
        intrinsic value from up to four independent models.
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
            reasons.append(f"Using SGR ({sgr:.1%}) for growth-dependent models (ROE: {roe:.1%}, Payout: {payout_ratio:.1%})")
        else:
            # Fallback (Using historical isn't strictly available in standard payload yet, falling back to 10%)
            # Future enhancement: use 3Y CAGR from historical financial endpoints
            growth_rate = 0.10
            reasons.append("Using default 10% growth for growth-dependent models (SGR unavailable)")

        # Apply caps
        original_growth = growth_rate
        growth_rate = max(min_growth, min(growth_rate, max_growth))
        if growth_rate != original_growth:
            reasons.append(f"Growth rate capped from {original_growth:.1%} to {growth_rate:.1%}")

        breakdown["growth_rate_used"] = growth_rate

        # calculate_relative_pe and calculate_owner_earnings_value are both
        # single-stage (perpetuity) Gordon Growth formulas, which require
        # growth_rate meaningfully below discount_rate to produce a sane,
        # stable result. growth_rate above is a near-term rate (SGR, capped
        # up to max_growth=25% by default) -- exactly the companies this fix
        # targets (high-ROE compounders) are the ones most likely to have
        # growth_rate > discount_rate, which would otherwise make both models
        # silently return None for precisely the businesses they're meant to
        # help. No real company grows at a high rate forever, so cap the rate
        # fed into these two perpetuity formulas to a sustainable spread below
        # the discount rate, the same way DCF already uses a separate, lower
        # terminal_growth for its own perpetuity stage.
        min_spread = dcf_config.get("min_perpetuity_spread", 0.02)
        perpetuity_growth_rate = min(growth_rate, discount_rate - min_spread)

        # 2. Run all four models independently.
        models: Dict[str, float] = {}

        dcf_val = self.calculate_dcf(fcf, growth_rate, discount_rate, terminal_growth, shares)
        if dcf_val is not None:
            breakdown["dcf_value"] = dcf_val
            models["dcf"] = dcf_val
            reasons.append(f"DCF Value computed at {dcf_val:.2f} (Assumptions: {discount_rate:.1%} discount, {terminal_growth:.1%} terminal)")
        else:
            warnings.append("Insufficient or invalid data for DCF valuation.")

        relative_pe_val = self.calculate_relative_pe(eps, payout_ratio, perpetuity_growth_rate, discount_rate)
        if relative_pe_val is not None:
            breakdown["relative_pe_value"] = relative_pe_val
            models["relative_pe"] = relative_pe_val
            reasons.append(f"Relative P/E Value computed at {relative_pe_val:.2f} (book-value-free, growth-based)")
        else:
            warnings.append("Insufficient or invalid data for Relative P/E valuation.")

        graham_val = self.calculate_graham(eps, bvps)
        if graham_val is not None:
            breakdown["graham_value"] = graham_val
            models["graham"] = graham_val
            reasons.append(f"Graham Value computed at {graham_val:.2f}")
        else:
            warnings.append("Insufficient or invalid data for Graham valuation.")

        owner_earnings_val = self.calculate_owner_earnings_value(fcf, shares, perpetuity_growth_rate, discount_rate)
        if owner_earnings_val is not None:
            breakdown["owner_earnings_value"] = owner_earnings_val
            models["owner_earnings"] = owner_earnings_val
            reasons.append(f"Owner Earnings Value computed at {owner_earnings_val:.2f}")
        else:
            warnings.append("Insufficient or invalid data for Owner Earnings valuation.")

        # 3. Weighted Blended Intrinsic Value.
        # Weights are renormalized over whichever models actually produced a
        # value, so a missing model dilutes nothing -- it's simply excluded,
        # and the remaining models keep their relative weight to each other.
        if models:
            total_weight = sum(self.weights.get(name, 0.0) for name in models)
            if total_weight > 0:
                blended_value = sum(models[name] * self.weights.get(name, 0.0) for name in models) / total_weight
            else:
                # All contributing models have zero configured weight (unusual
                # config) -- fall back to a simple average rather than divide by zero.
                blended_value = sum(models.values()) / len(models)
            model_summary = ", ".join(f"{name} ({self.weights.get(name, 0.0):.0%})" for name in models)
            reasons.append(f"Blended intrinsic value computed as {blended_value:.2f} using {len(models)} model(s): {model_summary}.")

            # Handle negative intrinsic values
            if blended_value <= 0:
                breakdown["intrinsic_value"] = None
                breakdown["buy_price"] = None
                reasons.append("Valuation not meaningful (blended intrinsic value <= 0).")
            else:
                breakdown["intrinsic_value"] = blended_value

                # 4. Margin of Safety and Buy Price
                mos_config = self.config.get("margin_of_safety", {})
                target_mos = mos_config.get("default", 0.20)

                if current_price and current_price > 0:
                    mos = (blended_value - current_price) / blended_value
                    breakdown["margin_of_safety"] = mos
                    reasons.append(f"Margin of Safety computed at {mos:.1%}")
                    # Keep the precise mos value for scoring (don't clamp the number
                    # that feeds RiskEngine/InvestmentEngine), but add a readable
                    # bucket for anyone consuming the report directly, since a
                    # four-digit percentage (e.g. -2109%) carries no extra decision
                    # value over "Extremely Overvalued" for a human reader.
                    if mos >= 0.20:
                        mos_bucket = "Undervalued"
                    elif mos >= 0:
                        mos_bucket = "Fair Value"
                    elif mos >= -0.50:
                        mos_bucket = "Overvalued"
                    else:
                        mos_bucket = "Extremely Overvalued"
                    breakdown["margin_of_safety_bucket"] = mos_bucket

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
        if models and blended_value <= 0:
            valuation_status = "Negative Blended Value (all available models <= 0)"
        elif not models:
            # Distinguish "we had nothing to work with" from "we had some
            # inputs but every model rejected them" (e.g. negative EPS).
            any_input_present = any(v is not None for v in (eps, bvps, fcf, shares, roe, payout_ratio))
            valuation_status = "Invalid Inputs" if any_input_present else "Missing Inputs"

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

        confidence = len(models) / len(DEFAULT_WEIGHTS)

        return EngineResult(
            value=blended_value,
            confidence=min(confidence, 1.0),
            breakdown=breakdown,
            reasons=reasons,
            method="Multi-Model Weighted Blend (DCF, Relative P/E, Graham, Owner Earnings)",
            rule_version="val_v2",
            timestamp=datetime.now(),
            warnings=warnings
        )
