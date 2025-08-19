# intelliTest

> AI-powered test automation for web applications.

intelliTest is a full-stack application designed to streamline web testing by leveraging generative AI. It provides a user-friendly dashboard to automatically generate page element "fingerprints", write `pytest` tests from natural language descriptions, and run/manage your entire test suite without leaving the browser.

## Table of Contents

  * [Features](#features)
  * [Tech Stack](#tech-stack)
  * [Prerequisites](#prerequisites)
  * [Installation & Setup](#installation-&-usage-with-make-recommended)
  * [Running the Application](#running-the-application)
  * [How to Use](#how-to-use)
  * [Project Structure](#project-structure)

-----

## Features

  * **AI-Powered Page Fingerprinting:** Analyzes a URL and generates a stable JSON object of key UI element locators.
  * **Natural Language Test Generation:** Generates complete `pytest` and Playwright test files from a simple English description of a user action.
  * **Interactive Test Runner:** Run individual test files or the entire test suite with the click of a button directly from the dashboard.
  * **Detailed Test Result Viewer:** View a summary and detailed traceback for failed tests in a clean, color-coded modal.
  * **Authentication State Management:** Log in to your target application once and save the session state to be reused by tests that require authentication.
  * **Simple File Management:** View and delete generated test files, fingerprints, and test reports from the UI.

-----

## Tech Stack

  * **Backend:** Python, FastAPI, Playwright, pytest, Google Generative AI
  * **Frontend:** React, Vite

-----

## Prerequisites

Before you begin, ensure you have the following installed:

  * Python 3.10+
  * Node.js 18+
  * An active Google AI API Key.

-----

## Installation & Usage with Make (Recommended)

This project includes a `Makefile` to automate setup and common development tasks.

### 1\. Prerequisites

  - Ensure you have `make`, Python 3.10+, and Node.js 18+ installed.
  - Create a `.env` file in the project root. You can copy the `env.example` file if it exists.
  - Add your Google AI API key to the `.env` file:
    ```
    API_KEY="YOUR_GOOGLE_AI_API_KEY_HERE"
    ```

-----

### 2\. One-Step Development Setup

Run the following command from the project root. This single command will create the Python virtual environment, install all backend and frontend dependencies, and download the necessary Playwright browsers.

```bash
make setup-dev
```

After the setup is complete, activate the Python virtual environment to use the installed tools:

```bash
source venv/bin/activate
```

-----

### 3\. Running the Application

#### Using the start_dev.sh script
1. Make the startup script executable 
    ```bash chmod +x start_dev.sh```
2. Run the script
    `./start_dev.sh`


#### Using make
You'll need two separate terminals to run the backend and frontend servers.

**Start the Backend Server:**

```bash
make api
```

**Start the Frontend Server:**
(From the `frontend/` directory)

```bash
npm run dev
```

The application will now be running with the API at `http://127.0.0.1:8000` and the UI at `http://localhost:5174` (or a similar port).

-----

### Other Useful Commands

  * `make test`: Run the entire `pytest` suite.
  * `make clean`: Remove all generated files, including the Python virtual environment, `node_modules`, and cached files. This is useful for a fresh start.
  * `make help`: Display a list of all available commands and their descriptions.

-----

## Manual Installation and Usage

### Backend Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd intelliTest
    ```
2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```
3.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Set up environment variables:**
      * Create a file named `.env` in the project's root directory.
      * Add your Google AI API key to it:
        ```
        API_KEY="YOUR_GOOGLE_AI_API_KEY_HERE"
        ```

### Frontend Setup

1.  **Navigate to the frontend directory:**
    ```bash
    cd frontend
    ```
2.  **Install Node.js dependencies:**
    ```bash
    npm install
    ```

-----

## Running the Application

You'll need to run the backend and frontend servers in two separate terminals.

1.  **Start the Backend Server**

      * From the **project root** directory, run:

    <!-- end list -->

    ```bash
    uvicorn src.intelli_test.main:app --reload
    ```

      * The API will be available at `http://127.0.0.1:8000`.

2.  **Start the Frontend Dev Server**

      * From the **`frontend/`** directory, run:

    <!-- end list -->

    ```bash
    npm run dev
    ```

      * The dashboard will be available at `http://localhost:5174` (or whatever port Vite assigns).

-----

## How to Use

### 1\. Set Authentication State (First-Time Use)

Initial versions only support Google Gemini Flash 2.0 Models, so please configure an API Key that has access to that model.

For testing applications that require a login, the first step is to create an `auth_state.json` file.

  * Click the **Set Auth State** button.
  * Fill in the login URL and provide simple, step-by-step instructions for the AI to follow (e.g., "Enter the username into the email field, enter the password into the password field, then click the login button.").
  * Click **Generate Auth State**. This will open a browser, log in, and save the session cookies and local storage.

### 2\. Fingerprint a Page

To make test generation more accurate, create a fingerprint of the page you want to test.

  * In the "Available Page Fingerprints" panel, click **Create New Fingerprint**.
  * Enter the URL of the page and an output filename.
  * If the page requires a login to access, check the "Use Authenticated Session" box.
  * Click **Generate Fingerprint**.

### 3\. Generate a Test

  * In the "Available Tests" panel, click **Create New Test**.
  * Write a clear, simple description of the test you want to perform (e.g., "Verify that a user can search for 'puppies' and see results.").
  * Provide a valid Python filename (e.g., `test_puppy_search.py`).
  * Optionally, select the fingerprint file for the page you are testing.
  * Click **Generate Test**.

### 4\. Run Tests & View Results

  * **Run a single test:** Click the green "play" icon next to any test in the "Available Tests" panel.
  * **Run all tests:** Click the yellow "Run All" button at the top of the "Available Tests" panel.
  * **View results:** After a test run, a new entry will appear in the "Test Results" panel. Click the "view" icon to see a detailed report, including tracebacks for any failures.

-----

## Project Structure

```
/
├── elements/      # Stores AI-generated page fingerprints (.json)
├── frontend/      # React UI source code
├── reports/       # Stores test run results (.json)
├── src/
│   └── intelli_test/  # Backend FastAPI application source
└── tests/         # Stores AI-generated pytest files (.py)
```