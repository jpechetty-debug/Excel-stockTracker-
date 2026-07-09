"""
Risk Engine
Decomposes risk into distinct testable dimensions.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from domain.models import EngineResult
from domain.engines.rule_parser import RuleParser

BANKING_INDUSTRIES = {
    "Banks",
    "Private Bank",
    "Public Bank",
    "Financial Services",
    "NBFC",
    "Housing Finance",
    "Insurance"
}

def _interpolate_gnpa(gnpa: float) -> float:
    if gnpa < 1.0: return 0.0
    if gnpa <= 2.0: return 0.0 + (gnpa - 1.0) * 20.0
    if gnpa <= 3.0: return 20.0 + (gnpa - 2.0) * 20.0
    if gnpa <= 4.0: return 40.0 + (gnpa - 3.0) * 30.0
    if gnpa <= 5.0: return 70.0 + (gnpa - 4.0) * 30.0
    return 100.0

def _interpolate_car(car: float) -> float:
    if car >= 18.0: return 0.0
    if car >= 16.0: return 0.0 + (18.0 - car) * 10.0
    if car >= 14.0: return 20.0 + (16.0 - car) * 15.0
    if car >= 12.0: return 50.0 + (14.0 - car) * 15.0
    if car >= 11.5: return 80.0 + (12.0 - car) * 40.0
    return 100.0


class RiskEngine:
    """Calculates risk across Business, Financial, Valuation, Market, and Liquidity dimensions."""
    
    def __init__(self, rule_parser: RuleParser):
        self.rule_parser = rule_parser

    def compute_risk(self, financial_result: EngineResult, valuation_result: EngineResult,
                     industry: Optional[str] = None, sector: Optional[str] = None,
                     gross_npa: Optional[float] = None, net_npa: Optional[float] = None, 
                     car: Optional[float] = None, pcr: Optional[float] = None) -> EngineResult:
        """
        Calculates a dimensional risk score. Higher score = Higher Risk.
        """
        rules = self.rule_parser.get_rules("scoring")
        version = self.rule_parser.get_rule_version("scoring")
        
        breakdown = {}
        reasons = []
        warnings = []
        
        # Initialize components (for transparency/debugging as requested)
        business_risk = None
        financial_risk = None
        valuation_risk = None
        governance_risk = None
        
        # Financial Risk
        f_metrics = financial_result.breakdown
        dte = f_metrics.get("debt_to_equity")
        
        is_bank = False
        # Broad string match across industry and sector
        for val in (industry, sector):
            if val:
                val_lower = val.lower()
                if any(k in val_lower for k in ["bank", "financial", "nbfc", "housing finance", "insurance", "credit", "loan"]):
                    is_bank = True
                    break
        
        if is_bank:
            reasons.append(f"Matched banking/financials (industry='{industry}', sector='{sector}'). Using GNPA/CAR risk model.")
            
            npa_risk = None
            car_risk = None
            
            if gross_npa is not None:
                npa_risk = _interpolate_gnpa(gross_npa)
                reasons.append(f"Gross NPA {gross_npa:.2f}% -> {npa_risk:.1f} risk")
            else:
                warnings.append("Missing Gross NPA % for banking model.")
                
            if car is not None:
                car_risk = _interpolate_car(car)
                reasons.append(f"CAR {car:.2f}% -> {car_risk:.1f} risk")
            else:
                warnings.append("Missing CAR % for banking model.")
                
            if npa_risk is not None and car_risk is not None:
                financial_risk = (npa_risk * 0.60) + (car_risk * 0.40)
            elif npa_risk is not None:
                financial_risk = npa_risk
            elif car_risk is not None:
                financial_risk = car_risk
            else:
                financial_risk = 40.0
                warnings.append("No banking metrics available. Defaulting Financial Risk to 40.")
                
        else:
            if dte is not None:
                financial_risk = min(dte * 100, 100)
                reasons.append(f"Financial risk driven by D/E of {dte:.2f}x")
            else:
                financial_risk = 40.0
                warnings.append("Missing D/E for standard model. Defaulting Financial Risk to 40.")

        breakdown["financial_risk"] = financial_risk

        # Other risk components are currently placeholders for future models.
        # Valuation Risk is excluded intentionally to avoid double-counting.
        # Business Risk and Governance Risk will be implemented in future iterations.
        
        # Total Risk (For now, only driven by Financial Risk)
        total_risk = financial_risk
        breakdown["total_risk"] = total_risk
        breakdown["business_risk"] = business_risk
        breakdown["valuation_risk"] = valuation_risk
        breakdown["governance_risk"] = governance_risk
        
        # Prorating is no longer necessary as Financial Risk handles its own defaults and is the only active dimension.
        final_risk = total_risk
        confidence = min(financial_result.confidence, valuation_result.confidence)

        return EngineResult(
            value=final_risk,
            confidence=confidence,
            breakdown=breakdown,
            reasons=reasons,
            method="Dimensional Risk Decomposition",
            rule_version=version,
            timestamp=datetime.now(),
            warnings=warnings
        )
