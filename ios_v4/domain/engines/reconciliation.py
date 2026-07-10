"""
Reconciliation Engine
Detects conflicts between the automated engine's fetched metrics (e.g. yfinance's
own returnOnEquity, which is a black-box TTM computation) and manually-researched,
cited figures in the 'Financial Data' sheet (screener.in, company filings, etc.).

These are two structurally different data pipelines computing the same metric,
and can legitimately diverge - different fiscal-period cutoffs, TTM vs annual
basis, or genuine data-quality issues on either side. A silent one-time copy-paste
fix doesn't help: the automated engine will just re-pull and overwrite on the
next run. This engine makes the conflict visible and durable instead.
"""
from datetime import datetime, timezone
from typing import Optional
from domain.models import EngineResult


class ReconciliationEngine:

    def __init__(self, variance_threshold: float = 0.15):
        # 15% relative variance - loose enough to tolerate normal TTM/FY noise,
        # tight enough to catch the ~20-40% mismatches that actually change a
        # valuation verdict (e.g. SBI 13.55% engine vs 18.57% researched).
        self.variance_threshold = variance_threshold

    def check_metric(self, metric_name: str, engine_value: Optional[float], reference_value: Optional[float],
                      rule_version: str = "v4.0") -> EngineResult:
        breakdown = {}
        reasons = []
        warnings = []

        if engine_value is None or reference_value is None:
            return EngineResult(
                value=None, confidence=0.0, breakdown=breakdown, reasons=reasons,
                method="Reconciliation: Cross-Source Variance Check", rule_version=rule_version,
                timestamp=datetime.now(timezone.utc),
                warnings=[f"Cannot reconcile {metric_name}: one or both sources missing."]
            )

        breakdown["engine_value"] = engine_value
        breakdown["reference_value"] = reference_value

        denom = max(abs(engine_value), abs(reference_value), 1e-9)
        variance = abs(engine_value - reference_value) / denom
        breakdown["variance_pct"] = variance * 100

        is_conflict = variance > self.variance_threshold
        if is_conflict:
            reasons.append(
                f"{metric_name} conflict: automated engine shows {engine_value:.2f}, "
                f"Financial Data sheet shows {reference_value:.2f} "
                f"({variance:.1%} relative variance, threshold {self.variance_threshold:.0%})."
            )
            warnings.append(
                f"Downstream valuation ({metric_name}-dependent) is unreliable until this is resolved."
            )
        else:
            reasons.append(f"{metric_name} matches within tolerance ({variance:.1%} variance).")

        return EngineResult(
            value=variance * 100,
            confidence=1.0,
            breakdown=breakdown,
            reasons=reasons,
            method="Reconciliation: Cross-Source Variance Check",
            rule_version=rule_version,
            timestamp=datetime.now(timezone.utc),
            warnings=warnings
        )
