import logging
import pytest
from playwright.sync_api import Page, expect
from utilities import imageComparison, smartElementFinder, config

# --- Logger Setup ---
logger = logging.getLogger(__name__)

def test_login_successful(page: Page, request: pytest.FixtureRequest):
    """Tests the login functionality with valid credentials and performs a visual check."""
    logger.info(f"Starting test: {request.node.name}")
    page.goto(f"{config.BASE_URL}{config.LOGIN_PAGE_PATH}")

    # Use the smart finder to locate elements based on definitions in loginPage.json
    email_field = smartElementFinder.find_element_smart(page, 'loginPage', 'email_field')
    password_field = smartElementFinder.find_element_smart(page, 'loginPage', 'password_field')
    login_button = smartElementFinder.find_element_smart(page, 'loginPage', 'login_button')
  
    email_field.fill(config.TEST_USER)
    password_field.fill(config.PASSWORD)
    login_button.click()

    page.wait_for_load_state('networkidle', timeout=50000)

    # Assert that the login was successful by checking the URL
    expect(page).to_have_url(f"{config.BASE_URL}{config.ACCOUNT_PAGE_PATH}")

    # Perform visual regression testing
    logger.info("Performing visual comparison for the account page.")
    score, diff_image = imageComparison.compare_test_run_images(page, request.node.name)
    
    # Assert that the visual similarity score meets the threshold
    assert score >= config.SIMILARITY_THRESHOLD, (
        f"Visual regression test failed for '{request.node.name}'. "
        f"Similarity score of {score:.2f} is below the threshold of {config.SIMILARITY_THRESHOLD}."
    )
    logger.info(f"Visual comparison passed with a score of {score:.2f}.")


def test_login_failed(page: Page, request: pytest.FixtureRequest):
    """Tests that login fails with invalid credentials and an error is shown."""
    logger.info(f"Starting test: {request.node.name}")
    page.goto(f"{config.BASE_URL}{config.LOGIN_PAGE_PATH}")

    # Locate elements using the smart finder
    email_field = smartElementFinder.find_element_smart(page, 'loginPage', 'email_field')
    password_field = smartElementFinder.find_element_smart(page, 'loginPage', 'password_field')
    login_button = smartElementFinder.find_element_smart(page, 'loginPage', 'login_button')

    # Fill the form with invalid credentials
    email_field.fill(config.INVALID_USER)
    password_field.fill("this-is-a-wrong-password")
    login_button.click()

    # Locate the error message and assert it is visible
    error_message = smartElementFinder.find_element_smart(page, 'loginPage', 'login_error_message')
    expect(error_message).to_be_visible()
    expect(error_message).to_have_text("Invalid email or password")

    logger.info("Login failed as expected and error message was displayed.")
