import logging
import uuid
from fastapi import APIRouter, BackgroundTasks, HTTPException
from intelli_test.schemas import FingerprintRequest, TestGenerationRequest
from intelli_test.tasks import run_fingerprint_generation, run_test_generation

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/generate",  # Common prefix for all routes in this file
    tags=["Generation"]  # Groups endpoints in the API docs
)

# Dictionary to store running tasks
# TODO: Repace with Redis or another persistent store for production
tasks = {}

def run_task_wrapper(task_id:str, func, *args, **kwargs):
    """
    Wrapper to run a task in the background with a unique ID.
    """
    logger.info(f"Starting task {task_id} with args: {args}, kwargs: {kwargs}")
    try:
        func(*args, **kwargs)
        tasks[task_id]['status'] = 'complete'
    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        tasks[task_id]['status'] = 'failed'

@router.post("/test", status_code=202)
async def create_test_file(request: TestGenerationRequest, background_tasks: BackgroundTasks):
    """
    Accepts a natural language description and generates a new Python test file.
    """
    file_name = request.file_name
    # Basic security and validation
    if not file_name.startswith("test_") or not file_name.endswith(".py"):
        raise HTTPException(
            status_code=400, 
            detail="Invalid file_name. It must start with 'test_' and end with '.py'."
        )
    if "/" in file_name or "\\" in file_name:
        raise HTTPException(
            status_code=400,
            detail="Invalid file_name. It cannot contain path separators."
        )
    
    fingerprint_filename = request.fingerprint_filename
    if fingerprint_filename:
        if not fingerprint_filename.endswith(".json"):
            raise HTTPException(status_code=400, detail="fingerprint_filename must end with .json")
        if "/" in fingerprint_filename or "\\" in fingerprint_filename:
            raise HTTPException(
                status_code=400, detail="fingerprint_filename cannot contain path separators."
            )

    task_id = str(uuid.uuid4())
    tasks[task_id] = {'status': 'pending'}

    logger.info(f"Starting test generation for file: {file_name} with task_id: {task_id}")
    
    # Add wrapper function to background tasks
    background_tasks.add_task(
        run_task_wrapper,
        task_id,
        run_test_generation,
        request.description,
        request.file_name,
        request.fingerprint_filename,
        request.requires_login
    )
    
    # Return the task_id to the client
    return {"message": f"Test file generation for '{file_name}' has started.", "task_id": task_id}


@router.post("/fingerprint", status_code=202)
async def create_fingerprint(request: FingerprintRequest, background_tasks: BackgroundTasks):
    """
    Accepts a URL and triggers the AI-powered element fingerprinting process
    in the background.
    """
    if not request.url.startswith("http"):
        raise HTTPException(status_code=400, detail="Invalid URL provided. Must start with http or https.")

    task_id = str(uuid.uuid4())
    tasks[task_id] = {'status': 'pending'}

    logger.info(f"Starting fingerprint request for URL: {request.url} with task_id: {task_id}")
    
    # Add wrapper function to background tasks
    background_tasks.add_task(
        run_task_wrapper,
        task_id,
        run_fingerprint_generation,
        request.url,
        request.output_filename,
        request.use_authentication,
        request.allow_redirects
    )
    
    # Return the task_id to the client
    return {"message": "Fingerprint generation has started.", "task_id": task_id}

@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """
    Poll this endpoint with a task_id to check the status of a background job.
    """
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {"task_id": task_id, "status": task['status']}