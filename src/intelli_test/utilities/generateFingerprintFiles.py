import google.generativeai as genai
import json
import logging
import os
from playwright.sync_api import sync_playwright, Page

from . import config, htmlSimplifier

# --- Configuration ---
# Set up logging to see the script's progress and any potential issues.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configure the generative AI model
genai.configure(api_key=config.API_KEY)
model = genai.GenerativeModel(model_name=config.MODEL_NAME)

def build_locator_prompt(simplified_html: str) -> str:
    """
    Constructs the detailed prompt to send to the generative AI.
    """
    return f"""
    You are an expert test automation engineer. Your task is to analyze the provided simplified HTML and generate a JSON object containing stable, unique, and interactable locators for the key elements on the page.

    **Instructions:**
    1.  The JSON output must be a single object.
    2.  Each key in the object should be a descriptive, snake_case name for the element (e.g., `email_field`, `login_button`).
    3.  Each value must be an object containing:
        - `primary_selector`: The best, most stable CSS selector. The selector MUST be specific enough to uniquely identify a single element.
        - `tag`: The HTML tag name of the element (e.g., "input", "button").
        - `text`: The visible text of the element, if any.

    **Selector Strategy:**
    - **Priority:** Prefer `[data-testid]`, then `id`, then a combination of other unique attributes like `name`, `type`, or `aria-label`.
    - **Specificity:** Combine attributes to ensure uniqueness. For example, instead of just `input[name='email']`, use `input[name='email'][type='email']` if it helps.
    - **Interactability:** For elements like `<input>`, `<textarea>`, and `<button>`, the generated selector should point to an element that is NOT `readonly` or `disabled`. If multiple elements match a potential selector (e.g., two inputs with `id="email"`), create a selector for the one that is interactable. For example: `input#email:not([readonly])`.

    **Example Output Format:**
    {{
      "email_field": {{
        "primary_selector": "input#email:not([readonly])",
        "tag": "input",
        "text": ""
      }},
      "login_button": {{
        "primary_selector": "button[data-test='login-submit']",
        "tag": "button",
        "text": "Login"
      }}
    }}

    **Simplified HTML from the Target Page:**
    ```html
    {simplified_html}
    ```

    **Generated JSON Locators:**
    """


def generate_locators_for_page(page: Page, output_path: str):
    """
    Orchestrates the process: simplifies HTML, queries the AI, and saves the result.
    """
    logger.info(f"Starting locator generation for page: {page.title()}")
    
    # Wait for the page to be fully loaded to ensure all dynamic content is present.
    page.wait_for_load_state('networkidle', timeout=50000)
    
    simplified_html = htmlSimplifier.simplify_html(page)
    if not simplified_html:
        logger.error("HTML simplification returned an empty string. Cannot proceed.")
        return

    prompt = build_locator_prompt(simplified_html)

    try:
        logger.info("Sending request to generative AI. This may take a moment...")
        generation_config = genai.types.GenerationConfig(response_mime_type="application/json")
        response = model.generate_content(prompt, generation_config=generation_config)
        raw_text = response.text

        # Clean the response to remove markdown fences and other unwanted characters.
        cleaned_text = raw_text.strip().removeprefix("```json").removesuffix("```").strip()
        logger.info("Successfully received and cleaned AI response.")

        # Parse the cleaned JSON string.
        locators = json.loads(cleaned_text)

        # Save the generated locators to the specified file.
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(locators, f, indent=2)
        
        logger.info(f"Successfully saved locators to {output_path}")

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from AI response: {e}")
        logger.error(f"Invalid JSON string received: {cleaned_text}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during AI query or file saving: {e}")


def generate_fingerprint_file(page: Page, target_url: str, output_file: str, auth_file_path: str | None = None):
    """
    Generate fingerprint file for a specified page, optionally using saved authentication state.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # Use authentication state if provided to create a pre-authenticated context.
        context_options = {}
        if auth_file_path and os.path.exists(auth_file_path):
            context_options['storage_state'] = auth_file_path
            logger.info(f"Loading authentication state from: {auth_file_path}")
        
        context = browser.new_context(**context_options)
        page = context.new_page()
        
        logger.info(f"Navigating to {target_url}...")
        page.goto(target_url)
        
        generate_locators_for_page(page, output_file)
        
        browser.close()
