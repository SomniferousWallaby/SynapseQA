import logging
import pytest
from dotenv import dotenv_values
from playwright.sync_api import Page, expect
from utilities import imageComparison, smartElementFinder

# --- Logger Setup ---
logger = logging.getLogger(__name__)

# --- Environment Variable Loading ---
config = dotenv_values()
BASE_URL = config.get("BASE_URL")
TEST_USER = config.get("TEST_USER") or config.get("USER")
PASSWORD = config.get("PASSWORD")
INVALID_USER = config.get("INVALID_USER")

if not all((BASE_URL, TEST_USER, PASSWORD, INVALID_USER)):
    raise ValueError(
        "One or more required environment variables (BASE_URL, TEST_USER/USER, PASSWORD, INVALID_USER) "
        "are not set. Please check your .env file."
    )

# --- Visual Regression Constants ---
VISUAL_THRESHOLD = float(config.get("SIMILARITY_THRESHOLD", 0.95))

def test_login_successful(page: Page, request: pytest.FixtureRequest):
    """Tests the login functionality with valid credentials and performs a visual check."""
    logger.info(f"Starting test: {request.node.name}")
    page.goto(f"{BASE_URL}auth/login")

    # Use the smart finder to locate elements based on definitions in loginPage.json
    email_field = smartElementFinder.find_element_smart(page, 'loginPage', 'email_field')
    password_field = smartElementFinder.find_element_smart(page, 'loginPage', 'password_field')
    login_button = smartElementFinder.find_element_smart(page, 'loginPage', 'login_button')
  
    email_field.fill(TEST_USER)
    password_field.fill(PASSWORD)
    login_button.click()

    page.wait_for_load_state('networkidle', timeout=50000)

    # Assert that the login was successful by checking the URL
    expect(page).to_have_url(f"{BASE_URL}account")

    # Perform visual regression testing
    logger.info("Performing visual comparison for the account page.")
    score, diff_image = imageComparison.compare_test_run_images(page, request.node.name)
    
    # Assert that the visual similarity score meets the threshold
    assert score >= VISUAL_THRESHOLD, (
        f"Visual regression test failed for '{request.node.name}'. "
        f"Similarity score of {score:.2f} is below the threshold of {VISUAL_THRESHOLD}."
    )
    logger.info(f"Visual comparison passed with a score of {score:.2f}.")


def test_login_failed(page: Page, request: pytest.FixtureRequest):
    """Tests that login fails with invalid credentials and an error is shown."""
    logger.info(f"Starting test: {request.node.name}")
    page.goto(f"{BASE_URL}auth/login")

    # Locate elements using the smart finder
    email_field = smartElementFinder.find_element_smart(page, 'loginPage', 'email_field')
    password_field = smartElementFinder.find_element_smart(page, 'loginPage', 'password_field')
    login_button = smartElementFinder.find_element_smart(page, 'loginPage', 'login_button')

    # Fill the form with invalid credentials
    email_field.fill(INVALID_USER)
    password_field.fill("this-is-a-wrong-password")
    login_button.click()

    # Locate the error message and assert it is visible
    error_message = smartElementFinder.find_element_smart(page, 'loginPage', 'login_error_message')
    expect(error_message).to_be_visible()
    expect(error_message).to_have_text("Invalid email or password")

    logger.info("Login failed as expected and error message was displayed.")
