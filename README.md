# intelliTest: AI-Powered Test Automation

`intelliTest` is a testing toolkit that leverages Generative AI to accelerate web testing with Playwright.<br>
It features an interactive web dashboard that allows you to generate element locators, create complete test files from natural language, and handle authenticated sessions seamlessly.

<p align="left">
  <img src="dashboard.png" alt="intelliTest Dashboard" width="700"/>
</p>

## Core Features

*   🚀 **Interactive Web Dashboard**: A user-friendly UI (powered by React and FastAPI) to manage all testing tasks from your browser.
*   🤖 **AI-Powered Test Generation**: Describe a test in plain English (e.g., "verify that an invalid login shows an error message") and have the AI write a complete, executable `pytest` file.
*   👆 **Intelligent Element Fingerprinting**: Automatically scan a web page to generate a JSON map of stable, human-readable element locators, making your tests more resilient to UI changes.
*   🔒 **Flexible Authentication**: Use the UI to automatically generate an authentication state. Run the browser in headless or headed mode, and provide credentials on-the-fly or use defaults from your environment.
*   🧩 **Fixture-Aware Test Generation**: The AI is smart enough to use `pytest` fixtures (like `logged_in_page`) for tests that require a pre-authenticated state, resulting in cleaner, DRYer code.

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 1. Clone the Repository
```bash
git clone <your-repository-url>
cd intelliTest
```

### 2. Install Dependencies
Install both the Python backend and Node.js frontend dependencies.
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers (this is a required one-time setup)
playwright install

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### 3. Configure Environment Variables
Copy the example environment file and edit it with your specific details (API keys, URLs, etc.).
```bash
cp .env.example .env
```
Make sure to fill in `GENAI_API_KEY` and other relevant variables.

### 4. Run the Application
Use the provided development script to start both the frontend and backend servers. This script also handles port cleanup to prevent "Address already in use" errors.
```bash
# Make the script executable (one-time setup)
chmod +x start_dev.sh

# Run the development server
./start_dev.sh
```
Once running, open your browser and navigate to the frontend URL (typically `http://localhost:5173` or as indicated in your terminal).

## Workflow: Creating a Test with the UI

1.  **Set Authentication State**:
    -   In the dashboard, click "Set Auth State".
    -   Fill in the login URL and instructions for the AI.
    -   Optionally provide a username and password to override the defaults.
    -   Choose whether to run the browser in headless mode.
    -   Click "Generate Auth State". The application will automatically log in and save the session. The status on the dashboard will update, showing when the session expires.

2.  **Create a Page Fingerprint**:
    -   Click "Create New Fingerprint".
    -   Enter the URL of the page you want to test (e.g., a user profile page).
    -   Give it a descriptive output filename (e.g., `profilePage`).
    -   Check "Use Authenticated Session" if the page is behind a login.
    -   Click "Generate Fingerprint". This creates a JSON file in the `elements/` directory.

3.  **Generate a Test File**:
    -   Click "Create New Test".
    -   Describe the test you want to perform in plain English.
    -   Provide a valid Python filename (e.g., `test_profile_update.py`).
    -   Select the fingerprint file you created in the previous step.
    -   Check "Requires Login" if the test needs an authenticated session.
    -   Click "Generate Test".

4.  **Review and Run**:
    -   A new test file will appear in your `tests/` directory.
    -   You can review the AI-generated code and then run your entire test suite from the command line with `pytest`.

## For Advanced Users: API Endpoints

While the UI is the primary way to interact with `intelliTest`, all functionality is exposed via a RESTful API. You can view the interactive API documentation by navigating to `/docs` on the backend server (e.g., `http://127.0.0.1:8000/docs`). This is useful for scripting or custom integrations.

## Makefile for Development

For developers who prefer using `make`, a `Makefile.mk` is included to streamline common tasks.

*   **One-Command Setup**: Install all dependencies (Python, Node.js, and Playwright browsers) and set up the virtual environment.
    ```bash
    make -f Makefile.mk setup-dev
    ```
*   **Run the Test Suite**:
    ```bash
    make -f Makefile.mk test
    ```
*   **See all commands**:
    ```bash
    make -f Makefile.mk help
    ```
