from pathlib import Path
from pipeline.context import ExecutionContext, Severity
from pipeline.runner import PipelineStep
from infrastructure.excel.reader import ExcelReader
import os


class StepOpenWorkbook:
    
    @property
    def name(self) -> str:
        return "Open Workbook & Load Companies"
        
    def validate(self, context: ExecutionContext) -> bool:
        if not context.config.get("excel", {}).get("master_file"):
            context.log("Missing master_file in configuration.", Severity.FATAL)
            return False
        return True
        
    def execute(self, context: ExecutionContext) -> bool:
        try:
            master_file = context.config.get("excel", {}).get("master_file")
            if not master_file:
                context.log("Master file not specified in configuration.", Severity.FATAL)
                return False
                
            if not os.path.exists(master_file):
                context.log(f"Master workbook not found: {master_file}", Severity.FATAL)
                return False
                
            reader = ExcelReader(context.config_loader)
            companies, existing_data = reader.read_companies(
                filepath=master_file,
                limit=context.limit,
                tickers=context.tickers
            )
            
            context.artifacts.raw_companies = companies
            context.artifacts.existing_data = existing_data
            context.log(f"Opened workbook: {master_file} and extracted {len(companies)} companies.", Severity.INFO)
            return True
            
        except Exception as e:
            context.log(f"Failed to open workbook: {str(e)}", Severity.FATAL)
            return False
            
    def rollback(self, context: ExecutionContext) -> None:
        context.artifacts.raw_companies = []
