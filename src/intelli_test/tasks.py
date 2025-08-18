import logging
import os

from intelli_test.utilities import generateFingerprintFiles, create_auth_state, automatedLogin, config, testFileGenerator

logger = logging.getLogger(__name__)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


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


def run_test_generation(description: str, file_name: str, fingerprint_filename: str | None = None, requires_login: bool = False):
    """Background task wrapper for generating a test file."""
    logger.info(f"Background task started for test generation: {file_name}")
    try:
        testFileGenerator.generate_test_file(description, file_name, fingerprint_filename=fingerprint_filename, requires_login=requires_login)
        logger.info(f"Background task finished for test generation: {file_name}")
    except Exception as e:
        logger.error(f"Error during background test generation for {file_name}: {e}", exc_info=True)


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
