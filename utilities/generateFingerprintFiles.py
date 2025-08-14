import google.generativeai as genai
import json
import logging
import os
from playwright.sync_api import sync_playwright, Page
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# --- Configuration ---
# Set up logging to see the script's progress and any potential issues.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from a .env file.
load_dotenv()

API_KEY = os.getenv("GENAI_API_KEY")
MODEL_NAME = os.getenv("MODEL")

if not API_KEY or not MODEL_NAME:
    raise ValueError("GENAI_API_KEY and MODEL must be set in your .env file.")

# Configure the generative AI model
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel(model_name=MODEL_NAME)


# --- Core Functions ---

def simplify_html_for_locators(page: Page) -> str:
    """
    Strips HTML down to its essential interactive elements and their attributes.
    This simplified version is easier for the LLM to process accurately.
    """
    try:
        html_content = page.content()
        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove tags that don't contain user-facing content.
        for tag in soup(["script", "style", "meta", "link", "path", "svg"]):
            tag.decompose()

        simplified_tags = []
        # Find all potentially interactive or significant elements.
        for tag in soup.find_all(["a", "button", "input", "textarea", "select", "h1", "h2", "h3", "label", "div", "span", "p"]):
            attrs = {
                "id": tag.get("id"),
                "class": " ".join(tag.get("class", [])),
                "name": tag.get("name"),
                "placeholder": tag.get("placeholder"),
                "aria-label": tag.get("aria-label"),
                "data-testid": tag.get("data-testid"),
                "role": tag.get("role"),
                "type": tag.get("type"),
                "href": tag.get("href")
            }
            text = ' '.join(tag.stripped_strings)
            tag_name = tag.name
            clean_attrs = {k: v for k, v in attrs.items() if v}
            attr_str = " ".join([f'{k}="{v}"' for k, v in clean_attrs.items()])
            
            # Construct the simplified tag string.
            full_tag_str = f"<{tag_name} {attr_str}>"
            if text:
                full_tag_str += f"{text}</{tag_name}>"
            
            simplified_tags.append(full_tag_str)

        logger.info(f"Simplified HTML to {len(simplified_tags)} elements for AI context.")
        return "\n".join(simplified_tags)
    except Exception as e:
        logger.error(f"An error occurred during HTML simplification: {e}")
        return ""


def build_locator_prompt(simplified_html: str) -> str:
    """
    Constructs the detailed prompt to send to the generative AI.
    """
    return f"""
    You are an expert test automation engineer. Your task is to analyze the provided simplified HTML and generate a JSON object containing stable locators for the key interactive and informational elements on the page.

    **Instructions:**
    1.  The JSON output must be a single object.
    2.  Each key in the object should be a descriptive, snake_case name for the element (e.g., `email_field`, `login_button`).
    3.  Each value must be an object containing:
        - `primary_selector`: The best, most stable CSS selector (prefer `[data-testid]`, then `id`, then other unique attributes).
        - `tag`: The HTML tag name of the element (e.g., "input", "button").
        - `text`: The visible text of the element, if any.

    **Example Output Format:**
    {{
      "email_field": {{
        "primary_selector": "#email",
        "tag": "input",
        "text": ""
      }},
      "login_button": {{
        "primary_selector": "[data-test='login-submit']",
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
    page.wait_for_load_state('networkidle', timeout=10000)
    
    simplified_html = simplify_html_for_locators(page)
    if not simplified_html:
        logger.error("HTML simplification returned an empty string. Cannot proceed.")
        return

    prompt = build_locator_prompt(simplified_html)

    try:
        logger.info("Sending request to generative AI. This may take a moment...")
        response = model.generate_content(prompt)
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


def generate_fingerprint_file(page: Page, target_url, output_file):
    """
    Generate fingerprint file for specified page
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        logger.info(f"Navigating to {target_url}...")
        page.goto(target_url)
        
        generate_locators_for_page(page, output_file)
        
        browser.close()
