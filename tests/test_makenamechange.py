import pytest
import logging
from playwright.sync_api import Page, expect
from utilities import smartElementFinder, config

def test_change_login_name(logged_in_page: Page):
    """
    This test changes the user's login name.
    """
    logging.info("Navigating to the profile page.")
    logged_in_page.goto(f"{config.BASE_URL}/profile")

    logging.info("Locating the 'Edit Profile' button.")
    edit_profile_button = smartElementFinder.find_element_smart(logged_in_page, 'profile_page', 'edit_profile_button')

    logging.info("Clicking the 'Edit Profile' button.")
    edit_profile_button.click()

    logging.info("Locating the 'Login Name' field.")
    login_name_field = smartElementFinder.find_element_smart(logged_in_page, 'profile_page', 'login_name_field')

    logging.info("Clearing the 'Login Name' field.")
    login_name_field.fill("")

    logging.info("Entering the new login name 'stooart'.")
    login_name_field.fill("stooart")

    logging.info("Locating the 'Save Changes' button.")
    save_changes_button = smartElementFinder.find_element_smart(logged_in_page, 'profile_page', 'save_changes_button')

    logging.info("Clicking the 'Save Changes' button.")
    save_changes_button.click()

    logging.info("Verifying the success message.")
    success_message = smartElementFinder.find_element_smart(logged_in_page, 'profile_page', 'success_message')
    expect(success_message).to_be_visible()

    logging.info("Verifying that the login name has been updated in the UI.")
    updated_login_name = smartElementFinder.find_element_smart(logged_in_page, 'profile_page', 'updated_login_name')
    expect(updated_login_name).to_have_text("stooart")