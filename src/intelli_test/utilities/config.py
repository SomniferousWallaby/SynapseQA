import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def get_required_env(var_name: str) -> str:
    """Gets an environment variable, raising an error if it's not set."""
    value = os.getenv(var_name)
    if value is None:
        raise ValueError(f"Required environment variable '{var_name}' is not set in your .env file.")
    return value

# --- Path Constants ---
# Correctly determine the project root, which is three levels up from this file's directory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
AUTH_STATE_PATH = os.path.join(PROJECT_ROOT.parent, "auth_state.json")
AUTH_SETTINGS_PATH = os.path.join(PROJECT_ROOT.parent, "auth_creation_settings.json")

# --- API Configuration ---
# The API key is the only truly required secret. We get it from the .env file, but it can also be set via the UI
# The app will check for its presence at runtime via the UI instead of crashing on startup.
API_KEY = os.getenv("GENAI_API_KEY")
MODEL_NAME = "gemini-2.0-flash" # Default model TODO: Make this configurable via the UI
# TODO: Add greater config options for the model, like other providers, local models, etc.


# --- Default Test Values (Optional Overrides) ---
# These can be set in the .env file to use some of the function not utilized by the UI, but they are not required.
# The application will primarily use values entered by the user in the dashboard.
BASE_URL = os.getenv("BASE_URL", "")
LOGIN_PAGE_PATH = os.getenv("LOGIN_PAGE_PATH", "")
ACCOUNT_PAGE_PATH = os.getenv("ACCOUNT_PAGE_PATH", "")
TEST_USER = os.getenv("TEST_USER", "")
PASSWORD = os.getenv("PASSWORD", "")
INVALID_USER = os.getenv("INVALID_USER", "")