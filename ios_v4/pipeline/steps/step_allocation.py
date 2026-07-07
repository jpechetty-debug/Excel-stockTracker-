from pipeline.context import ExecutionContext, Severity
from pipeline.runner import PipelineStep
from domain.engines.allocation import AllocationEngine


class StepAllocation:
    
    @property
    def name(self) -> str:
        return "Allocation Engine (Constraints)"
        
    def validate(self, context: ExecutionContext) -> bool:
        if not context.artifacts.business_scores:
            context.log("No business scores available for allocation.", Severity.FATAL)
            return False
        return True
        
    def execute(self, context: ExecutionContext) -> bool:
        try:
            portfolio_config = context.config.get("portfolio", {})
            portfolio_size = portfolio_config.get("size", 1000000)
            engine = AllocationEngine(max_position_size=0.10, cash_floor=0.05, portfolio_size=portfolio_size)
            scores = context.artifacts.business_scores
            valuations = context.artifacts.valuations if hasattr(context.artifacts, "valuations") else {}
            
            allocations = engine.calculate_allocations(scores, valuations)
            context.artifacts.allocations = allocations
            
            context.log(f"Allocated portfolio targets for {len(allocations)} companies.", Severity.INFO)
            return True
            
        except Exception as e:
            context.log(f"Fatal error in Allocation Engine: {str(e)}", Severity.FATAL)
            return False
            
    def rollback(self, context: ExecutionContext) -> None:
        context.artifacts.allocations = {}
