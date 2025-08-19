import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import set_key, find_dotenv
from intelli_test.utilities import config

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/settings", tags=["Settings"])

class ApiKeyRequest(BaseModel):
    api_key: str

@router.get("/api-key-status")
async def get_api_key_status():
    """Checks if the Google AI API Key is set."""
    # config.GENAI_API_KEY is loaded from the .env file on startup
    is_set = bool(config.API_KEY)
    return {"is_set": is_set}

@router.post("/api-key")
async def save_api_key(request: ApiKeyRequest):
    """Saves the Google AI API Key to the .env file."""
    try:
        # Find the .env file in the project root
        dotenv_path = find_dotenv()
        if not dotenv_path:
            # If .env doesn't exist, create it in the project root
            dotenv_path = config.PROJECT_ROOT.parent / ".env"
            dotenv_path.touch()

        # Set the key in the .env file. This will add or update the variable.
        set_key(dotenv_path, "GENAI_API_KEY", request.api_key)
        set_key(dotenv_path, "MODEL_NAME", config.MODEL_NAME)  # Ensure MODEL_NAME is also set
        
        logger.info("Successfully saved API_KEY to .env file.")
        return {"message": "API Key saved successfully."}
    except Exception as e:
        logger.error(f"Failed to save API Key to .env file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not save the API key.")