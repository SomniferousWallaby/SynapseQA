import sys
import os
# Add the 'src' directory to sys.path if not already present
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)
    
import pytest
import logging
from playwright.sync_api import Page, expect, Browser
from intelli_test.utilities import config

def pytest_configure(config):
    """
    Configures logging for the entire test suite run.
    This hook runs once before any tests are collected.
    """
    project_root = os.path.dirname(os.path.abspath(__file__))
    logs_folder = os.path.join(project_root, 'logs')
    os.makedirs(logs_folder, exist_ok=True)
    
    # Get the root logger and set the level.
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Clear any existing handlers to avoid duplicate logs.
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
        
    # Create a shared formatter.
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Add a file handler to log to a file.
    file_handler = logging.FileHandler(
        filename=os.path.join(logs_folder, 'test_run.log'),
        mode='w'
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Add a stream handler to also log to the console.
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)

@pytest.fixture(scope="function")
def logged_in_page(browser: Browser) -> Page:
    """
    A fixture that provides a pre-authenticated page object by loading
    the saved authentication state

    It creates a new browser context for isolation.
    """
    auth_file = config.AUTH_STATE_PATH
    if not os.path.exists(auth_file):
        pytest.fail(
            f"Authentication state file not found at '{auth_file}'. "
            "Please run 'python -m utilities.create_auth_state' to generate it."
        )

    context = browser.new_context(storage_state=auth_file)
    page = context.new_page()

    yield page

    # Clean up the context to ensure no state leaks between tests.
    context.close()
