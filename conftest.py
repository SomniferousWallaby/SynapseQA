import os
import pytest
import logging
from playwright.sync_api import Page, expect
from intelli_test.utilities import config, smartElementFinder

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
def logged_in_page(page: Page) -> Page:
    """
    A fixture that logs in a user and returns an authenticated page object.
    This avoids repeating login steps in every test that requires authentication.
    """
    page.goto(f"{config.BASE_URL}{config.LOGIN_PAGE_PATH}")

    # Use the smart finder to locate elements and log in
    # NOTE: Using 'loginPage' as the category, which is consistent with test_login.py
    smartElementFinder.find_element_smart(page, 'loginPage', 'email_field').fill(config.TEST_USER)
    smartElementFinder.find_element_smart(page, 'loginPage', 'password_field').fill(config.PASSWORD)
    smartElementFinder.find_element_smart(page, 'loginPage', 'login_button').click()

    # Wait for navigation and verify login was successful
    expect(page).to_have_url(f"{config.BASE_URL}{config.ACCOUNT_PAGE_PATH}", timeout=10000)
    
    yield page