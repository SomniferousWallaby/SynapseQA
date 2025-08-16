import os
import logging
import json
from fastapi import APIRouter, HTTPException
from intelli_test.utilities import config
from intelli_test.schemas import AuthStateRequest, AutomatedAuthStateRequest
from intelli_test.tasks import run_create_auth_state, run_automated_auth_creation
from fastapi import BackgroundTasks


logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/authentication",  # Common prefix for all routes in this file
    tags=["Authentication"]  # Groups endpoints in the API docs
)

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

@router.post("/auth_state/manual", status_code=202)
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


@router.post("/auth_state/automated", status_code=202)
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


@router.get("/auth_state/automated/settings")
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

