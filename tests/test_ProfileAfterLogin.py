import pytest
import logging
from playwright.sync_api import Page, expect
from utilities import smartElementFinder, config

def test_edit_user_profile(logged_in_page: Page):
    """
    Test that a user's profile can be edited.
    """
    logging.info("Navigating to user profile page.")
    logged_in_page.goto(f"{config.BASE_URL}/account/profile")

    logging.info("Filling out profile information.")
    first_name_input = smartElementFinder.find_element_smart(logged_in_page, 'ProfileAfterLogin', 'first_name_input')
    first_name_input.fill("John")

    last_name_input = smartElementFinder.find_element_smart(logged_in_page, 'ProfileAfterLogin', 'last_name_input')
    last_name_input.fill("Doe")

    email_input = smartElementFinder.find_element_smart(logged_in_page, 'ProfileAfterLogin', 'email_input')
    email_input.fill("john.doe@example.com")

    phone_input = smartElementFinder.find_element_smart(logged_in_page, 'ProfileAfterLogin', 'phone_input')
    phone_input.fill("123-456-7890")

    street_input = smartElementFinder.find_element_smart(logged_in_page, 'ProfileAfterLogin', 'street_input')
    street_input.fill("123 Main St")

    postal_code_input = smartElementFinder.find_element_smart(logged_in_page, 'ProfileAfterLogin', 'postal_code_input')
    postal_code_input.fill("12345")

    city_input = smartElementFinder.find_element_smart(logged_in_page, 'ProfileAfterLogin', 'city_input')
    city_input.fill("Anytown")

    state_input = smartElementFinder.find_element_smart(logged_in_page, 'ProfileAfterLogin', 'state_input')
    state_input.fill("CA")

    country_input = smartElementFinder.find_element_smart(logged_in_page, 'ProfileAfterLogin', 'country_input')
    country_input.fill("USA")

    update_profile_button = smartElementFinder.find_element_smart(logged_in_page, 'ProfileAfterLogin', 'update_profile_button')
    update_profile_button.click()

    # Assertion
    # TODO: Implement assertion to verify profile update was successful, e.g., check for a success message
    # For now, just check URL is still profile page
    expect(logged_in_page).to_have_url(f"{config.BASE_URL}/account/profile")