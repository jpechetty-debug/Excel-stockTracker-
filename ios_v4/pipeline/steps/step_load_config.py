from pipeline.context import ExecutionContext, Severity
from pipeline.runner import PipelineStep
from config.config_loader import ConfigLoader


class StepLoadConfig:
    
    @property
    def name(self) -> str:
        return "Load Configuration"
        
    def validate(self, context: ExecutionContext) -> bool:
        return True
        
    def execute(self, context: ExecutionContext) -> bool:
        try:
            context.reporter.report_progress("Parsing configuration files...")
            
            config_loader = ConfigLoader()
            context.config_loader = config_loader
            context.config = config_loader.settings
            
            # Allow CLI to override master file
            if context.input_file:
                if "excel" not in context.config:
                    context.config["excel"] = {}
                context.config["excel"]["master_file"] = context.input_file
                
            context.log(f"Configuration loaded. Provider: {context.provider_name}", Severity.INFO)
            return True
            
        except Exception as e:
            context.log(f"Failed to load config: {str(e)}", Severity.FATAL)
            return False
            
    def rollback(self, context: ExecutionContext) -> None:
        context.config = {}
