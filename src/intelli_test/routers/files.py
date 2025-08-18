import os
import logging
import json
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from intelli_test.utilities import config
from ..security import get_secure_path, get_secure_path_for_delete

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/files",  # Common prefix for all routes in this file
    tags=["Files"]  # Groups endpoints in the API docs
)

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))


@router.get("/fingerprints")
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


@router.get("/tests")
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


@router.get("/auth-state")
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

@router.get("/content")
async def get_file_content(
    type: str = Query(..., description="The type of file: 'test' or 'fingerprint'"),
    filename: str = Query(..., description="The name of the file to retrieve")
):
    """
    Retrieves the content of a specific test or fingerprint file.
    """
    try:
        # Get absolute path
        secure_path = get_secure_path(type, filename)
        
        # Read the file's text content
        content = secure_path.read_text(encoding="utf-8")
        
        return {"filename": filename, "content": content}
    except HTTPException as e:
        # If get_secure_path raised an error (e.g., file not found), re-raise it
        raise e
    except Exception as e:
        # Catch any other potential errors (e.g., permission errors)
        logger.error(f"Error reading file '{filename}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not read the file.")
    
@router.delete("/")
async def delete_file_endpoint(
    type: str = Query(..., description="The type of file: 'test' or 'fingerprint'"),
    filename: str = Query(..., description="The name of the file to delete")
):
    """
    Deletes a specific test or fingerprint file.
    """
    logger.info(f"Received request to delete file '{filename}' of type '{type}'")
    try:
        # Validate input and get a safe file path
        secure_path = get_secure_path_for_delete(type, filename)
        
        if secure_path.is_file():
            secure_path.unlink()  # Actual delete operation
            logger.info(f"Successfully deleted file: {secure_path}")
            return {"message": f"File '{filename}' deleted successfully."}
        else:
            # If the file is already gone, that's still a success.
            logger.warning(f"File to delete not found (already deleted?): {secure_path}")
            return {"message": f"File '{filename}' was already deleted."}

    except HTTPException as e:
        # Re-raise errors from the security helper (e.g., invalid filename)
        raise e
    except Exception as e:
        logger.error(f"Error during file deletion for '{filename}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred while deleting the file.")