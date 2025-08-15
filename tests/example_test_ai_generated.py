import logging
import pytest
from playwright.sync_api import Page, expect
from intelli_test.utilities import genAITestGenerator, smartElementFinder, config

logger = logging.getLogger(__name__)

def _run_ai_command(page: Page, command: str):
    """
    A helper function to run an AI command, wait for the page to settle,
    and handle potential errors with a clear pytest failure message.
    """
    logger.info(f"Executing AI test for command: '{command}'")
    try:
        genAITestGenerator.executeGenAITest(page, command)
    except (ValueError, RuntimeError) as e:
        pytest.fail(f"AI test execution failed for command '{command}': {e}", pytrace=False)

def test_ai_login_flow(page: Page):
    """
    Generates and executes a test flow based on a natural language command.
    """
    # Define the command with placeholders for credentials.
    test_user = config.TEST_USER
    test_password = config.PASSWORD

    user_command = f"go to the login page, fill in the email with '{test_user}', fill in the password with '{test_password}', and click the login button"
    logger.info(f"Executing AI test for command: '{user_command}'")

    # 1. Use LLM to generate test steps and execute them
    _run_ai_command(page, user_command)
    page.wait_for_load_state('networkidle', timeout=50000)

    # 2. Check login was successful
    logger.info("All AI-generated steps executed. Verifying final state.")
    expect(page).to_have_url(f"{config.BASE_URL}{config.ACCOUNT_PAGE_PATH}")

def test_profile_update(logged_in_page: Page):
    """
    Generates and executes a test flow to update a user's profile,
    starting from an authenticated state provided by the `logged_in_page` fixture.
    """
    # The fixture handles login, so we start on the account page.
    # 1. Click the profile button to navigate to the profile editing page.
    _run_ai_command(logged_in_page, "Click on the profile button")

    # 2. Change the profile name and submit.
    _run_ai_command(logged_in_page, "Update the profile first name to 'ugga-dugga' and click the 'Update Profile' button")

    # 3. Assert the update was successful
    logger.info("All AI-generated steps executed. Verifying final state.")
    expect(logged_in_page).to_have_url(f"{config.BASE_URL}{config.ACCOUNT_PAGE_PATH}/profile")
    success_message = smartElementFinder.find_element_smart(logged_in_page, 'profilePage', 'update_success_message')
    expect(success_message).to_be_visible()
    expect(success_message).to_have_text("Your profile is successfully updated!")