import json
import os
import logging
from playwright.sync_api import Page, Locator, TimeoutError

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FINGERPRINTS_FOLDER = os.path.join(PROJECT_ROOT, 'elements')

logger = logging.getLogger(__name__)

# --- Fingerprint Caching ---
FINGERPRINTS_CACHE = {}

def _load_fingerprints(category: str):
    """Loads and caches element definitions from a JSON file to avoid re-reading."""
    if category in FINGERPRINTS_CACHE:
        return FINGERPRINTS_CACHE[category]

    fingerprints_file = os.path.join(FINGERPRINTS_FOLDER, f"{category}.json")
    logger.info(f"Loading element definitions from: {fingerprints_file}")
    try:
        with open(fingerprints_file, 'r') as f:
            fingerprints = json.load(f)
            FINGERPRINTS_CACHE[category] = fingerprints
            return fingerprints
    except FileNotFoundError as e:
        error_msg = f"The element definition file was not found at: {fingerprints_file}"
        logger.error(error_msg, exc_info=True)
        raise FileNotFoundError(error_msg) from e
    except json.JSONDecodeError as e:
        error_msg = f"The definition file at {fingerprints_file} is not a valid JSON file."
        logger.error(error_msg, exc_info=True)
        raise ValueError(error_msg) from e

def find_element_smart(page: Page, elements_category: str, element_key: str) -> Locator:
    """
    Finds a Playwright Locator using a primary selector, with a self-healing
    fallback that logs its actions.
    """
    FINGERPRINTS = _load_fingerprints(elements_category)
    try:
        # The fingerprint file now has a root 'elements' key.
        elements = FINGERPRINTS.get("elements", {})
        if not elements:
            raise KeyError(f"No 'elements' found in fingerprint file for '{elements_category}'. The file might be malformed.")
        fingerprint = elements[element_key]
    except KeyError as e:
        error_msg = f"Element key '{element_key}' not found within the 'elements' of category '{elements_category}'."
        logger.error(error_msg)
        raise KeyError(error_msg) from e

    # 1. Try the primary selector first.
    primary_locator = page.locator(fingerprint["primary_selector"])
    try:
        primary_locator.wait_for(state="attached", timeout=2000)
        logger.info(f"Found element '{element_key}' using primary selector.")
        return primary_locator
    except TimeoutError:
        logger.warning(f"Primary locator for '{element_key}' failed. Attempting self-healing search (smart matching).")

    # 2. If it fails, search for candidates using locators and score them.
    candidates_locator = page.locator(fingerprint["tag"])
    best_candidate_locator = None
    highest_score = -1

    for i in range(candidates_locator.count()):
        candidate_locator = candidates_locator.nth(i)
        # Scoring based on text match.
        score = 10 if candidate_locator.inner_text().strip() == fingerprint.get("text") else 0
        if score > highest_score:
            highest_score = score
            best_candidate_locator = candidate_locator

    if best_candidate_locator:
        logger.info(f"Self-healed! Found locator for '{element_key}' using fallback search: ${best_candidate_locator}")
        return best_candidate_locator

    error_msg = f"Could not find or heal locator for element: '{element_key}'"
    logger.error(error_msg)
    raise TimeoutError(error_msg)