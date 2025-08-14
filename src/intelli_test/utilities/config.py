import os
from dotenv import load_dotenv

load_dotenv()

def get_required_env(var_name: str) -> str:
    """Gets an environment variable, raising an error if it's not set."""
    value = os.getenv(var_name)
    if value is None:
        raise ValueError(f"Required environment variable '{var_name}' is not set in your .env file.")
    return value

# --- Path Constants ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUTH_STATE_PATH = os.path.join(PROJECT_ROOT, "auth_state.json")

# --- Centralized Configuration Values ---
API_KEY = get_required_env("GENAI_API_KEY")
MODEL_NAME = get_required_env("MODEL")
BASE_URL = get_required_env("BASE_URL")
LOGIN_PAGE_PATH = get_required_env("LOGIN_PAGE_PATH")
ACCOUNT_PAGE_PATH = get_required_env("ACCOUNT_PAGE_PATH")
TEST_USER = get_required_env("TEST_USER")
PASSWORD = get_required_env("PASSWORD")
INVALID_USER = get_required_env("INVALID_USER")
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", 0.95))