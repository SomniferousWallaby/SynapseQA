import subprocess
import json
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from intelli_test import security
from intelli_test.utilities import config
from pathlib import Path

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tests", tags=["Tests"])

class TestRunRequest(BaseModel):
    filename: str


def run_all_tests_background():
    """Runs the entire pytest suite in the background."""
    logger.info("Background task started for running all tests.")
    report_dir = config.PROJECT_ROOT.parent / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"report-all-tests.json"
    project_root = config.PROJECT_ROOT.parent
    try:
        command = [
            "pytest",
            f"{project_root}/tests/", # Target the whole tests directory
            "--json-report",
            f"--json-report-file={report_path}",
            "--tb=short",
        ]
        subprocess.run(
            command,
            cwd=config.PROJECT_ROOT,
            timeout=600 # Longer timeout for the full suite
        )
        logger.info("Background task for running all tests finished.")
    except Exception as e:
        logger.error(f"Error during 'run all' background task: {e}", exc_info=True)
@router.post("/run-all", status_code=202)
async def run_all_tests_endpoint(background_tasks: BackgroundTasks):
    """
    Triggers a background task to run the entire test suite.
    """
    logger.info("Received request to run all tests.")
    background_tasks.add_task(run_all_tests_background)
    return {"message": "Test suite run has been started in the background."}


@router.post("/run")
async def run_test_endpoint(request: TestRunRequest):
    """
    Runs a specific test file using pytest and returns the results as JSON.
    """
    logger.info(f"Received request to run test: {request.filename}")

    report_dir = config.PROJECT_ROOT.parent / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"report-{request.filename.removesuffix('.py').removeprefix('test_')}.json"

    try:
        # 1. Validate and get the full path to the test file
        test_file_path = security.get_secure_path("test", request.filename)

        # 2. Construct the pytest command
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

