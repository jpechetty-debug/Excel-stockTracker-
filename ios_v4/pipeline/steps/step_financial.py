from pipeline.context import ExecutionContext, Severity
from pipeline.runner import PipelineStep
from domain.engines.financial import FinancialEngine


class StepFinancial:
    
    @property
    def name(self) -> str:
        return "Financial Engine (Objective Facts)"
        
    def validate(self, context: ExecutionContext) -> bool:
        if not context.artifacts.market_data:
            context.log("No market data available for financial engine.", Severity.FATAL)
            return False
        return True
        
    def execute(self, context: ExecutionContext) -> bool:
        try:
            engine = FinancialEngine()
            market_data = context.artifacts.market_data
            
            for ticker, data in market_data.items():
                try:
                    result = engine.calculate_metrics(data)
                    context.artifacts.financials[ticker] = result
                    
                    if result.warnings:
                        context.log(f"[{ticker}] Financial Engine warnings: {', '.join(result.warnings)}", Severity.WARNING)
                        
                except Exception as e:
                    context.log(f"[{ticker}] Financial calc failed: {str(e)}", Severity.WARNING)
                    
            context.log(f"Computed financial facts for {len(context.artifacts.financials)} companies.", Severity.INFO)
            return True
            
        except Exception as e:
            context.log(f"Fatal error in Financial Engine: {str(e)}", Severity.FATAL)
            return False
            
    def rollback(self, context: ExecutionContext) -> None:
        context.artifacts.financials = {}
