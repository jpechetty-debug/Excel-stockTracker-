from pipeline.context import ExecutionContext, Severity
from pipeline.runner import PipelineStep
from domain.engines.valuation import ValuationEngine


class StepValuation:
    
    @property
    def name(self) -> str:
        return "Valuation Engine (Pricing Facts)"
        
    def validate(self, context: ExecutionContext) -> bool:
        # Valuation relies on financial facts. If financial is empty, we can still
        # try if market_data exists, but typically we want at least market_data.
        if not context.artifacts.market_data:
            context.log("No market data available for valuation engine.", Severity.FATAL)
            return False
        return True
        
    def execute(self, context: ExecutionContext) -> bool:
        try:
            config = context.config.get("valuation", {})
            engine = ValuationEngine(config)
            market_data = context.artifacts.market_data
            
            for ticker, data in market_data.items():
                try:
                    current_price = data.get("price", 0.0)
                    result = engine.calculate_valuation(data, current_price)
                    context.artifacts.valuations[ticker] = result
                    
                    if result.warnings:
                        context.log(f"[{ticker}] Valuation warnings: {', '.join(result.warnings)}", Severity.WARNING)
                        
                except Exception as e:
                    context.log(f"[{ticker}] Valuation calc failed: {str(e)}", Severity.WARNING)
                    
            context.log(f"Computed valuation facts for {len(context.artifacts.valuations)} companies.", Severity.INFO)
            return True
            
        except Exception as e:
            context.log(f"Fatal error in Valuation Engine: {str(e)}", Severity.FATAL)
            return False
            
    def rollback(self, context: ExecutionContext) -> None:
        context.artifacts.valuations = {}
