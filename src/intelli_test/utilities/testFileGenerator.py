import google.generativeai as genai
import logging
import os
from . import config
import json

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# Configure the generative AI model
genai.configure(api_key=config.API_KEY)
model = genai.GenerativeModel(model_name=config.MODEL_NAME)
logger = logging.getLogger(__name__)

def get_available_page_objects():
    """Scans the elements directory to find available page object models."""
    elements_dir = os.path.join(PROJECT_ROOT, 'elements')
    if not os.path.isdir(elements_dir):
        return []
    return [f.removesuffix('.json') for f in os.listdir(elements_dir) if f.endswith('.json')]

def build_test_file_prompt(description: str, fingerprint_filename: str | None = None, requires_login: bool = False) -> str:
    """Constructs the prompt for generating a complete Python test file."""

    fixture_name = "logged_in_page" if requires_login else "page"
    login_instructions = ""
    if requires_login:
        login_instructions = f"""4.  The test function MUST accept the `{fixture_name}: Page` fixture. This fixture handles user login, so DO NOT add any login steps. Use `{fixture_name}` for all subsequent browser interactions."""
    else:
        login_instructions = f"""4.  The test function must accept the `{fixture_name}: Page` and `request: pytest.FixtureRequest` fixtures."""

    navigation_instruction = f"5.  Use `{fixture_name}.goto()` for navigation. For example: `{fixture_name}.goto(f\"{{config.BASE_URL}}{{config.LOGIN_PAGE_PATH}}\")`."
    page_object_context = ""
    page_object_name = "the relevant page"

    # If a specific fingerprint file is provided, use its content to build a precise prompt.
    if fingerprint_filename:
        fingerprint_path = os.path.join(PROJECT_ROOT, 'elements', fingerprint_filename)
        try:
            with open(fingerprint_path, 'r', encoding='utf-8') as f:
                elements_json = json.load(f)
            
            page_url = elements_json.get("url")
            elements = elements_json.get("elements", {})

            if page_url:
                # If a URL is found in the fingerprint, create a direct navigation instruction.
                navigation_instruction = f"5.  The test MUST begin by navigating to the page's specific URL. Use `{fixture_name}.goto('{page_url}')`."

            
            elements_str = json.dumps(elements, indent=2)
            page_object_name = fingerprint_filename.removesuffix('.json')

            page_object_context = f"""
**Available Elements for '{page_object_name}':**
```json
{elements_str}
```
"""
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Could not load provided fingerprint file '{fingerprint_filename}': {e}. Falling back to listing all available page objects.")
            fingerprint_filename = None # Clear filename to trigger fallback

    # Fallback/old logic: List all available page objects if no specific file is given or if it fails to load.
    if not fingerprint_filename:
        page_objects = get_available_page_objects()
        page_objects_list = ", ".join([f"'{name}'" for name in page_objects]) if page_objects else "none"
        page_object_context = f"""- The available `page_object_name`s are: [{page_objects_list}]. You must infer the correct one."""

    return f"""
You are an expert Python test automation engineer specializing in Playwright and pytest. Your task is to write a complete Python test file based on a user's description.

**Instructions:**
1.  The output must be a single block of raw Python code. Do not include any explanations or markdown formatting like ```python.
2.  The test file must include these imports: `pytest`, `logging`, `from playwright.sync_api import Page, expect`, and `from utilities import smartElementFinder, config`.
3.  Define a single test function that starts with `test_`. The function name should be descriptive and in snake_case.
{login_instructions}
{navigation_instruction}
6.  **Crucially, you MUST use `smartElementFinder.find_element_smart({fixture_name}, 'page_object_name', 'element_key')` to locate ALL elements.**
    {page_object_context}
7.  Use `expect()` from Playwright for all assertions. For example: `expect(locator).to_be_visible()` or `expect({fixture_name}).to_have_url(...)`.
8.  If the test does NOT require login (i.e., it uses the `page` fixture), use `config.TEST_USER` and `config.PASSWORD` for credentials if the description implies a login action.

**User's Test Description:**
"{description}"

**Generated Python Code:**
"""

def generate_test_file(description: str, file_name: str, fingerprint_filename: str | None = None, requires_login: bool = False):
    """Generates a test file from a description and saves it."""
    logger.info(f"Starting test file generation for: {file_name}")
    
    prompt = build_test_file_prompt(description, fingerprint_filename=fingerprint_filename, requires_login=requires_login)
    
    try:
        logger.info("Sending request to generative AI for test file generation...")
        response = model.generate_content(prompt)
        generated_code = response.text.strip()

        # Clean the response to remove markdown fences, which the model sometimes adds despite instructions.
        if generated_code.startswith("```python"):
            generated_code = generated_code.removeprefix("```python").strip()
        if generated_code.endswith("```"):
            generated_code = generated_code.removesuffix("```").strip()

        if not generated_code.startswith("import"):
            raise ValueError("Generated response does not appear to be valid Python code.")

        output_path = os.path.join(PROJECT_ROOT, 'tests', file_name)
        
        # Ensure the output directory exists before writing the file.
        output_dir = os.path.dirname(output_path)
        os.makedirs(output_dir, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(generated_code)
        
        logger.info(f"Successfully generated and saved test file to {output_path}")

    except Exception as e:
        logger.error(f"Failed to generate test file '{file_name}': {e}", exc_info=True)