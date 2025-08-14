# intelliTest: AI-Powered Test Automation Toolkit

`intelliTest` is a powerful testing toolkit that leverages Generative AI to automate web testing with Playwright. It is exposed via a RESTful API, allowing you to generate element locators, create complete test files from natural language, and handle authenticated sessions seamlessly.

## Core Features

*   🚀 **RESTful API**: An easy-to-use API (powered by FastAPI) to orchestrate all testing tasks.
*   🤖 **AI-Powered Test Generation**: Describe a test in plain English (e.g., "verify that an invalid login shows an error message") and have the AI write a complete, executable `pytest` file.
*   👆 **Intelligent Element Fingerprinting**: Automatically scan a web page to generate a JSON map of stable, human-readable element locators, making your tests more resilient to UI changes.
*   🔒 **Authenticated Session Handling**: Easily generate an authentication state file to run tests on pages that are behind a login wall.
*   🧩 **Fixture-Aware Test Generation**: The AI is smart enough to use `pytest` fixtures (like `logged_in_page`) for tests that require a pre-authenticated state, resulting in cleaner, DRYer code.
*   🖼️ **Visual Regression Testing**: Capture and compare screenshots to catch unintended visual changes in your application.

## Architecture

The project is built around a simple and powerful architecture:

1.  **Backend API (FastAPI)**: Exposes endpoints to trigger fingerprinting and test generation. It uses background tasks to handle long-running browser automation and AI queries without blocking.
2.  **AI Utilities (Python)**: A collection of scripts in the `utilities/` folder that contain the core logic for interacting with Playwright and the Generative AI model.
3.  **Frontend (Future)**: The API-first design makes it easy to build a user-friendly web interface on top of the backend.

## Getting Started
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    Copy the example environment file and edit it with your specific details (API keys, URLs, etc.).
    ```bash
    cp .env.example .env
    ```

5.  **Create Authentication State (Optional):**
    If you need to test pages behind a login, run this one-time script. It will open a browser, allow you to log in manually, and save your session to an `auth_state.json` file.
    ```bash
    python -m utilities.create_auth_state
    ```

6.  **Run the API Server:**
    ```bash
    uvicorn main:app --reload
    ```
    You can now access the interactive API documentation at `http://127.0.0.1:8000/docs`.

## Typical Workflow

1.  **(One-time setup)** If your site requires a login, run `python -m utilities.create_auth_state` to save your session.
2.  **Fingerprint a Page**: Send a request to the `POST /fingerprint` endpoint with the URL of a page you want to test (e.g., the account profile page). Set `use_authentication` to `true` if it's behind a login. This creates a file like `elements/profilePage.json`.
3.  **Generate a Test**: Send a request to the `POST /generate-test` endpoint. Provide a natural language `description` of the test, a `file_name` for the new test, the `fingerprint_filename` you just created, and set `requires_login` to `true`.
4.  **Review and Run**: A new test file will appear in your `tests/` directory. You can review the AI-generated code and then run it as part of your test suite with `pytest`.

## API Endpoints

The following endpoints are available. For detailed request models, see the interactive documentation at `/docs`.

### `POST /fingerprint`

Scans a web page and generates a JSON file of element locators.

*   **Request Body**:
    ```json
    {
      "url": "https://practicesoftwaretesting.com/#/account",
      "output_filename": "accountPage",
      "use_authentication": true
    }
    ```
*   **Action**: Triggers a background task to generate `elements/accountPage.json`.

### `POST /generate-test`

Generates a complete Python test file from a natural language description.

*   **Request Body**:
    ```json
    {
      "description": "A test that navigates to the user profile and verifies the first name field is visible.",
      "file_name": "test_verify_profile_name.py",
      "fingerprint_filename": "accountPage.json",
      "requires_login": true
    }
    ```
*   **Action**: Triggers a background task to create `tests/test_verify_profile_name.py` using the `logged_in_page` fixture and locators from `accountPage.json`.



