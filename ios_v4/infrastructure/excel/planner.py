"""
Update Planner Module
Acts as a firewall between calculation engines and physical Excel I/O.
Determines what should be updated and records provenance and statuses.
"""

from typing import List, Dict, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from config.config_loader import ConfigLoader
from domain.models import CompanyData


class UpdateStatus(Enum):
    UPDATED = auto()
    UNCHANGED = auto()
    SKIPPED_NONE = auto()
    SKIPPED_MANUAL = auto()
    SKIPPED_VALIDATION = auto()
    FAILED = auto()


@dataclass
class UpdateAction:
    ticker: str
    field: str
    old_value: Any
    new_value: Any
    status: UpdateStatus
    reason: str
    provider: str
    confidence: float
    method: str
    rule_version: str
    timestamp: datetime


@dataclass
class WorkbookUpdatePlan:
    actions: List[UpdateAction] = field(default_factory=list)
    
    def get_action_count(self, status: UpdateStatus) -> int:
        return sum(1 for a in self.actions if a.status == status)


class UpdatePlanner:
    """Creates a deterministic plan of updates without modifying the workbook."""
    
    def __init__(self, config: ConfigLoader):
        self.config = config
        self.allowed_columns: Set[str] = set()
        system_zones = config.column_map.get("zones", {}).get("system", [])
        for item in system_zones:
            if "column" in item and "field" in item:
                self.allowed_columns.add(item["field"])

    def create_plan(self, companies: List[CompanyData], existing_data: Dict[str, Dict[str, Any]]) -> WorkbookUpdatePlan:
        """
        existing_data: A mapping of Ticker -> { field_name -> old_value }
        companies: The CompanyData objects populated with computed metrics.
        """
        plan = WorkbookUpdatePlan()
        
        for company in companies:
            ticker = company.ticker
            current_row = existing_data.get(ticker, {})
            
            for field, metric in company.metrics.items():
                old_val = current_row.get(field)
                new_val = metric.value
                
                # Default provenance attributes
                prov = metric.provenance
                provider = prov.provider if prov else "System"
                conf = prov.confidence if prov else 1.0
                method = prov.calculation_version if prov else "Direct"
                rule_ver = prov.rule_version if prov else "v4.0"
                
                # Soft-Fail Policy Enforcement
                if new_val is None:
                    # Allow clearing cell if it's a valuation metric and valuation calculation is invalid/negative,
                    # or if the old value is negative.
                    is_valuation_field = field in ("intrinsic_value", "buy_price", "margin_of_safety")
                    val_status_metric = company.metrics.get("valuation_status")
                    val_status = val_status_metric.value if val_status_metric else None
                    
                    if old_val is not None and (
                        (is_valuation_field and val_status in ("Negative FCF / DCF Invalid", "Invalid Inputs")) or
                        (isinstance(old_val, (int, float)) and old_val < 0)
                    ):
                        status = UpdateStatus.UPDATED
                        reason = "Clear negative/invalid valuation"
                    else:
                        status = UpdateStatus.SKIPPED_NONE
                        reason = "Field not provided by provider or calculation impossible"
                elif field not in self.allowed_columns:
                    status = UpdateStatus.SKIPPED_MANUAL
                    reason = "Field is not in System Zone"
                elif str(old_val) == str(new_val):
                    status = UpdateStatus.UNCHANGED
                    reason = "Values are identical"
                else:
                    status = UpdateStatus.UPDATED
                    reason = "Update approved"
                    
                plan.actions.append(UpdateAction(
                    ticker=ticker,
                    field=field,
                    old_value=old_val,
                    new_value=new_val,
                    status=status,
                    reason=reason,
                    provider=provider,
                    confidence=conf,
                    method=method,
                    rule_version=rule_ver,
                    timestamp=datetime.now()
                ))
                
        return plan
