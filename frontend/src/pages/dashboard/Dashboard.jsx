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

    if (seconds < 60) return `${seconds} seconds ago`;
    if (minutes < 60) return `${minutes} minutes ago`;
    if (hours < 24) return `${hours} hours ago`;
    return `${days} days ago`;
}

function getAuthStateStatus(authState) {
    if (!authState.exists) {
        return 'error';
    }
    const authDate = new Date(authState.last_modified);
    const now = new Date();
    const ageInHours = (now - authDate) / (1000 * 60 * 60);

    if (ageInHours > 24) {
        return 'warning';
    }
    return 'success';
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
    const [isSubmitting, setIsSubmitting] = useState(false);
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

    const addToast = (message, type = 'info', duration = 5000) => {
        const id = Date.now() + Math.random();
        setToasts(prevToasts => [...prevToasts, { id, message, type }]);
        if (duration !== null) {
            setTimeout(() => removeToast(id), duration);
        }
        return id;
    };
    
    const handleApiSubmit = async (endpoint, body, successMessage) => {
        setIsSubmitting(true);
        
        const startMessage = endpoint.includes('fingerprint') 
            ? 'Starting fingerprint generation...' 
            : 'Starting test generation...';
        
        const startId = addToast(startMessage, 'info', null);
        
        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });
            const result = await response.json();
            console.log('API Response:', result);
            
            if (!response.ok) throw new Error(result.detail || 'An unknown error occurred.');

            removeToast(startId);
            addToast(result.message, 'success');
            
            // Fetch data before returning
            await fetchData();
            return true;
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

        const success = await handleApiSubmit(
            '/generate-test', 
            body, 
            'Test file generation has been queued successfully'
        );
        if (success) {
            setIsTestModalOpen(false);
        }
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
            <h1>intelliTest Dashboard</h1>

            <div className="status-container">
                <div className={`status-box ${getAuthStateStatus(authState)}`}>
                    <strong>Auth State:</strong>
                    {authState.exists
                        ? ` Present (Updated ${formatTimeAgo(authState.last_modified)})`
                        : ' Not Found'}
                </div>
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
                    <form 
                        onSubmit={(e) => {
                            e.preventDefault(); // Prevent default here
                            console.log('Form submit event triggered at:', Date.now());
                            if (!isSubmitting) { // Extra check here
                                handleFingerprintSubmit(e);
                            } else {
                                console.log('Submission already in progress, ignoring form submit');
                            }
                        }} 
                        className="modal-form"
                    >
                    <label htmlFor="url">Target URL</label>
                    <input type="url" id="url" name="url" placeholder="https://example.com/login" required />

                    <label htmlFor="output_filename">Output Filename (without extension)</label>
                    <input type="text" id="output_filename" name="output_filename" placeholder="loginPage" required />

                    <div className="checkbox-group">
                        <input type="checkbox" id="use_authentication" name="use_authentication" />
                        <label htmlFor="use_authentication">Use Authenticated Session</label>
                    </div>

                    <button type="submit" className="submit-btn" disabled={isSubmitting}>
                        {isSubmitting ? 'Generating...' : 'Generate Fingerprint'}
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
                        <label htmlFor="requires_login">Requires Login (uses logged_in_page fixture)</label>
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