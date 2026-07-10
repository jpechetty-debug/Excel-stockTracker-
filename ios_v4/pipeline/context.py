"""
Pipeline Context
Contains the ExecutionContext passed through every pipeline step.
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from domain.models import EngineResult
from infrastructure.logging.logger import logger
from pipeline.reporter import ProgressReporter


class PipelineState(Enum):
    NOT_STARTED = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    SKIPPED = auto()


class Severity(Enum):
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    FATAL = auto()


@dataclass
class PipelineArtifacts:
    """Stores all intermediate domain outputs."""
    raw_companies: List[Dict[str, Any]] = field(default_factory=list)
    market_data: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    financials: Dict[str, EngineResult] = field(default_factory=dict)
    valuations: Dict[str, EngineResult] = field(default_factory=dict)
    business_scores: Dict[str, EngineResult] = field(default_factory=dict)
    risks: Dict[str, EngineResult] = field(default_factory=dict)
    investment_scores: Dict[str, EngineResult] = field(default_factory=dict)
    allocations: Dict[str, EngineResult] = field(default_factory=dict)
    reconciliation: Dict[str, EngineResult] = field(default_factory=dict)
    existing_data: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    final_output_path: Optional[str] = None


@dataclass
class ExecutionContext:
    """The singular context object passed to every pipeline step."""
    
    # Core Services
    config: Dict[str, Any] = field(default_factory=dict)
    provider_name: str = "yfinance"
    is_dry_run: bool = False
    input_file: Optional[str] = None
    output_file: Optional[str] = None
    limit: Optional[int] = None
    tickers: Optional[List[str]] = None
    config_loader: Any = None
    threads: Optional[int] = None
    
    # State & Reporting
    state: PipelineState = PipelineState.NOT_STARTED
    reporter: ProgressReporter = field(default_factory=ProgressReporter)
    
    # Artifacts (Instead of floating variables)
    artifacts: PipelineArtifacts = field(default_factory=PipelineArtifacts)
    
    # Metrics
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    step_timings: Dict[str, float] = field(default_factory=dict)
    api_calls: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    
    def log(self, message: str, severity: Severity = Severity.INFO):
        """Standardized logging with severity handling."""
        if severity == Severity.INFO:
            logger.info(message)
        elif severity == Severity.WARNING:
            logger.warning(message)
        elif severity == Severity.ERROR:
            logger.error(message)
        elif severity == Severity.FATAL:
            logger.critical(message)
            self.state = PipelineState.FAILED
