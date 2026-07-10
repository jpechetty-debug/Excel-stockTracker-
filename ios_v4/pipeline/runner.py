"""
Pipeline Runner and Step Protocol
"""

import time
from typing import Protocol, List
from datetime import datetime, timezone
from pipeline.context import ExecutionContext, PipelineState, Severity
from infrastructure.logging.logger import logger


class PipelineStep(Protocol):
    """The contract that every pipeline step must implement."""
    
    @property
    def name(self) -> str:
        """Name of the step."""
        ...
        
    def execute(self, context: ExecutionContext) -> bool:
        """Execute the step. Returns True if successful, False if FATAL."""
        ...
        
    def validate(self, context: ExecutionContext) -> bool:
        """Validate state before or after execution."""
        ...
        
    def rollback(self, context: ExecutionContext) -> None:
        """Rollback in case of failure."""
        ...


class PipelineRunner:
    """Orchestrates PipelineStep execution."""
    
    def __init__(self):
        self.steps: List[PipelineStep] = []
        
    def add_step(self, step: PipelineStep):
        self.steps.append(step)
        
    def run(self, context: ExecutionContext) -> ExecutionContext:
        """Executes all registered steps."""
        context.state = PipelineState.RUNNING
        context.start_time = datetime.now(timezone.utc)
        context.reporter.set_total_steps(len(self.steps))
        
        logger.info("Starting IOS v4.0 Pipeline...")
        
        for step in self.steps:
            if context.state == PipelineState.FAILED:
                logger.critical(f"Pipeline in FAILED state. Skipping {step.name}.")
                continue
                
            context.reporter.start_step(step.name)
            
            step_start = time.perf_counter()
            try:
                # Validation
                if not step.validate(context):
                    context.log(f"Validation failed for {step.name}", Severity.FATAL)
                    break
                    
                # Execution
                success = step.execute(context)
                
                if not success:
                    context.log(f"Execution failed for {step.name}", Severity.FATAL)
                    step.rollback(context)
                    break
                    
            except Exception as e:
                context.log(f"Unhandled exception in {step.name}: {str(e)}", Severity.FATAL)
                step.rollback(context)
                break
            finally:
                step_end = time.perf_counter()
                elapsed = step_end - step_start
                context.step_timings[step.name] = elapsed
                logger.debug(f"{step.name} completed in {elapsed:.3f}s")
                
        context.end_time = datetime.now(timezone.utc)
        
        if context.state != PipelineState.FAILED:
            context.state = PipelineState.COMPLETED
            logger.info("\nPipeline Completed Successfully.")
        else:
            logger.critical("\nPipeline Failed.")
            
        return context
