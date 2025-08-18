import google.generativeai as genai
import logging
import os
import json
from playwright.sync_api import sync_playwright, Page
import textwrap
from . import config

# Configure the generative AI model
genai.configure(api_key=config.API_KEY)
model = genai.GenerativeModel(model_name=config.MODEL_NAME)
logger = logging.getLogger(__name__)

# This template is defined at the module level to avoid indentation issues
# with f-strings inside functions. The .format() method will be used to
# inject the AI-generated script body.
_SCRIPT_TEMPLATE = """
import logging
from playwright.sync_api import Page
from intelli_test.utilities import config

def perform_login(page: Page):
    logger = logging.getLogger(__name__)
    logger.info("Executing dynamically generated login script...")

{script_body}

    logger.info("Dynamic login script finished.")
"""

def build_login_script_prompt(login_url: str, login_instructions: str, fingerprint_json: dict | None = None, username: str | None = None, password: str | None = None) -> str:
    """Constructs the prompt for generating a Playwright login script."""
    
    elements = {}
    if fingerprint_json:
        elements = fingerprint_json.get("elements", {})
    elements_str = json.dumps(elements, indent=2)
    
    if username and password:
        # Escape quotes in username/password to be safe inside the f-string prompt
        safe_username = username.replace('"', '\\"')
        safe_password = password.replace('"', '\\"')
        credentials_instruction = f'4.  **Credentials:** Use the literal string `"{safe_username}"` for the username and `"{safe_password}"` for the password.'
    else:
        credentials_instruction = '4.  **Credentials:** Use `config.TEST_USER` and `config.PASSWORD` for the username and password. The `config` object is already imported and available to your code.'
    
    return f"""
You are an expert Python test automation engineer specializing in Playwright. Your task is to write the body of a Python function that logs into a website.

**Critical Instructions:**
1.  **Code Only:** The output must be ONLY the Python code for the function body. Do NOT include the function definition `def perform_login(page: Page):`, any `import` statements, or any markdown formatting like ```python.
2.  **No Indentation:** All lines of your generated code must have NO initial indentation. The execution environment will handle indenting the code block correctly.
3.  **Context:** The code will be executed inside a function that receives a `page: Page` object that has already navigated to the login page.
{credentials_instruction}
5.  **Locators:** Use the provided element locators to interact with the page. If no locators are provided, use your best judgment for selectors.
6.  **Wait After Action:** After the login action (e.g., clicking a button), you MUST add a wait condition to ensure the login completes. The best method is to wait for the URL to change to something that is NOT the login page. Use this exact line of code: `page.wait_for_url(lambda url: "{login_url}" not in url, timeout=15000)`.

**User's Login Instructions:**
"{login_instructions}"

**Available Elements from Fingerprint File:**
```json
{elements_str}
```

**Generated Python Code (function body only):**
"""

def create_automated_auth_state(login_url: str, login_instructions: str, fingerprint_filename: str | None = None, headless: bool = True, username: str | None = None, password: str | None = None):
    """
    Generates a login script using AI, executes it to log in, and saves the auth state.
    """
    if fingerprint_filename is None:
        logger.info(f"Starting automated auth state creation for {login_url} using no fingerprint file.")
    else:
        logger.info(f"Starting automated auth state creation for {login_url} using fingerprint file: {fingerprint_filename}")

    fingerprint_data = None
    # 1. Load the fingerprint file
    if fingerprint_filename:
        fingerprint_path = os.path.join(config.PROJECT_ROOT.parent, 'elements', fingerprint_filename)
        if not os.path.exists(fingerprint_path):
            raise FileNotFoundError(f"Fingerprint file not found at: {fingerprint_path}")
    
        with open(fingerprint_path, 'r', encoding='utf-8') as f:
            fingerprint_data = json.load(f)

    # 2. Build the prompt and get the script from AI
    prompt = build_login_script_prompt(login_url, login_instructions, fingerprint_data, username=username, password=password)
    
    try:
        logger.info("Sending request to generative AI for login script...")
        response = model.generate_content(prompt)
        login_script_body = response.text.strip().removeprefix("```python").removesuffix("```").strip()

        # Indent the AI-generated script body to fit inside the function template.
        indented_script_body = textwrap.indent(login_script_body, ' ' * 4)

        # Create the full script by formatting the template.
        full_script = _SCRIPT_TEMPLATE.format(script_body=indented_script_body)

        logger.info(f"Generated login script to be executed:\n{full_script}")

        script_namespace = {}
        exec(full_script, globals(), script_namespace)
        perform_login_func = script_namespace['perform_login']

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            context = browser.new_context()
            page = context.new_page()
            page.goto(login_url)
            perform_login_func(page)
            context.storage_state(path=config.AUTH_STATE_PATH)
            logger.info(f"Authentication state saved to {config.AUTH_STATE_PATH}")
            page.wait_for_timeout(3000) # Give user a moment to see the result
            browser.close()
    except Exception as e:
        logger.error(f"Failed to create automated auth state: {e}", exc_info=True)
        raise