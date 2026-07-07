import json
from pathlib import Path
from datetime import datetime
from pipeline.context import ExecutionContext, Severity
from pipeline.runner import PipelineStep

class StepReports:
    
    @property
    def name(self) -> str:
        return "Generate Run Summary"
        
    def validate(self, context: ExecutionContext) -> bool:
        return True
        
    def execute(self, context: ExecutionContext) -> bool:
        try:
            reports_dir = Path("reports")
            reports_dir.mkdir(exist_ok=True)
            
            run_file = reports_dir / "run_summary.json"
            
            coverage = context.config.get("coverage", {})
            
            summary = {
                "timestamp": datetime.now().isoformat(),
                "status": context.state.name,
                "provider": context.provider_name,
                "dry_run": context.is_dry_run,
                "input_file": context.input_file or context.config.get("excel", {}).get("master_file"),
                "metrics": {
                    "total_companies_loaded": len(context.artifacts.raw_companies),
                    "total_companies_fetched": len(context.artifacts.market_data),
                    "api_calls": context.api_calls,
                },
                "coverage": coverage,
                "artifacts_produced": [
                    "workbook_diff.csv",
                    "run_summary.json"
                ],
                "timing_ms": context.step_timings
            }
            
            with open(run_file, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=4)
                
            context.log(f"Run summary generated at {run_file}", Severity.INFO)
            
            # Print coverage report to terminal
            if coverage:
                print("\n--- Provider Coverage Report ---")
                print(f"{'Metric':<20} | {'Available':<10} | {'Missing':<10}")
                print("-" * 46)
                for f, stats in coverage.items():
                    print(f"{f:<20} | {stats['avail']:<10} | {stats['miss']:<10}")
                print("--------------------------------\n")
            
            return True
            
        except Exception as e:
            context.log(f"Failed to generate reports: {str(e)}", Severity.ERROR)
            return False
            
    def rollback(self, context: ExecutionContext) -> None:
        pass
