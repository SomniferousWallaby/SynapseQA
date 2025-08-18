import subprocess
import json
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from intelli_test import security
from intelli_test.utilities import config
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tests", tags=["Tests"])

class TestRunRequest(BaseModel):
    filename: str

@router.post("/run")
async def run_test_endpoint(request: TestRunRequest):
    """
    Runs a specific test file using pytest and returns the results as JSON.
    """
    logger.info(f"Received request to run test: {request.filename}")

    report_dir = config.PROJECT_ROOT.parent / "results"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"report-{request.filename.removesuffix('.py').removeprefix('test_')}.json"

    try:
        # 1. Securely validate and get the full path to the test file
        test_file_path = security.get_secure_path("test", request.filename)

        # 2. Construct the pytest command
        #    --json-report-file=none prints the report to stdout instead of a file
        command = [
            "pytest",
            str(test_file_path),
            "--json-report",
            f"--json-report-file={report_path}",
            "--tb=short"
        ]
        
        # 3. Execute the command
        logger.info(f"Running command: {' '.join(command)} at {config.PROJECT_ROOT.parent}") 
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=config.PROJECT_ROOT.parent, 
            timeout=120
        )

        # 4. Check for errors during the run
        if not report_path.is_file():
            logger.error(f"Pytest did not create the report file at {report_path}.")
            raise HTTPException(status_code=500, detail="Test run failed to produce a report file.")
        
        # 5. Read the JSON report from the file
        report_content = report_path.read_text(encoding="utf-8")
        report = json.loads(report_content)
        return report

    except Exception as e:
        # Re-raise known HTTP exceptions
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"An unexpected error occurred while running test '{request.filename}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred while running the test.")
    #finally:
        # 6. Clean up and delete the temporary file
        #if report_path.is_file():
        #    report_path.unlink()