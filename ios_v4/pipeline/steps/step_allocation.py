from pipeline.context import ExecutionContext, Severity
from pipeline.runner import PipelineStep
from domain.engines.allocation import AllocationEngine


class StepAllocation:
    
    @property
    def name(self) -> str:
        return "Allocation Engine (Constraints)"
        
    def validate(self, context: ExecutionContext) -> bool:
        if not hasattr(context.artifacts, 'investment_scores') or not context.artifacts.investment_scores:
            context.log("No investment scores available for allocation engine.", Severity.FATAL)
            return False
        return True
        
    def execute(self, context: ExecutionContext) -> bool:
        try:
            portfolio_config = context.config.get("portfolio", {})
            engine = AllocationEngine(
                max_position_size=portfolio_config.get("max_position_size", 0.10),
                cash_floor=portfolio_config.get("cash_floor", 0.05),
                portfolio_size=portfolio_config.get("portfolio_size", 1000000.0)
            )
            
            investment_scores = context.artifacts.investment_scores
            
            allocations = engine.calculate_allocations(investment_scores)
            
            context.artifacts.allocations = allocations
            
            context.log(f"Allocated portfolio targets for {len(allocations)} companies.", Severity.INFO)
            return True
            
        except Exception as e:
            context.log(f"Fatal error in Allocation Engine: {str(e)}", Severity.FATAL)
            return False
            
    def rollback(self, context: ExecutionContext) -> None:
        context.artifacts.allocations = {}
