const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

// A helper to handle responses and errors
const handleResponse = async (response) => {
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const errorMessage = errorData.detail || 'An unknown error occurred.';
        throw new Error(errorMessage);
    }
    return response.json();
};

export const fetchDashboardData = async () => {
    const [testsResponse, fingerprintsResponse, authStateResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/files/tests`),
        fetch(`${API_BASE_URL}/files/fingerprints`),
        fetch(`${API_BASE_URL}/files/auth-state`)
    ]);

    const tests = await handleResponse(testsResponse);
    const fingerprints = await handleResponse(fingerprintsResponse);
    const authState = await handleResponse(authStateResponse);

    return { tests, fingerprints, authState };
};

export const checkTaskStatus = async (taskId) => {
    const response = await fetch(`${API_BASE_URL}/generate/status/${taskId}`);
    if (!response.ok) {
        throw new Error('Failed to fetch task status.');
    }
    return response.json();
};

export const submitGenerationTask = async (endpoint, body) => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
    if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Submission failed.');
    }
    return response.json();
};

export const submitAutoAuth = (formState) => {
    return fetch(`${API_BASE_URL}/authentication/auth_state/automated`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formState),
    }).then(handleResponse);
};

export const fetchAutoAuthSettings = () => {
    return fetch(`${API_BASE_URL}/authentication/auth_state/automated/settings`).then(res => res.ok ? res.json() : {});
};

export const fetchFileContent = (filename, type) => {
    return fetch(`${API_BASE_URL}/files/content?type=${type}&filename=${filename}`).then(handleResponse);
};

export const deleteFile = (filename, type) => {
    return fetch(`${API_BASE_URL}/files?type=${type}&filename=${filename}`, {
        method: 'DELETE',
    }).then(handleResponse);
};

export const runTest = (filename) => {
    return fetch(`${API_BASE_URL}/tests/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename }),
    }).then(handleResponse);
};

export const fetchReports = () => {
    return fetch(`${API_BASE_URL}/files/reports`).then(handleResponse);
};

export const runAllTests = () => {
    return fetch(`${API_BASE_URL}/tests/run-all`, {
        method: 'POST',
    }).then(handleResponse);
};

export const getApiKeyStatus = () => {
    return fetch(`${API_BASE_URL}/settings/api-key-status`).then(handleResponse);
};

export const saveApiKey = (apiKey) => {
    return fetch(`${API_BASE_URL}/settings/api-key`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: apiKey }),
    }).then(handleResponse);
};