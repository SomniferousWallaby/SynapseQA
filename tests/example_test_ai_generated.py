import logging
import pytest
from playwright.sync_api import Page, expect
from utilities import genAITestGenerator, smartElementFinder, config

logger = logging.getLogger(__name__)


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
    try:
        genAITestGenerator.executeGenAITest(page, user_command)
    except (ValueError, RuntimeError) as e:
        pytest.fail(f"AI test execution failed: {e}", pytrace=False)
    page.wait_for_load_state('networkidle', timeout=50000)

    # 2. Check login was successful
    logger.info("All AI-generated steps executed. Verifying final state.")
    expect(page).to_have_url(f"{config.BASE_URL}{config.ACCOUNT_PAGE_PATH}")

def test_profile_update(page: Page):
    """
    Generates an executes a test flow to update a user's profile based on a natural language command.
    """
    test_user = config.TEST_USER
    test_password = config.PASSWORD

    # 1. Login
    page.goto(f"{config.BASE_URL}{config.LOGIN_PAGE_PATH}")
    user_command_1 = (f"On the login page, fill in the email with '{test_user}', fill in the password with '{test_password}', and click the login button ")
    logger.info(f"Executing AI test for command: '{user_command_1}'")
    try:
        genAITestGenerator.executeGenAITest(page, user_command_1)
    except (ValueError, RuntimeError) as e:
        # Fail the test with a clear message if the executor raises an exception.
        pytest.fail(f"AI test execution failed: {e}", pytrace=False)
    page.wait_for_load_state('networkidle', timeout=50000)

    # 2. Click the profile button
    user_command_2 = f"Click on the profile button"
    logger.info(f"Executing AI test for command: '{user_command_2}'")
    try:
        genAITestGenerator.executeGenAITest(page, user_command_2)
    except (ValueError, RuntimeError) as e:
        # Fail the test with a clear message if the executor raises an exception.
        pytest.fail(f"AI test execution failed: {e}", pytrace=False)
    page.wait_for_load_state('networkidle', timeout=50000)

    # 3. Change the profile name.
    user_command_3 = f"Update the profile first name to 'ugga-dugga' and click the 'Update Profile' button"
    logger.info(f"Executing AI test for command: '{user_command_3}'")
    try:
        genAITestGenerator.executeGenAITest(page, user_command_3)
    except (ValueError, RuntimeError) as e:
        # Fail the test with a clear message if the executor raises an exception.
        pytest.fail(f"AI test execution failed: {e}", pytrace=False)

    # 4. Assert the update was successful
    logger.info("All AI-generated steps executed. Verifying final state.")
    expect(page).to_have_url(f"{config.BASE_URL}{config.ACCOUNT_PAGE_PATH}/profile")
    success_message = smartElementFinder.find_element_smart(page, 'profilePage', 'update_success_message')
    expect(success_message).to_be_visible()
    expect(success_message).to_have_text("Your profile is successfully updated!")