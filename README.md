# intelliTest: AI-Powered Test Automation Toolkit

`intelliTest` is a powerful and flexible testing toolkit for Python that leverages Generative AI to streamline and enhance web test automation with Playwright. It provides a suite of utilities to automatically generate element locators, write tests from natural language, and perform visual regression checks.

## Core Features

*   🤖 **AI-Driven Test Execution**: Write test steps in plain English (e.g., "log in with user X and password Y") and have the AI convert them into executable Playwright actions.
*   👆 **Automatic Element Fingerprinting**: Point the tool at a URL, and it will use an LLM to analyze the page and generate a JSON map of stable, human-readable element locators.
*   🩹 **Self-Healing Selectors**: Use the generated "fingerprints" to reliably find elements. If a primary selector fails, the system automatically searches for the best alternative, making your tests more resilient to UI changes.
*   🖼️ **Visual Regression Testing**: Automatically capture and compare screenshots to catch unintended visual changes in your application.

## How It Works

The toolkit is composed of several independent but complementary utilities:

1.  **Generate Fingerprints**: Run the `generateFingerprintFiles.py` script against your web application's pages. This creates JSON files in the `elements/` directory, which act as a "page object model" for your elements.
2.  **Write Tests**:
    *   **Traditional Approach**: Write `pytest` tests using `playwright`. Instead of hardcoding selectors, use the `smartElementFinder` utility to look up elements by their logical name (e.g., `login_button`). Use `imageComparison` to add visual checks. (See `tests/test_login.py` for an example).
    *   **AI-Driven Approach**: Write `pytest` tests that define a high-level user command in plain English. The `genAITestGenerator` utility will convert this command into a series of browser actions and execute them. (See `tests/test_ai_generated.py` for an example).
3.  **Run Tests**: Execute your test suite using `pytest`.

## Getting Started

### Prerequisites

*   Python 3.8+
*   `pip` and `venv`

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd intelliTest
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    The project uses a `.env` file for configuration, such as API keys and base URLs. Copy the example file and fill in your values.
    ```bash
    cp .env.example .env
    ```
    You will need to edit `.env` with your `GENAI_API_KEY` and other project-specific values.

## Utilities Overview

All core logic is located in the `utilities/` directory.

### `generateFingerprintFiles.py`

This script automates the creation of element locator maps ("fingerprints").

*   **Usage**: Call the `generate_fingerprint_file` function from another script, passing a target URL and an output file path.
*   **Process**: It navigates to the URL, simplifies the page's HTML, sends it to a Generative AI to identify key elements and stable CSS selectors, and saves the result as a JSON file in the `elements/` directory.

### `genAITestGenerator.py`

This utility translates natural language commands into Playwright test steps.

*   **Usage**: Call `executeGenAITest(page, user_command)` from within a test.
*   **Process**: It takes the current page state and a user command, queries an AI model to convert the command into a JSON list of actions (e.g., `navigate`, `fill`, `click`), and executes them sequentially.

### `smartElementFinder.py`

Provides a robust, self-healing method for locating elements on a page.

*   **Usage**: Call `find_element_smart(page, 'category', 'element_key')`. The `category` corresponds to a JSON file in `elements/` (e.g., `loginPage`), and `element_key` is the logical name of the element (e.g., `email_field`).
*   **Process**: It first tries to find an element using its primary selector from the JSON file. If that fails, it initiates a "self-healing" search, looking for other elements of the same type and scoring them based on text content to find the best match.

### `imageComparison.py`

Handles visual regression testing.

*   **Usage**: Call `compare_test_run_images(page, request)` from a `pytest` test.
*   **Process**: It takes a screenshot and compares it to a baseline image using the Structural Similarity Index (SSIM). If no baseline exists, it creates one. Your test can then assert that the similarity score is above a defined threshold.
