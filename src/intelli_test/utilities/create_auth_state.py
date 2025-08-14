import os
import asyncio
from playwright.async_api import async_playwright
from . import config

async def main():
    """

    Launches a browser, allows the user to log in manually,
    and then saves the authentication state to a file.
    """
    if os.path.exists(config.AUTH_STATE_PATH):
        overwrite = input(f"'{config.AUTH_STATE_PATH}' already exists. Overwrite? (y/n): ").lower()
        if overwrite != 'y':
            print("Exiting without creating a new auth state file.")
            return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Must be non-headless for manual login
        context = await browser.new_context()
        page = await context.new_page()

        login_url = f"{config.BASE_URL}{config.LOGIN_PAGE_PATH}"
        print(f"Navigating to login page: {login_url}")
        await page.goto(login_url)

        print("\n" + "="*60)
        print("Please log in to the website in the browser window that just opened.")
        print("Once you are successfully logged in, press Enter in this terminal.")
        print("="*60)
        input()  # Wait for user to press Enter

        print(f"Saving authentication state to {config.AUTH_STATE_PATH}...")
        await context.storage_state(path=config.AUTH_STATE_PATH)
        
        print("Authentication state saved successfully. You can now close the browser.")
        await browser.close()

def main_sync():
    """Synchronous wrapper to be used as a script entry point."""
    asyncio.run(main())

if __name__ == "__main__":
    main_sync()

