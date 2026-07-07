"""
Progress Reporter
Owned by the pipeline to centrally manage progress logging.
"""

from infrastructure.logging.logger import logger


class ProgressReporter:
    """Handles centralized progress reporting."""
    
    def __init__(self, total_steps: int = 1):
        self.total_steps = total_steps
        self.current_step = 0
        
    def set_total_steps(self, total: int):
        self.total_steps = total
        
    def start_step(self, step_name: str):
        """Marks the start of a new step."""
        self.current_step += 1
        pct = int((self.current_step / max(1, self.total_steps)) * 100)
        
        # Simple progress bar
        bar_length = 20
        filled = int(bar_length * self.current_step // max(1, self.total_steps))
        bar = '█' * filled + '░' * (bar_length - filled)
        
        logger.info(f"\n{step_name}...")
        logger.info(f"{bar} {pct}%")

    def report_progress(self, message: str):
        """Reports intermediate progress without advancing the step counter."""
        logger.info(f"  -> {message}")
