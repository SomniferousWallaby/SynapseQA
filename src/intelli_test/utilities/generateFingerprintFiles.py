import google.generativeai as genai
import json
import logging
import os
from playwright.sync_api import sync_playwright, Page
from intelli_test.utilities import config, htmlSimplifier

# Logging is configured at the application entry point (e.g., in api.py or conftest.py).
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


def generate_locators_for_page(page: Page, output_path: str, target_url: str):
    """
    Orchestrates the process: simplifies HTML, queries the AI, and saves the result.
    """
    logger.info(f"Starting locator generation for page: {page.title()}")
    
    # Wait for the page to be fully loaded to ensure all dynamic content is present.
    page.wait_for_load_state('domcontentloaded', timeout=50000)
    
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
        valid_json_string = cleaned_text.replace("\\\\'", "\'")

        parsed_json = json.loads(valid_json_string)
        logger.info("Successfully received and cleaned AI response.")

        # The AI sometimes wraps the response object in a list.
        # If it's a list with one dictionary inside, we can safely extract it.
        if isinstance(parsed_json, list) and len(parsed_json) == 1 and isinstance(parsed_json[0], dict):
            logger.warning("AI returned a list containing a single dictionary. Extracting the dictionary.")
            locators = parsed_json[0]
        elif isinstance(parsed_json, dict):
            locators = parsed_json
        else:
            # If it's neither a dictionary nor a list with one dictionary, then it's an invalid format.
            error_msg = (
                f"AI response was not in the expected format (a JSON object), but was type {type(parsed_json)}. "
                "The generated fingerprint file will not be saved. Please try again."
            )
            logger.error(error_msg)
            raise TypeError(error_msg)

        # Structure the final JSON to include the URL and the element locators.
        data_to_save = {
            "url": target_url,
            "elements": locators
        }
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        # Save the generated locators to the specified file.
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, indent=2)
        
        logger.info(f"Successfully saved locators to {output_path}")

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from AI response: {e}")
        logger.error(f"Invalid JSON string received: {valid_json_string}")
        raise TypeError(e)
    except Exception as e:
        logger.error(f"An unexpected error occurred during AI query or file saving: {e}")
        raise e




def generate_fingerprint_file(target_url: str, output_file: str, use_authentication: bool = False, allow_redirects: bool = False):
    """
    Generate fingerprint file for a specified page, optionally using saved authentication state.
    This function manages its own Playwright instance.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # Use authentication state if provided to create a pre-authenticated context.
        context_options = {}

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..','..'))
        auth_path = os.path.join(project_root, 'auth_state.json')

        if use_authentication and os.path.exists(auth_path):
            context_options['storage_state'] = auth_path
            logger.info(f"Loading authentication state from: {auth_path}")
        elif use_authentication and not os.path.exists(auth_path):
            raise RuntimeError(f"Authentication requested, but auth file not found at: {auth_path}")
        else:
            logger.warning("No authentication state provided or file not found. Proceeding without authentication.")
        
        context = browser.new_context(**context_options)
        page = context.new_page()
        
        logger.info(f"Navigating to {target_url}...")
        page.goto(target_url)
        page.wait_for_load_state('domcontentloaded')

        # Verify that we landed on the correct page and were not redirected.
        if target_url != page.url and not allow_redirects:
            error_msg = (
                f"Fingerprint generation failed. Navigated to '{target_url}' but was redirected to'{page.url}'. "
                "Your 'auth_state.json' may be expired or invalid. "
                "Please regenerate it by running 'python -m utilities.create_auth_state'."
            )
            logger.error(error_msg)
            browser.close()
            raise RuntimeError(error_msg)
        elif allow_redirects and target_url != page.url:
            logger.info(f"Allowing redirects. Navigated to '{target_url}' but was redirected to'{page.url}'.")
        
        generate_locators_for_page(page, output_file, target_url)
        
        browser.close()
