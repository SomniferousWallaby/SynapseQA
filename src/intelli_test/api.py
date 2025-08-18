# api/main.py
import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Import the router objects from your new files
from .routers import generation, auth, files, tests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="intelliTest API",
    description="API for orchestrating AI-powered web testing.",
    version="1.0.0"
)

# --- Middleware Configuration ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Include Routers ---
app.include_router(generation.router)
app.include_router(auth.router)
app.include_router(files.router)
app.include_router(tests.router)


# --- Static Files Mount (for Production) ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
static_files_path = os.path.join(project_root, 'frontend', 'build')

if os.path.isdir(static_files_path):
    app.mount("/", StaticFiles(directory=static_files_path, html=True), name="static-root")
    logger.info(f"Serving static production build from: {static_files_path}")
else:
    logger.warning(f"Static production build directory not found at '{static_files_path}'.")


# --- Root Endpoint ---
@app.get("/")
def read_root():
    return {"message": "Welcome to the intelliTest API. Visit /docs for documentation."}