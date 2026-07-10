"""
Step: Recalculate Workbook

Why this exists:
Master Universe intentionally keeps several columns as live Excel formulas
(Target Allocation %, Position Size, and historically Margin of Safety / EPS
Implied / Justified P/E before those were literal-ized) rather than one-off
computed values, so a human opening the file in Excel always sees them
recalculate automatically if they tweak Dashboard assumptions or an Evidence
Gate flag by hand. That's a deliberate design choice, not a bug.

The catch: openpyxl (what this pipeline uses to write the file) does not
evaluate formulas - it only stores the formula string. Any cell like that has
no cached result until some real spreadsheet engine opens the file at least
once. Read it back with openpyxl using data_only=True before that happens and
every formula cell silently returns None, not an error - which looks exactly
like missing/broken data to any downstream Python tool (StepValidateWorkbook,
verify_output.py, or a human running their own audit script) even though the
formula is completely correct and would show the right value instantly in
Excel.

This step closes that gap the moment the pipeline itself writes the file, by
shelling out to LibreOffice headless to force a recalculation pass and
resaving, so every consumer downstream - including our own validator that
runs right after this step - sees real cached values, not None.

Non-fatal by design: if LibreOffice isn't installed in this environment, we
log a clear warning and continue. The workbook is still completely correct
for a human opening it in Excel; only automated Python-side reads of the
formula columns are affected until it's recalculated by *something*.
"""
import shutil
import subprocess
from pathlib import Path
from pipeline.context import ExecutionContext, Severity
from pipeline.runner import PipelineStep


class StepRecalculateWorkbook:

    @property
    def name(self) -> str:
        return "Recalculate Workbook (LibreOffice)"

    def validate(self, context: ExecutionContext) -> bool:
        if not context.artifacts.final_output_path:
            context.log("No output path recorded; skipping recalculation.", Severity.WARNING)
            return False
        return True

    def execute(self, context: ExecutionContext) -> bool:
        path = Path(context.artifacts.final_output_path)
        if not path.exists():
            context.log(f"Cannot recalculate - output file not found: {path}", Severity.WARNING)
            return True  # non-fatal

        soffice = shutil.which("soffice") or shutil.which("libreoffice")
        if not soffice:
            context.log(
                "LibreOffice not found on PATH - skipping recalculation. "
                "Formula cells (Target Allocation %, Position Size, etc.) will "
                "have no cached value until the file is opened in Excel/LibreOffice "
                "at least once. Downstream Python tools reading with "
                "openpyxl(data_only=True) will see None for those cells until then, "
                "which is a caching gap, not a data error.",
                Severity.WARNING,
            )
            return True  # non-fatal

        try:
            import tempfile, shutil as _shutil

            with tempfile.TemporaryDirectory() as tmpdir:
                result = subprocess.run(
                    [soffice, "--headless", "--convert-to", "xlsx", "--outdir", tmpdir, str(path)],
                    capture_output=True, text=True, timeout=120,
                )
                converted = Path(tmpdir) / path.name
                # LibreOffice returns exit code 0 even when it fails to write
                # (e.g. the classic "same source/dest path" lock conflict this
                # step exists partly to avoid by using a temp dir at all) - so
                # exit code alone isn't trustworthy. Check the output file
                # actually landed before treating this as a success.
                if result.returncode != 0 or not converted.exists():
                    context.log(
                        f"LibreOffice recalculation failed (exit {result.returncode}, "
                        f"output present: {converted.exists()}): {result.stderr.strip()[:300]}. "
                        f"Formula cells may read as None downstream until the file is "
                        f"opened manually.",
                        Severity.WARNING,
                    )
                    return True  # non-fatal

                _shutil.move(str(converted), str(path))

            context.log(f"Workbook recalculated via LibreOffice: {path}", Severity.INFO)
            return True

        except subprocess.TimeoutExpired:
            context.log("LibreOffice recalculation timed out after 120s - skipping.", Severity.WARNING)
            return True  # non-fatal
        except Exception as e:
            context.log(f"Recalculation step failed to run: {str(e)}", Severity.WARNING)
            return True  # non-fatal - don't let this break the pipeline

    def rollback(self, context: ExecutionContext) -> None:
        pass
