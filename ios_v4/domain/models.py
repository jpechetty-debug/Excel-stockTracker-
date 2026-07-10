"""
Domain Models Module
Defines strongly typed dataclasses for core domain objects.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List

from decimal import Decimal

@dataclass(slots=True, frozen=True)
class EngineResult:
    """Explainable AI (XAI) output from calculation and decision engines."""
    value: Decimal | None
    confidence: float
    breakdown: Dict[str, Decimal]
    reasons: List[str]
    method: str
    rule_version: str
    timestamp: datetime
    warnings: List[str]


@dataclass(slots=True, frozen=True)
class Provenance:
    """Metadata regarding data origin and confidence."""
    source: str
    provider: str
    timestamp: datetime
    confidence: int
    rule_version: str
    calculation_version: str

@dataclass(slots=True, frozen=True)
class Metric:
    """A financial metric wrapping its value and provenance."""
    value: Decimal | str | None
    provenance: Provenance

@dataclass(slots=True, frozen=True)
class CompanyData:
    """Core domain model representing a single company's tracking data."""
    ticker: str
    company_name: str
    
    # System fields with provenance
    metrics: Dict[str, Metric] = field(default_factory=dict)
    
    # Manual fields (Strings that must not be blindly overwritten)
    manual_fields: Dict[str, str] = field(default_factory=dict)

    def get_metric_value(self, name: str) -> Decimal | str | None:
        """Helper to get a raw value if it exists."""
        if name in self.metrics:
            return self.metrics[name].value
        return None
