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
            # NOTE: context.config is config_loader.settings (settings.yaml), which
            # only has portfolio.size - it does NOT contain max_position_size,
            # cash_target, or min_position_size. Those live in rules/v4_0.yaml's
            # 'allocation' section, loaded separately into config_loader.rules.
            # Reading from context.config here (as this used to) silently returns
            # {} for all of them, every run, regardless of what's configured.
            allocation_config = context.config_loader.rules.get("allocation", {})
            portfolio_size = context.config.get("portfolio", {}).get("size", 1000000.0)
            engine = AllocationEngine(
                max_position_size=allocation_config.get("max_position_size", 0.10),
                cash_floor=allocation_config.get("cash_target", 0.05),
                portfolio_size=allocation_config.get("portfolio_size", portfolio_size),
                min_position_size=allocation_config.get("min_position_size", 0.0)
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
