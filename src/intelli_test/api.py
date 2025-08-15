import logging
import os
import json
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
import subprocess
from pathlib import Path
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from fastapi.staticfiles import StaticFiles

from .utilities import generateFingerprintFiles, create_auth_state, automatedLogin
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

# --- Static Files Mount (for Production) ---
# This serves the built React app. It's configured to not crash if the build folder doesn't exist (e.g., in development).
# Correctly determine the project root, which is two levels up from this file's directory (api.py -> src -> project_root)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
static_files_path = os.path.join(project_root, 'frontend', 'build')

if os.path.isdir(static_files_path):
    # Mount at the root to serve the SPA. `html=True` is for client-side routing.
    app.mount("/", StaticFiles(directory=static_files_path, html=True), name="static-root")
    logger.info(f"Serving static production build from: {static_files_path}")
else:
    logger.warning(f"Static production build directory not found at '{static_files_path}'. This is expected in development.")

# --- Background Task Models ---
class FingerprintRequest(BaseModel):
    url: str
    output_filename: str  # e.g., "loginPage"
    use_authentication: bool = False
    allow_redirects: bool = False

def run_fingerprint_generation(url: str, output_filename: str, use_authentication: bool, allow_redirects: bool):
    """
    A wrapper function to be run in the background.
    It handles the Playwright context management.
    """
    logger.info(f"Background task started for fingerprinting: {url}")
    
    auth_path = None
    if use_authentication: # Check for auth file existence before starting the long-running task.
        auth_path = config.AUTH_STATE_PATH
        if not os.path.exists(auth_path):
            logger.error(f"Authentication requested, but auth file not found at: {auth_path}")
            logger.error(f"Please run 'python -m utilities.create_auth_state' to generate it.")
            return  # Stop the background task
        logger.info(f"Using authentication file: {auth_path}")
    else:
        logger.info("Authentication not requested.")

    # Use the project_root to construct a reliable, absolute path.
    output_path = os.path.join(project_root, 'elements', f"{output_filename}.json")

    try:
        generateFingerprintFiles.generate_fingerprint_file(
            target_url=url, 
            output_file=output_path, 
            use_authentication=use_authentication, 
            allow_redirects=allow_redirects
        )
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


class AuthStateRequest(BaseModel):
    url: str # Base site URL ex. www.google.com
    login_path: str # Path to the login page ex. /auth/login

def run_create_auth_state(url: str, login_path: str):
    """
    Background task to create or update the authentication state.
    This is typically used to manually log in and save the session state.
    """
    logger.info(f"Creating authentication state for URL: {url}")
    try:
        create_auth_state.main_sync(url=url, login_path=login_path)
        logger.info("Authentication state creation completed")
    except Exception as e:
        logger.error(f"Error during authentication state creation for {url}: {e}", exc_info=True)


class AutomatedAuthStateRequest(BaseModel):
    login_url: str
    login_instructions: str
    fingerprint_filename: str | None = None
    headless: bool = True
    username: str | None = None
    password: str | None = None

def run_automated_auth_creation(login_url: str, login_instructions: str, fingerprint_filename: str | None = None, headless: bool = True, username: str | None = None, password: str | None = None):
    """Background task for automated auth state creation."""
    logger.info(f"Background task started for automated auth state creation for: {login_url}")
    try:
        automatedLogin.create_automated_auth_state(
            login_url=login_url,
            login_instructions=login_instructions,
            fingerprint_filename=fingerprint_filename,
            headless=headless,
            username=username,
            password=password
        )
        logger.info(f"Background task finished for automated auth state creation for: {login_url}")
    except Exception as e:
        logger.error(f"Error during background automated auth state creation for {login_url}: {e}", exc_info=True)


class TestRunRequest(BaseModel):
    filename: str


# --- Path Security Helper ---
def get_secure_path(file_type: str, filename: str) -> Path:
    """
    Validates file_type and filename, and returns a secure, absolute path.
    Prevents path traversal attacks.
    """
    if file_type not in ("test", "fingerprint"):
        raise HTTPException(status_code=400, detail="Invalid file type specified.")

    # Basic sanitization
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Filename cannot contain path separators.")

    base_dir_map = {
        "test": Path(project_root) / "tests",
        "fingerprint": Path(project_root) / "elements",
    }
    
    base_dir = base_dir_map[file_type]
    secure_path = base_dir.joinpath(filename).resolve()

    # Final check to ensure the resolved path is within the intended base directory
    if not secure_path.is_file() or base_dir not in secure_path.parents:
        raise HTTPException(status_code=404, detail="File not found or path is invalid.")

    return secure_path


def get_secure_path_for_delete(file_type: str, filename: str) -> Path:
    """
    A slightly different version for deletion that doesn't check for existence,
    as the file might be gone, but still performs security checks.
    """
    if file_type not in ("test", "fingerprint"):
        raise HTTPException(status_code=400, detail="Invalid file type specified.")

    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Filename cannot contain path separators.")

    base_dir_map = {
        "test": Path(project_root) / "tests",
        "fingerprint": Path(project_root) / "elements",
    }
    
    base_dir = base_dir_map[file_type]
    # Resolve the path to get its canonical form
    secure_path = base_dir.joinpath(filename).resolve()

    # Check that the resolved path is inside the intended directory
    if base_dir not in secure_path.parents:
        raise HTTPException(status_code=400, detail="Invalid filename, path traversal detected.")

    return secure_path


# --- API Endpoints ---
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
    background_tasks.add_task(
        run_fingerprint_generation, 
        request.url, 
        request.output_filename, 
        request.use_authentication,
        request.allow_redirects
    )
    return {"message": "Fingerprint generation has been started in the background."}


@app.post("/auth_state/manual", status_code=202)
async def create_auth_state(request: AuthStateRequest, background_tasks: BackgroundTasks):
    """
    Accepts a request to create or update the authentication state.
    This is typically used to manually log in and save the session state.
    """
    logger.info("Received request to create or update authentication state.")
    background_tasks.add_task(
        run_create_auth_state,
        request.url,
        request.login_path
    )
    return {"message": "Authentication state creation has been started in the background."}


@app.post("/auth_state/automated", status_code=202)
async def create_automated_auth_state(request: AutomatedAuthStateRequest, background_tasks: BackgroundTasks):
    """
    Triggers an AI-driven process to log in and save the authentication state.
    It also saves the request details to pre-fill the form on subsequent visits.
    """
    # Save the request data for future use
    try:
        with open(config.AUTH_SETTINGS_PATH, 'w', encoding='utf-8') as f:
            json.dump(request.dict(), f, indent=2)
        logger.info(f"Saved automated auth settings to {config.AUTH_SETTINGS_PATH}")
    except Exception as e:
        # Log the error but don't fail the request, as saving is a convenience feature.
        logger.warning(f"Could not save automated auth settings: {e}", exc_info=True)

    if not request.login_url.startswith("http"):
        raise HTTPException(status_code=400, detail="Invalid login_url provided. Must start with http or https.")
    if request.fingerprint_filename:
        if not request.fingerprint_filename.endswith(".json"):
            raise HTTPException(status_code=400, detail="fingerprint_filename must end with .json")
        if "/" in request.fingerprint_filename or "\\" in request.fingerprint_filename:
            raise HTTPException(
                status_code=400, detail="fingerprint_filename cannot contain path separators."
            )

    logger.info(f"Received automated auth state request for URL: {request.login_url}")
    background_tasks.add_task(
        run_automated_auth_creation,
        request.login_url,
        request.login_instructions,
        request.fingerprint_filename,
        request.headless,
        request.username,
        request.password
    )
    return {"message": "Automated authentication state creation has been started in the background."}


@app.get("/auth_state/automated/settings")
async def get_automated_auth_settings():
    """
    Returns the last used settings for automated auth state creation.
    """
    if not os.path.exists(config.AUTH_SETTINGS_PATH):
        logger.info("Automated auth settings file not found. Returning empty object.")
        return {}
    
    try:
        with open(config.AUTH_SETTINGS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Could not read or parse automated auth settings file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not read automated auth settings file.")


@app.get("/files/fingerprints")
async def list_fingerprint_files():
    """Returns a list of available fingerprint JSON files."""
    # Use the project_root defined at the top of this file for reliability
    elements_dir = os.path.join(project_root, 'elements')
    if not os.path.isdir(elements_dir):
        logger.warning(f"Fingerprints directory not found at '{elements_dir}'. Returning empty list.")
        return [] # Return empty list if directory doesn't exist
    try:
        return [f for f in os.listdir(elements_dir) if f.endswith('.json')]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/files/tests")
async def list_test_files():
    """Returns a list of available test Python files."""
    # Use the project_root defined at the top of this file for reliability
    tests_dir = os.path.join(project_root, 'tests')
    if not os.path.isdir(tests_dir):
        logger.warning(f"Tests directory not found at '{tests_dir}'. Returning empty list.")
        return [] # Return empty list if directory doesn't exist
    try:
        # Filter out __pycache__ and other non-test files
        return [
            f for f in os.listdir(tests_dir) 
            if f.startswith('test_') and f.endswith('.py')
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/files/auth-state")
async def get_auth_state_status():
    """
    Checks for the existence, modification time, and expiration status of the auth_state.json file.
    """
    auth_path = config.AUTH_STATE_PATH
    if os.path.exists(auth_path):
        try:
            with open(auth_path, 'r', encoding='utf-8') as f:
                auth_data = json.load(f)

            last_modified_timestamp = os.path.getmtime(auth_path)
            last_modified_dt = datetime.fromtimestamp(last_modified_timestamp)

            cookies = auth_data.get("cookies", [])
            if not cookies:
                logger.warning(f"Auth state file at '{auth_path}' contains no cookies. Treating as expired.")
                return {"exists": True, "last_modified": last_modified_dt.isoformat(), "expires_at": None, "is_expired": True}

            # Find the expiration timestamp from the cookies. A session is invalid if any of its cookies expire.
            # We look for the soonest expiration time. Timestamps of -1 mean it's a session cookie.
            expirations = [
                cookie.get("expires")
                for cookie in cookies
                if cookie.get("expires") and cookie.get("expires") != -1
            ]

            if not expirations:
                logger.info(f"Auth state file at '{auth_path}' contains no expiring cookies. Cannot determine exact expiration time.")
                return {"exists": True, "last_modified": last_modified_dt.isoformat(), "expires_at": None, "is_expired": False}

            # The session expires when the first cookie expires.
            soonest_expiration_ts = min(expirations)
            expires_at_dt = datetime.fromtimestamp(soonest_expiration_ts)
            is_expired = datetime.now() > expires_at_dt

            return {"exists": True, "last_modified": last_modified_dt.isoformat(), "expires_at": expires_at_dt.isoformat(), "is_expired": is_expired}
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Could not parse auth file at '{auth_path}': {e}")
            raise HTTPException(status_code=500, detail="Could not parse auth file.")
        except Exception as e:
            logger.error(f"Could not read auth file metadata from '{auth_path}': {e}")
            raise HTTPException(status_code=500, detail="Could not read auth file metadata.")
    else:
        logger.warning(f"Auth state file not found at '{auth_path}'.")
        return {"exists": False, "last_modified": None, "expires_at": None, "is_expired": True}


@app.get("/")
def read_root():
    return {"message": "Welcome to the intelliTest API. Visit /docs for documentation."}