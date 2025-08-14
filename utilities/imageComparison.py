from skimage.metrics import structural_similarity as ssim
import cv2
import os
import shutil
import pytest
import logging
from playwright.sync_api import Page

logger = logging.getLogger(__name__)

# --- Path Constants ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES_FOLDER = os.path.join(PROJECT_ROOT, 'images')

def compare_images(image1, image2):
    ''' 
    Compares two images and returns a score and a difference value.
    A score of 1.0 indicates a perfect match.
    '''
    baseline = cv2.imread(image1)
    current = cv2.imread(image2)

    baseline_grayscale = cv2.cvtColor(baseline, cv2.COLOR_BGR2GRAY)
    current_grayscale = cv2.cvtColor(current, cv2.COLOR_BGR2GRAY)

    (score, diff) = ssim(baseline_grayscale, current_grayscale, full=True)
    diff = (diff * 255).astype("uint8")

    return score, diff

def take_screenshot(page: Page, request: pytest.FixtureRequest):
    '''
    Takes a screenshot and save it to the images folder.
    Uses the name of the current running test to identify it.
    '''
    currentTestName = request.node.name
    screenshot_path = os.path.join(IMAGES_FOLDER, f"{currentTestName}_current.png")
    page.screenshot(path=screenshot_path)
    logger.info(f"Screenshot saved to: {screenshot_path}")


def compare_test_run_images(page: Page, request: pytest.FixtureRequest):
    '''
    Compares a baseline images with the current image generated
    by a test. If no baseline image exists, it creates one.
    '''
    currentTestName = request.node.name
    baseline = os.path.join(IMAGES_FOLDER, f"{currentTestName}_baseline.png")
    current = os.path.join(IMAGES_FOLDER, f"{currentTestName}_current.png")

    if not os.path.exists(current):
        logger.info("Current image not found. Taking screenshot of current state...")
        take_screenshot(page, request)

    if not os.path.exists(baseline):
        logger.info(f"Baseline image not found. Creating...")
        shutil.copy(current, baseline)
        return (1, 0)
    return (compare_images(baseline, current))