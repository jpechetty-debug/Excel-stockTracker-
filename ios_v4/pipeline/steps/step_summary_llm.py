import json
import os
from pathlib import Path
from pipeline.context import ExecutionContext, Severity
from pipeline.runner import PipelineStep

try:
    from pixelprompt import PixelPrompt, RenderConfig, optimize_prompt
    from anthropic import Anthropic
    HAS_LLM_DEPS = True
except ImportError:
    HAS_LLM_DEPS = False


class StepSummaryLLM:
    
    @property
    def name(self) -> str:
        return "LLM Pipeline Summary Assistant"
        
    def validate(self, context: ExecutionContext) -> bool:
        if not HAS_LLM_DEPS:
            context.log("pixelprompt or anthropic not installed. Skipping LLM summary.", Severity.WARNING)
        return True
        
    def execute(self, context: ExecutionContext) -> bool:
        if not HAS_LLM_DEPS:
            return True
            
        try:
            reports_dir = Path("reports")
            run_file = reports_dir / "run_summary.json"
            
            if not run_file.exists():
                context.log("run_summary.json not found, skipping LLM summary", Severity.WARNING)
                return True
                
            with open(run_file, "r", encoding="utf-8") as f:
                json_data = f.read()
                
            api_key = context.config.get("llm", {}).get("anthropic_api_key") or os.environ.get("ANTHROPIC_API_KEY")
            
            if not api_key:
                context.log("No Anthropic API key found in config or env. Skipping LLM summary.", Severity.WARNING)
                return True
                
            context.log("Rendering JSON to images using PixelPrompt...", Severity.INFO)
            pxl = PixelPrompt(RenderConfig.for_content("json"))
            images = pxl.render(json_data)
            
            context.log(f"Calling Anthropic API with {len(images)} compressed image(s)...", Severity.INFO)
            client = Anthropic(api_key=api_key)
            
            prompt_text = "Based on this run summary, provide a brief natural language summary of the portfolio changes, highlighting the most significant valuation shifts, the total coverage, and recommended actions."
            optimized_prompt = optimize_prompt(prompt_text, style="structured")
            
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            *[img.to_content_block() for img in images],
                            {
                                "type": "text",
                                "text": optimized_prompt
                            }
                        ]
                    }
                ]
            )
            
            summary_text = response.content[0].text
            out_file = reports_dir / "llm_summary.md"
            with open(out_file, "w", encoding="utf-8") as f:
                f.write("# IOS Pipeline LLM Summary\n\n")
                f.write(summary_text)
                
            context.log(f"LLM summary generated at {out_file}", Severity.INFO)
            return True
            
        except Exception as e:
            context.log(f"Failed to generate LLM summary: {str(e)}", Severity.WARNING)
            # We return True because an LLM failure shouldn't fail the whole pipeline
            return True
            
    def rollback(self, context: ExecutionContext) -> None:
        pass
