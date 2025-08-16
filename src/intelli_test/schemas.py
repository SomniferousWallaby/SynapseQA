from pydantic import BaseModel

class FingerprintRequest(BaseModel):
    url: str
    output_filename: str  # e.g., "loginPage"
    use_authentication: bool = False
    allow_redirects: bool = False

class TestGenerationRequest(BaseModel):
    description: str
    file_name: str
    fingerprint_filename: str | None = None
    requires_login: bool = False

class AuthStateRequest(BaseModel):
    url: str # Base site URL ex. www.google.com
    login_path: str # Path to the login page ex. /auth/login

class AutomatedAuthStateRequest(BaseModel):
    login_url: str
    login_instructions: str
    fingerprint_filename: str | None = None
    headless: bool = True
    username: str | None = None
    password: str | None = None

class TestRunRequest(BaseModel):
    filename: str




