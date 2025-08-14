import logging
import os
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel
from playwright.sync_api import sync_playwright
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .utilities import generateFingerprintFiles
from .utilities import config, testFileGenerator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="intelliTest API",
    description="API for orchestrating AI-powered web testing.",
    version="1.0.0"
)

# --- Middleware Configuration ---
# Allow CORS for frontend development (e.g., React app on localhost:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify your frontend's origin, e.g., "http://localhost:3000"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Static Files Mount ---
# This will serve the built frontend application in production
static_files_path = os.path.join(config.PROJECT_ROOT, 'frontend', 'build')
app.mount("/static", StaticFiles(directory=static_files_path), name="static")

class FingerprintRequest(BaseModel):
    url: str
    output_filename: str  # e.g., "loginPage"
    use_authentication: bool = False

def run_fingerprint_generation(url: str, output_filename: str, use_authentication: bool):
    """
    A wrapper function to be run in the background.
    It handles the Playwright context management.
    """
    logger.info(f"Background task started for fingerprinting: {url}")
    
    auth_path = None
    if use_authentication:
        auth_path = config.AUTH_STATE_PATH
        if not os.path.exists(auth_path):
            logger.error(f"Authentication requested, but auth file not found at: {auth_path}")
            logger.error(f"Please run 'python -m utilities.create_auth_state' to generate it.")
            return  # Stop the background task
        logger.info(f"Using authentication file: {auth_path}")
    else:
        logger.info("Authentication not requested.")

    output_path = f"elements/{output_filename}.json"

    try:
        generateFingerprintFiles.generate_fingerprint_file(None, url, output_path, auth_file_path=auth_path)
        logger.info(f"Background task finished for fingerprinting: {url}")
    except Exception as e:
        logger.error(f"Error during background fingerprint generation for {url}: {e}", exc_info=True)

class TestGenerationRequest(BaseModel):
    description: str
    file_name: str
    fingerprint_filename: str | None = None
    requires_login: bool = False

def run_test_generation(description: str, file_name: str, fingerprint_filename: str | None = None, requires_login: bool = False):
    """Background task wrapper for generating a test file."""
    logger.info(f"Background task started for test generation: {file_name}")
    try:
        testFileGenerator.generate_test_file(description, file_name, fingerprint_filename=fingerprint_filename, requires_login=requires_login)
        logger.info(f"Background task finished for test generation: {file_name}")
    except Exception as e:
        logger.error(f"Error during background test generation for {file_name}: {e}", exc_info=True)

@app.post("/generate-test", status_code=202)
async def create_test_file(request: TestGenerationRequest, background_tasks: BackgroundTasks):
    """
    Accepts a natural language description and generates a new Python test file.
    """
    file_name = request.file_name
    # Basic security and validation
    if not file_name.startswith("test_") or not file_name.endswith(".py"):
        raise HTTPException(
            status_code=400, 
            detail="Invalid file_name. It must start with 'test_' and end with '.py'."
        )
    if "/" in file_name or "\\" in file_name:
        raise HTTPException(
            status_code=400,
            detail="Invalid file_name. It cannot contain path separators."
        )
    
    fingerprint_filename = request.fingerprint_filename
    if fingerprint_filename:
        if not fingerprint_filename.endswith(".json"):
            raise HTTPException(status_code=400, detail="fingerprint_filename must end with .json")
        if "/" in fingerprint_filename or "\\" in fingerprint_filename:
            raise HTTPException(
                status_code=400, detail="fingerprint_filename cannot contain path separators."
            )

    logger.info(f"Received test generation request for file: {file_name}")
    background_tasks.add_task(run_test_generation, request.description, request.file_name, request.fingerprint_filename, request.requires_login)
    return {"message": f"Test file generation for '{file_name}' has been started in the background."}

@app.post("/fingerprint", status_code=202)
async def create_fingerprint(request: FingerprintRequest, background_tasks: BackgroundTasks):
    """
    Accepts a URL and triggers the AI-powered element fingerprinting process
    in the background.
    """
    if not request.url.startswith("http"):
        raise HTTPException(status_code=400, detail="Invalid URL provided. Must start with http or https.")

    logger.info(f"Received fingerprint request for URL: {request.url}")
    background_tasks.add_task(run_fingerprint_generation, request.url, request.output_filename, request.use_authentication)
    return {"message": "Fingerprint generation has been started in the background."}

@app.get("/files/fingerprints")
async def list_fingerprint_files():
    """Returns a list of available fingerprint JSON files."""
    elements_dir = os.path.join(config.PROJECT_ROOT, 'elements')
    if not os.path.isdir(elements_dir):
        return []
    try:
        return [f for f in os.listdir(elements_dir) if f.endswith('.json')]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files/tests")
async def list_test_files():
    """Returns a list of available test Python files."""
    tests_dir = os.path.join(config.PROJECT_ROOT, 'tests')
    if not os.path.isdir(tests_dir):
        return []
    try:
        # Filter out __pycache__ and other non-test files
        return [
            f for f in os.listdir(tests_dir) 
            if f.startswith('test_') and f.endswith('.py')
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"message": "Welcome to the intelliTest API. Visit /docs for documentation."}