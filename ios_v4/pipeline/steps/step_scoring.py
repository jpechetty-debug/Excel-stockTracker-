from pipeline.context import ExecutionContext, Severity
from pipeline.runner import PipelineStep
from domain.engines.rule_parser import RuleParser
from domain.engines.scoring import ScoringEngine


class StepScoring:
    
    @property
    def name(self) -> str:
        return "Scoring Engine (Investment Policy)"
        
    def validate(self, context: ExecutionContext) -> bool:
        if not context.artifacts.financials:
            context.log("No financial facts available for scoring.", Severity.FATAL)
            return False
        return True
        
    def execute(self, context: ExecutionContext) -> bool:
        try:
            parser = RuleParser()
            engine = ScoringEngine(parser)
            financials = context.artifacts.financials
            
            for ticker, fin_result in financials.items():
                try:
                    result = engine.compute_business_score(fin_result)
                    context.artifacts.business_scores[ticker] = result
                    
                    if result.warnings:
                        context.log(f"[{ticker}] Scoring warnings: {', '.join(result.warnings)}", Severity.WARNING)
                        
                except Exception as e:
                    context.log(f"[{ticker}] Scoring failed: {str(e)}", Severity.WARNING)
                    
            context.log(f"Scored {len(context.artifacts.business_scores)} companies.", Severity.INFO)
            return True
            
        except Exception as e:
            context.log(f"Fatal error in Scoring Engine: {str(e)}", Severity.FATAL)
            return False
            
    def rollback(self, context: ExecutionContext) -> None:
        context.artifacts.business_scores = {}
