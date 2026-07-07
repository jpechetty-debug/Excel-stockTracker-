from pathlib import Path
from pipeline.context import ExecutionContext, Severity
from pipeline.runner import PipelineStep
from infrastructure.excel.writer import ExcelWriter
from infrastructure.excel.planner import UpdatePlanner
from domain.models import Metric, Provenance
from datetime import datetime


class StepWriteExcel:
    
    @property
    def name(self) -> str:
        return "Write Output to Excel"
        
    def validate(self, context: ExecutionContext) -> bool:
        if not context.artifacts.raw_companies:
            context.log("No companies to write.", Severity.WARNING)
            return False
        return True
        
    def execute(self, context: ExecutionContext) -> bool:
        try:
            excel_config = context.config.get("excel", {})
            master_file = excel_config.get("master_file", "IOS_Master_Tracker_v4.xlsx")
            
            output_file = context.output_file or master_file
            if context.is_dry_run:
                path = Path(master_file)
                output_file = f"{path.stem}_DRYRUN{path.suffix}"
                context.log(f"Dry-run enabled. Modifying copy: {output_file}", Severity.INFO)
                
            companies = context.artifacts.raw_companies
            
            # Map all artifacts into company metrics
            for company in companies:
                ticker = company.ticker
                
                prov_default = Provenance(
                    source="Pipeline",
                    provider=context.provider_name,
                    timestamp=datetime.now(),
                    confidence=1.0,
                    rule_version=context.config.get("rules", {}).get("active_version", "v4.0"),
                    calculation_version="direct"
                )
                
                # Market Data mapping
                if ticker in context.artifacts.market_data:
                    mdata = context.artifacts.market_data[ticker]
                    for k, v in mdata.items():
                        company.metrics[k] = Metric(value=v, provenance=prov_default)
                        
                # Financial Engine mapping
                if ticker in context.artifacts.financials:
                    res = context.artifacts.financials[ticker]
                    prov = prov_default  # We could construct a specific provenance from EngineResult
                    for k, v in res.breakdown.items():
                        company.metrics[k] = Metric(value=v, provenance=prov)
                        
                # Valuation Engine mapping
                if ticker in context.artifacts.valuations:
                    res = context.artifacts.valuations[ticker]
                    prov = prov_default
                    for k, v in res.breakdown.items():
                        company.metrics[k] = Metric(value=v, provenance=prov)

                # Scoring Engine mapping
                if ticker in context.artifacts.business_scores:
                    res = context.artifacts.business_scores[ticker]
                    prov = prov_default
                    company.metrics["business_score"] = Metric(value=res.value, provenance=prov)

                # Risk Engine mapping
                if ticker in context.artifacts.risks:
                    res = context.artifacts.risks[ticker]
                    prov = prov_default
                    company.metrics["investment_score"] = Metric(value=res.value, provenance=prov)

                # Allocation Engine mapping
                if ticker in context.artifacts.allocations:
                    res = context.artifacts.allocations[ticker]
                    prov = prov_default
                    company.metrics["target_allocation"] = Metric(value=res.breakdown.get("target_allocation"), provenance=prov)
                    company.metrics["portfolio_weight"] = Metric(value=res.breakdown.get("portfolio_weight"), provenance=prov)
            
            # Run Update Planner
            planner = UpdatePlanner(context.config_loader)
            plan = planner.create_plan(companies, context.artifacts.existing_data)
            
            context.log(f"Update Planner created {len(plan.actions)} actions.", Severity.INFO)
            
            # Run Writer
            reports_dir = Path("reports")
            writer = ExcelWriter(context.config_loader)
            writer.update_workbook(
                filepath=master_file,
                plan=plan,
                output_path=output_file,
                reports_dir=reports_dir
            )
            
            context.log(f"Workbook successfully saved to {output_file}", Severity.INFO)
            return True
            
        except Exception as e:
            context.log(f"Failed to write Excel: {str(e)}", Severity.FATAL)
            return False
            
    def rollback(self, context: ExecutionContext) -> None:
        pass
