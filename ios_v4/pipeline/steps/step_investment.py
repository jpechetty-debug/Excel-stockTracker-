from pipeline.context import ExecutionContext, Severity
from pipeline.runner import PipelineStep
from domain.engines.investment import InvestmentEngine


class StepInvestment:
    
    @property
    def name(self) -> str:
        return "Investment Engine (Orthogonal Synthesis)"
        
    def validate(self, context: ExecutionContext) -> bool:
        if not context.artifacts.business_scores:
            context.log("No business scores available. Investment Engine requires quality.", Severity.FATAL)
            return False
        return True
        
    def execute(self, context: ExecutionContext) -> bool:
        try:
            engine = InvestmentEngine()
            business_scores = context.artifacts.business_scores
            valuations = context.artifacts.valuations
            risks = context.artifacts.risks
            
            for ticker, b_res in business_scores.items():
                try:
                    v_res = valuations.get(ticker)
                    r_res = risks.get(ticker)
                    
                    result = engine.compute_investment_score(b_res, v_res, r_res)
                    
                    if not hasattr(context.artifacts, 'investment_scores'):
                        context.artifacts.investment_scores = {}
                    context.artifacts.investment_scores[ticker] = result
                    
                    if result.warnings:
                        context.log(f"[{ticker}] Investment Score warnings: {', '.join(result.warnings)}", Severity.WARNING)
                        
                except Exception as e:
                    context.log(f"[{ticker}] Investment Score failed: {str(e)}", Severity.WARNING)
                    
            if hasattr(context.artifacts, 'investment_scores'):
                context.log(f"Calculated investment scores for {len(context.artifacts.investment_scores)} companies.", Severity.INFO)
            return True
            
        except Exception as e:
            context.log(f"Fatal error in Investment Engine: {str(e)}", Severity.FATAL)
            return False
            
    def rollback(self, context: ExecutionContext) -> None:
        if hasattr(context.artifacts, 'investment_scores'):
            context.artifacts.investment_scores = {}
