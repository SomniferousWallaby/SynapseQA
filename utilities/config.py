import os
from dotenv import load_dotenv

load_dotenv()

def get_required_env(var_name: str) -> str:
    """Gets an environment variable, raising an error if it's not set."""
    value = os.getenv(var_name)
    if value is None:
        raise ValueError(f"Required environment variable '{var_name}' is not set in your .env file.")
    return value

# Centralized configuration values
API_KEY = get_required_env("GENAI_API_KEY")
MODEL_NAME = get_required_env("MODEL")
BASE_URL = get_required_env("BASE_URL")