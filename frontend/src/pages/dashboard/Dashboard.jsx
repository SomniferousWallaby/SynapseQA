import React, { useState, useEffect } from 'react';
import './Dashboard.css';
import Modal from '../../components/modal/Modal';
import ToastContainer from '../../components/toast/ToastContainer';

// Vite exposes environment variables via `import.meta.env`
// Only variables prefixed with VITE_ are exposed to the client.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

function formatTimeAgo(isoString) {
    if (!isoString) return '';
    const date = new Date(isoString);
    const now = new Date();
    const seconds = Math.round((now - date) / 1000);
    const minutes = Math.round(seconds / 60);
    const hours = Math.round(minutes / 60);
    const days = Math.round(hours / 24);

    if (seconds < 60) return `${seconds} second${seconds === 1 ? '' : 's'} ago`;
    if (minutes < 60) return `${minutes} minute${minutes === 1 ? '' : 's'} ago`;
    if (hours < 24) return `${hours} hour${hours === 1 ? '' : 's'} ago`;
    return `${days} day${days === 1 ? '' : 's'} ago`;
}

function formatTimeUntil(isoString) {
    if (!isoString) return '';
    const date = new Date(isoString);
    const now = new Date();
    const seconds = Math.round((date - now) / 1000);
    const minutes = Math.round(seconds / 60);
    const hours = Math.round(minutes / 60);
    const days = Math.round(hours / 24);

    if (seconds < 0) return 'already'; // Should be caught by is_expired, but a good fallback.
    if (seconds < 60) return `in ${seconds} second${seconds === 1 ? '' : 's'}`;
    if (minutes < 60) return `in ${minutes} minute${minutes === 1 ? '' : 's'}`;
    if (hours < 24) return `in ${hours} hour${hours === 1 ? '' : 's'}`;
    return `in ${days} day${days === 1 ? '' : 's'}`;
}

function getAuthStateStatus(authState) {
    if (!authState.exists) { // Not found - yellow
        return 'error'; 
    }
    if (authState.is_expired) { // Expired - red
        return 'error'; 
    }
    if (!authState.expires_at) { // Exists, not expired, but expiration date is unknown - yellow
        return 'warning';
    }
    return 'success'; // Present and valid
}

function Dashboard() {
    const [tests, setTests] = useState([]);
    const [fingerprints, setFingerprints] = useState([]);
    const [authState, setAuthState] = useState({ exists: false, last_modified: null });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Modal, form, and notification states
    const [isFingerprintModalOpen, setIsFingerprintModalOpen] = useState(false);
    const [isTestModalOpen, setIsTestModalOpen] = useState(false);
    const [isAutoAuthModalOpen, setIsAutoAuthModalOpen] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [autoAuthForm, setAutoAuthForm] = useState({
        login_url: '',
        login_instructions: '',
        fingerprint_filename: '',
        headless: true,
        username: '',
        password: '',
    });
    const [toasts, setToasts] = useState([]);

    const fetchData = async () => {
        try {
            setLoading(true);
            setError(null);

            const [testsResponse, fingerprintsResponse, authStateResponse] = await Promise.all([
                fetch(`${API_BASE_URL}/files/tests`),
                fetch(`${API_BASE_URL}/files/fingerprints`),
                fetch(`${API_BASE_URL}/files/auth-state`)
            ]);

            // Check for error responses and parse them
            if (!testsResponse.ok || !fingerprintsResponse.ok || !authStateResponse.ok) {
                const errorData = await testsResponse.json().catch(() => ({}));
                const errorMessage = errorData.detail || 'Network response was not ok. Is the backend API running?';
                throw new Error(errorMessage);
            }

            const testsData = await testsResponse.json();
            const fingerprintsData = await fingerprintsResponse.json();
            const authStateData = await authStateResponse.json();

            // Check for backend errors in the response data
            if (testsData.error) {
                addToast(`Error: ${testsData.error}`, 'error');
            }

            setTests(testsData);
            setFingerprints(fingerprintsData);
            setAuthState(authStateData);

        } catch (err) {
            setError(err.message);
            addToast(`Error: ${err.message}`, 'error');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };
        

    const removeToast = (id) => {
        setToasts(prevToasts => prevToasts.filter(toast => toast.id !== id));
    };

    const addToast = (message, type = 'info', duration) => {
        const id = Date.now() + Math.random();
        setToasts(prevToasts => [...prevToasts, { id, message, type }]);

        // Default duration is 5s, but errors are persistent by default so they aren't missed.
        const finalDuration = duration !== undefined ? duration : (type === 'error' ? null : 5000);

        if (finalDuration !== null) {
            setTimeout(() => removeToast(id), finalDuration);
        }
        return id;
    };
    
    const handleApiSubmit = async (endpoint, body) => {
        setIsSubmitting(true);
        
        const startMessage = endpoint.includes('fingerprint') 
            ? 'Starting fingerprint generation...' 
            : 'Starting test generation...';
        
        const startId = addToast(startMessage, 'info', null); // Keep this toast until the process is complete
        
        try {
            // 1. Trigger the background task on the server
            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });
            const result = await response.json();
            
            if (!response.ok) throw new Error(result.detail || 'An unknown error occurred.');

            // 2. Poll for the result, as the task runs in the background
            const pollForFile = (fileName, fileType, timeout = 30000, interval = 2000) => {
                return new Promise((resolve, reject) => {
                    const startTime = Date.now();

                    const intervalId = setInterval(async () => {
                        if (Date.now() - startTime > timeout) {
                            clearInterval(intervalId);
                            reject(new Error(`Polling for '${fileName}' timed out after ${timeout / 1000}s.`));
                            return;
                        }

                        try {
                            const listUrl = fileType === 'test' ? '/files/tests' : '/files/fingerprints';
                            const listResponse = await fetch(`${API_BASE_URL}${listUrl}`);
                            if (!listResponse.ok) return; // Silently fail and retry on next interval

                            const fileList = await listResponse.json();

                            if (fileList.includes(fileName)) {
                                clearInterval(intervalId);
                                await fetchData(); // Run a final full data fetch to update everything
                                resolve();
                            }
                        } catch (err) {
                            console.warn("Polling fetch failed, will retry:", err);
                        }
                    }, interval);
                });
            };

            const targetFileName = endpoint.includes('fingerprint') ? `${body.output_filename}.json` : body.file_name;
            const fileType = endpoint.includes('fingerprint') ? 'fingerprint' : 'test';

            await pollForFile(targetFileName, fileType);

            // 3. Finalize and update UI
            removeToast(startId);
            addToast(`Successfully generated ${targetFileName}`, 'success');
            return true; // Indicate success to the calling function
        } catch (error) {
            removeToast(startId);
            addToast(error.message, 'error');
            return false;
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleFingerprintSubmit = async (event) => {
        event.preventDefault();
        
        if (isSubmitting) {
            console.log('Submission already in progress, ignoring...');
            return;
        }
        
        console.log('Starting handleFingerprintSubmit...');
        const formData = new FormData(event.target);
        const body = {
            url: formData.get('url'),
            output_filename: formData.get('output_filename'),
            use_authentication: formData.get('use_authentication') === 'on',
            allow_redirects: formData.get('allow_redirects') === 'on',
        };

        console.log('Form data:', body);
        const success = await handleApiSubmit('/fingerprint', body);
        console.log('handleApiSubmit result:', success);
        
        if (success) {
            setIsFingerprintModalOpen(false);
        }
    };

    const handleTestSubmit = async (event) => {
        event.preventDefault();
        const formData = new FormData(event.target);
        const body = {
            description: formData.get('description'),
            file_name: formData.get('file_name'),
            fingerprint_filename: formData.get('fingerprint_filename'),
            requires_login: formData.get('requires_login') === 'on',
        };

        const success = await handleApiSubmit('/generate-test', body);
        if (success) {
            setIsTestModalOpen(false);
        }
    };

    const handleAutoAuthSubmit = async (event) => {
        event.preventDefault();
        if (isSubmitting) return;

        setIsSubmitting(true);
        const startId = addToast('Starting automated auth state creation...', 'info', null);

        try {
            const response = await fetch(`${API_BASE_URL}/auth_state/automated`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(autoAuthForm),
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.detail || 'An unknown error occurred.');

            const pollForAuthFile = (timeout = 12010, interval = 3000) => {
                return new Promise((resolve, reject) => {
                    const startTime = Date.now();
                    const initialTimestamp = authState.last_modified;

                    const intervalId = setInterval(async () => {
                        if (Date.now() - startTime > timeout) {
                            clearInterval(intervalId);
                            reject(new Error(`Polling for auth state update timed out after ${timeout / 1000}s.`));
                            return;
                        }
                        try {
                            const authResponse = await fetch(`${API_BASE_URL}/files/auth-state`);
                            if (!authResponse.ok) return;
                            const newAuthState = await authResponse.json();
                            if (newAuthState.exists && newAuthState.last_modified !== initialTimestamp) {
                                clearInterval(intervalId);
                                await fetchData();
                                resolve();
                            }
                        } catch (err) { /* Silently ignore polling errors and retry */ }
                    }, interval);
                });
            };
            await pollForAuthFile();
            removeToast(startId);
            addToast('Successfully created new auth state!', 'success');
            setIsAutoAuthModalOpen(false);
        } catch (error) {
            removeToast(startId);
            addToast(error.message, 'error');
        } finally {
            setIsSubmitting(false);
        }
    };

    const openAutoAuthModal = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/auth_state/automated/settings`);
            if (response.ok) {
                const settings = await response.json();
                // Ensure all fields have a default value to avoid uncontrolled component warnings
                setAutoAuthForm({
                    login_url: settings.login_url || '',
                    login_instructions: settings.login_instructions || '',
                    fingerprint_filename: settings.fingerprint_filename || '',
                    headless: settings.headless !== undefined ? settings.headless : true,
                    username: settings.username || '',
                    password: settings.password || '',
                });
            } else {
                // If settings don't exist or there's an error, use empty defaults
                setAutoAuthForm({ login_url: '', login_instructions: '', fingerprint_filename: '', headless: true, username: '', password: '' });
            }
        } catch (error) {
            console.error("Failed to fetch auth settings:", error);
            addToast("Could not load previous auth settings.", "error");
        }
        setIsAutoAuthModalOpen(true);
    };

    const handleAutoAuthFormChange = (e) => {
        const { name, value, type, checked } = e.target;
        setAutoAuthForm(prev => ({ ...prev, [name]: type === 'checkbox' ? checked : value }));
    };

    useEffect(() => {
        fetchData();
    }, []);

    if (loading) {
        return <div className="loading">Loading Dashboard...</div>;
    }

    if (error) {
        return <div className="error">{error}</div>;
    }

    return (
        <div className="dashboard">
            <ToastContainer toasts={toasts} removeToast={removeToast} />
            <h1>IntelliTest Dashboard</h1>

            <div className="status-container">
                <div className={`status-box ${getAuthStateStatus(authState)}`}>
                    <strong>Auth State:</strong>
                    {(() => {
                        if (!authState.exists) return ' Not Found';
                        const lastUpdated = `(Updated ${formatTimeAgo(authState.last_modified)})`;
                        if (authState.is_expired) return ` Expired ${lastUpdated}`;
                        if (!authState.expires_at) return ` Present, expiration unknown ${lastUpdated}`;
                        const expires = `(Expires ${formatTimeUntil(authState.expires_at)})`;
                        return ` Valid ${expires}`;
                    })()}
                </div>
                <button className="create-btn auth-btn" onClick={openAutoAuthModal}>Set Auth State</button>
            </div>

            <div className="panels-container">
                <div className="panel">
                    <h2>Available Tests</h2>
                    <button className="create-btn" onClick={() => setIsTestModalOpen(true)}>Create New Test</button>
                    <ul className="file-list">
                        {tests.length > 0 ? (
                            tests.map(test => <li key={test}>{test}</li>)
                        ) : (
                            <li>No tests found.</li>
                        )}
                    </ul>
                </div>
                <div className="panel">
                    <h2>Available Page Fingerprints</h2>
                    <button className="create-btn" onClick={() => setIsFingerprintModalOpen(true)}>Create New Fingerprint</button>
                    <ul className="file-list">
                        {fingerprints.length > 0 ? (
                            fingerprints.map(fp => <li key={fp}>{fp}</li>)
                        ) : (
                            <li>No fingerprints found.</li>
                        )}
                    </ul>
                </div>
            </div>

                <Modal isOpen={isFingerprintModalOpen} onClose={() => setIsFingerprintModalOpen(false)} title="Create New Fingerprint">
                    <form onSubmit={handleFingerprintSubmit} className="modal-form">
                    <label htmlFor="url">Target URL</label>
                    <input type="url" id="url" name="url" placeholder="https://example.com/login" required />

                    <label htmlFor="output_filename">Output Filename (without extension)</label>
                    <input type="text" id="output_filename" name="output_filename" placeholder="loginPage" required />

                    <div className="checkbox-group">
                        <input type="checkbox" id="use_authentication" name="use_authentication" />
                        <label htmlFor="use_authentication">Use Authenticated Session</label>
                    </div>

                    <div className="checkbox-group">
                        <input type="checkbox" id="allow_redirects" name="allow_redirects" />
                        <label htmlFor="allow_redirects">Allow Redirects</label>
                    </div>

                    <button type="submit" className="submit-btn" disabled={isSubmitting}>
                        {isSubmitting ? 'Generating...' : 'Generate Fingerprint'}
                    </button>
                </form>
            </Modal>

            <Modal isOpen={isAutoAuthModalOpen} onClose={() => setIsAutoAuthModalOpen(false)} title="Create Auth State">
                <form onSubmit={handleAutoAuthSubmit} className="modal-form">
                    <label htmlFor="login_url">Login Page URL</label>
                    <input 
                        type="url" 
                        id="login_url" 
                        name="login_url" 
                        placeholder="https://example.com/login" 
                        value={autoAuthForm.login_url}
                        onChange={handleAutoAuthFormChange}
                        required 
                    />

                    <label htmlFor="login_instructions">Login Instructions</label>
                    <textarea 
                        id="login_instructions" 
                        name="login_instructions" 
                        rows="3" 
                        placeholder="Describe the login process in plain english." 
                        value={autoAuthForm.login_instructions}
                        onChange={handleAutoAuthFormChange}
                        required
                    ></textarea>    

                    <label htmlFor="username">Username (Optional)</label>
                    <input 
                        type="text" 
                        id="username" 
                        name="username" 
                        placeholder="Defaults to TEST_USER in .env" 
                        value={autoAuthForm.username}
                        onChange={handleAutoAuthFormChange}
                    />

                    <label htmlFor="password">Password (Optional)</label>
                    <input 
                        type="password" 
                        id="password" 
                        name="password" 
                        placeholder="Defaults to PASSWORD in .env" 
                        value={autoAuthForm.password}
                        onChange={handleAutoAuthFormChange}
                    />
                    
                    <label htmlFor="fingerprint_filename">Fingerprint File (Optional)</label>
                    <select id="fingerprint_filename" name="fingerprint_filename" value={autoAuthForm.fingerprint_filename} onChange={handleAutoAuthFormChange}>
                        <option value="">None</option>
                        {fingerprints.map(fp => (
                            <option key={fp} value={fp}>{fp}</option>
                        ))}
                    </select>

                    <div className="checkbox-group">
                        <input
                            type="checkbox"
                            id="headless"
                            name="headless"
                            checked={autoAuthForm.headless}
                            onChange={handleAutoAuthFormChange}
                        />
                        <label htmlFor="headless">Run in Headless Mode</label>
                    </div>

                    <button type="submit" className="submit-btn" disabled={isSubmitting}>
                        {isSubmitting ? 'Generating...' : 'Generate Auth State'}
                    </button>
                </form>
            </Modal>

            <Modal isOpen={isTestModalOpen} onClose={() => setIsTestModalOpen(false)} title="Create New Test File">
                <form onSubmit={handleTestSubmit} className="modal-form">
                    <label htmlFor="description">Test Description</label>
                    <textarea id="description" name="description" rows="3" placeholder="e.g., Verify that a user can log in with valid credentials." required></textarea>

                    <label htmlFor="file_name">Test Filename</label>
                    <input type="text" id="file_name" name="file_name" placeholder="test_successful_login.py" required />

                    <label htmlFor="fingerprint_filename">Fingerprint File (Optional)</label>
                    <select id="fingerprint_filename" name="fingerprint_filename">
                        <option value="">None</option>
                        {fingerprints.map(fp => (
                            <option key={fp} value={fp}>{fp}</option>
                        ))}
                    </select>

                    <div className="checkbox-group">
                        <input type="checkbox" id="requires_login" name="requires_login" />
                        <label htmlFor="requires_login">Requires Login (uses Auth State for logging in)</label>
                    </div>

                    <button type="submit" className="submit-btn" disabled={isSubmitting}>
                        {isSubmitting ? 'Generating...' : 'Generate Test'}
                    </button>
                </form>
            </Modal>
        </div>
    );
}

export default Dashboard;