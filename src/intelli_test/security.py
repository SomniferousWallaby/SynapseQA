import os
from pathlib import Path
from fastapi import HTTPException

# Determine project_root relative to this file's location
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def get_secure_path(file_type: str, filename: str) -> Path:
    """
    Validates file_type and filename, and returns a secure, absolute path.
    Prevents path traversal attacks.
    """
    if file_type not in ("test", "fingerprint", "report"):
        raise HTTPException(status_code=400, detail="Invalid file type specified.")

    # Basic sanitization
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Filename cannot contain path separators.")

    base_dir_map = {
        "test": Path(project_root) / "tests",
        "fingerprint": Path(project_root) / "elements",
        "report": Path(project_root) / "reports"
    }
    
    base_dir = base_dir_map[file_type]
    secure_path = base_dir.joinpath(filename).resolve()

    # Final check to ensure the resolved path is within the intended base directory
    if not secure_path.is_file() or base_dir not in secure_path.parents:
        raise HTTPException(status_code=404, detail="File not found or path is invalid.")

    return secure_path


def get_secure_path_for_delete(file_type: str, filename: str) -> Path:
    """
    A slightly different version for deletion that doesn't check for existence,
    as the file might be gone, but still performs security checks.
    """
    if file_type not in ("test", "fingerprint"):
        raise HTTPException(status_code=400, detail="Invalid file type specified.")

    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Filename cannot contain path separators.")

    base_dir_map = {
        "test": Path(project_root) / "tests",
        "fingerprint": Path(project_root) / "elements",
        "report": Path(project_root) / "reports"
    }
    
    base_dir = base_dir_map[file_type]
    # Resolve the path to get its canonical form
    secure_path = base_dir.joinpath(filename).resolve()

    # Check that the resolved path is inside the intended directory
    if base_dir not in secure_path.parents:
        raise HTTPException(status_code=400, detail="Invalid filename, path traversal detected.")

    return secure_path
