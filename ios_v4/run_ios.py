import argparse
import sys
from pipeline.context import ExecutionContext
from pipeline.runner import PipelineRunner
from pipeline.steps.step_load_config import StepLoadConfig
from pipeline.steps.step_open_workbook import StepOpenWorkbook
from pipeline.steps.step_fetch_data import StepFetchData
from pipeline.steps.step_financial import StepFinancial
from pipeline.steps.step_valuation import StepValuation
from pipeline.steps.step_scoring import StepScoring
from pipeline.steps.step_risk import StepRisk
from pipeline.steps.step_investment import StepInvestment
from pipeline.steps.step_allocation import StepAllocation
from pipeline.steps.step_reconcile import StepReconcile
from pipeline.steps.step_write_excel import StepWriteExcel
from pipeline.steps.step_validate_workbook import StepValidateWorkbook
from pipeline.steps.step_reports import StepReports
from pipeline.steps.step_summary_llm import StepSummaryLLM
import infrastructure.providers.yfinance_provider
import infrastructure.providers.mock_provider


def main():
    parser = argparse.ArgumentParser(description="IOS v4.0 Institutional Operating System")
    parser.add_argument("--input", type=str, help="Master workbook path")
    parser.add_argument("--output", type=str, help="Output workbook path")
    parser.add_argument("--provider", type=str, default="yfinance", help="Market data provider")
    parser.add_argument("--dry-run", action="store_true", help="Execute without modifying the original workbook")
    parser.add_argument("--log-level", type=str, default="INFO", help="Logging level")
    parser.add_argument("--threads", type=int, default=None, help="Number of concurrent fetch threads (default: from config, or 1)")
    parser.add_argument("--limit", type=int, help="Limit to N companies for testing")
    parser.add_argument("--tickers", type=str, help="Comma-separated list of tickers to run")
    
    args = parser.parse_args()
    tickers_list = args.tickers.split(",") if args.tickers else None
    
    context = ExecutionContext(
        provider_name=args.provider,
        is_dry_run=args.dry_run,
        input_file=args.input,
        output_file=args.output,
        limit=args.limit,
        tickers=tickers_list,
        threads=args.threads
    )
    
    runner = PipelineRunner()
    
    # Register Steps Explicitly
    runner.add_step(StepLoadConfig())
    runner.add_step(StepOpenWorkbook())
    runner.add_step(StepFetchData())
    runner.add_step(StepFinancial())
    runner.add_step(StepValuation())
    runner.add_step(StepScoring())
    runner.add_step(StepRisk())
    runner.add_step(StepInvestment())
    runner.add_step(StepAllocation())
    runner.add_step(StepReconcile())
    runner.add_step(StepWriteExcel())
    runner.add_step(StepValidateWorkbook())
    runner.add_step(StepReports())
    runner.add_step(StepSummaryLLM())
    
    final_context = runner.run(context)
    
    if final_context.state.name == "FAILED":
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
