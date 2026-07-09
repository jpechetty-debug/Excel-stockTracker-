from pipeline.context import ExecutionContext, Severity
from pipeline.runner import PipelineStep
from domain.engines.rule_parser import RuleParser
from domain.engines.risk import RiskEngine


class StepRisk:
    
    @property
    def name(self) -> str:
        return "Risk Engine (Decomposition)"
        
    def validate(self, context: ExecutionContext) -> bool:
        if not context.artifacts.financials or not context.artifacts.valuations:
            context.log("Missing prerequisites for Risk Engine.", Severity.FATAL)
            return False
        return True
        
    def execute(self, context: ExecutionContext) -> bool:
        try:
            parser = RuleParser()
            engine = RiskEngine(parser)
            financials = context.artifacts.financials
            valuations = context.artifacts.valuations
            
            # Intersection of tickers that have both
            common_tickers = set(financials.keys()).intersection(set(valuations.keys()))
            
            existing_data = getattr(context.artifacts, 'existing_data', {}) or {}
            market_data = context.artifacts.market_data
            
            for ticker in common_tickers:
                try:
                    ed = existing_data.get(ticker, {})
                    md = market_data.get(ticker, {})
                    
                    industry = md.get("industry")
                    sector = md.get("sector")
                    gross_npa = ed.get("gross_npa")
                    net_npa = ed.get("net_npa")
                    car = ed.get("car")
                    pcr = ed.get("pcr")
                    
                    result = engine.compute_risk(
                        financials[ticker], 
                        valuations[ticker],
                        industry=industry,
                        sector=sector,
                        gross_npa=gross_npa,
                        net_npa=net_npa,
                        car=car,
                        pcr=pcr
                    )
                    context.artifacts.risks[ticker] = result
                    
                    if result.warnings:
                        context.log(f"[{ticker}] Risk warnings: {', '.join(result.warnings)}", Severity.WARNING)
                        
                except Exception as e:
                    context.log(f"[{ticker}] Risk calc failed: {str(e)}", Severity.WARNING)
                    
            context.log(f"Assessed risk for {len(context.artifacts.risks)} companies.", Severity.INFO)
            return True
            
        except Exception as e:
            context.log(f"Fatal error in Risk Engine: {str(e)}", Severity.FATAL)
            return False
            
    def rollback(self, context: ExecutionContext) -> None:
        context.artifacts.risks = {}
