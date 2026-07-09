from pipeline.context import ExecutionContext, Severity
from pipeline.runner import PipelineStep
from domain.engines.valuation import ValuationEngine
from domain.engines.rule_parser import RuleParser


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
            config = dict(context.config.get("valuation", {}))

            # Model weights (dcf/relative_pe/graham/owner_earnings) live in
            # rules/valuation.yaml rather than settings.yaml, alongside the
            # other rule-versioned config (scoring.yaml, v4_0.yaml). Load them
            # the same way StepScoring loads rules/scoring.yaml, and fall back
            # to the engine's built-in defaults if the rule file is missing or
            # malformed so a config issue degrades gracefully instead of
            # failing the whole valuation step.
            try:
                parser = RuleParser()
                valuation_rules = parser.get_rules("valuation")
                weights = valuation_rules.get("policies", {}).get("weights")
                if weights:
                    config["weights"] = weights
            except (FileNotFoundError, ValueError) as e:
                context.log(f"Could not load rules/valuation.yaml weights, using engine defaults: {e}", Severity.WARNING)

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
