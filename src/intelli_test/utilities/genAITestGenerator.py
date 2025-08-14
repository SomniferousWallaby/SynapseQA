import google.generativeai as genai
import json
import logging
from playwright.sync_api import Page
from utilities import htmlSimplifier, config

logger = logging.getLogger(__name__)
genai.configure(api_key=config.API_KEY)
model = genai.GenerativeModel(model_name=config.MODEL_NAME)

def buildPrompt(user_command, simplifiedHTML):
    prompt = f"""
    You are an expert test automation engineer. Your task is to convert a user's command into a sequence of Playwright actions in JSON format.
    The available actions are: "navigate", "fill", "click".
    The JSON output should be a list of objects, where each object has an "action", a "selector", and an optional "value".
    The JSON should be a raw string, without any markdown formatting.
    For the selector, infer the most likely CSS selector.
    Simplified HTML tags for the page in question are here: {simplifiedHTML}

    Example:
    User command: "go to the login page, fill in the email with 'test@example.com', and click the login button"
    JSON output:
    [
        {{"action": "navigate", "selector": "auth/login", "value": ""}},
        {{"action": "fill", "selector": "#email", "value": "test@example.com"}},
        {{"action": "click", "selector": "[data-test='login-submit']", "value": ""}}
    ]

    User command: "{user_command}"
    JSON output:
    """
    return prompt


def queryGenAI(user_command, simplifiedHTML):
    """
    Queries the generative AI, cleans the response, and parses it into a Python list.
    Returns a list of action dictionaries or None if parsing fails.
    """
    prompt = buildPrompt(user_command, simplifiedHTML)
    generation_config = genai.types.GenerationConfig(response_mime_type="application/json")
    response = model.generate_content(prompt, generation_config=generation_config)
    raw_text = response.text

    # Clean the response text to remove markdown fences and leading/trailing whitespace
    cleaned_text = raw_text.strip().removeprefix("```json").removesuffix("```").strip()
    logger.info(f"Cleaned JSON for parsing: {cleaned_text}")

    try:
        # Parse the cleaned JSON string into a Python object
        return json.loads(cleaned_text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from AI response: {e}")
        logger.error(f"Invalid JSON string was: {cleaned_text}")
        return None
    

def executeGenAITest(page: Page, user_command):
    page.wait_for_load_state('networkidle', timeout=50000)
    pageContext = htmlSimplifier.simplify_html(page)
    actions = queryGenAI(user_command, pageContext)

    if not actions:
        raise ValueError("Failed to generate or parse test steps from the AI model. Check the logs.")

    # Iterate through the parsed actions and execute them
    for step in actions:
        action = step.get("action")
        selector = step.get("selector")
        value = step.get("value", "")  # Default to empty string if not present

        logger.info(f"Executing: {action} on '{selector}' with value '{value}'")

        try:
            if action == "navigate":
                page.goto(f"{config.BASE_URL}{selector}")
            elif action == "fill":
                page.locator(selector).fill(value)
            elif action == "click":
                page.locator(selector).click()
            else:
                logger.warning(f"Unknown action '{action}' received from AI. Skipping.")
        except Exception as e:
            raise RuntimeError(f"Failed to execute AI-generated step {step}: {e}") from e