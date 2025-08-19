import React, { useState, useEffect } from 'react';
import './Dashboard.css';

// Custom Hooks
import { useToasts } from '../../hooks/useToasts';
import { useDashboardData } from './hooks/useDashboardData';

// API Service
import * as api from '../../services/apiService';

// Components
import ToastContainer from '../../components/toast/ToastContainer';
import AuthStatus from './components/AuthStatus';
import FilePanel from './components/FilePanel';
import CreateTestModal from './components/modals/CreateTestModal';
import CreateFingerprintModal from './components/modals/CreateFingerprintModal';
import CreateAuthStateModal from './components/modals/SetAuthStateModal';
import FileViewerModal from './components/modals/FileViewerModal';
import SettingsModal from './components/modals/SettingsModal';

function Dashboard() {
    // --- STATE MANAGEMENT ---
    const { toasts, addToast, removeToast } = useToasts();
    const { tests, fingerprints, authState, reports, loading, error, fetchData } = useDashboardData(addToast);

    // UI State
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isFingerprintModalOpen, setIsFingerprintModalOpen] = useState(false);
    const [isTestModalOpen, setIsTestModalOpen] = useState(false);
    const [isAutoAuthModalOpen, setIsAutoAuthModalOpen] = useState(false);
    const [isViewerModalOpen, setIsViewerModalOpen] = useState(false);
    const [isSettingsModalOpen, setIsSettingsModalOpen] = useState(false); // <-- Add this
    
    // Form & Viewer State
    const [autoAuthForm, setAutoAuthForm] = useState({ /* initial empty state */ });
    const [viewerContent, setViewerContent] = useState({});
    const [testResult, setTestResult] = useState(null);
    const [isViewerLoading, setIsViewerLoading] = useState(false);
    const [apiKeyStatus, setApiKeyStatus] = useState({ is_set: false });

    // --- EFFECTS ---
     useEffect(() => {
        const checkApiKey = async () => {
            try {
                const status = await api.getApiKeyStatus();
                setApiKeyStatus(status);
            } catch (err) {
                console.error("Could not fetch API key status:", err);
            }
        };
        checkApiKey();
    }, []);

    // --- EVENT HANDLERS ---
    const handleAutoAuthFormChange = (e) => {
        const { name, value, type, checked } = e.target;
        setAutoAuthForm(prev => ({ ...prev, [name]: type === 'checkbox' ? checked : value }));
    };

    const openAutoAuthModal = async () => {
        try {
            const settings = await api.fetchAutoAuthSettings();
            setAutoAuthForm({
                login_url: settings.login_url || '',
                login_instructions: settings.login_instructions || '',
                fingerprint_filename: settings.fingerprint_filename || '',
                headless: settings.headless !== undefined ? settings.headless : true,
                username: settings.username || '',
                password: settings.password || '',
            });
            setIsAutoAuthModalOpen(true);
        } catch (err) {
            addToast("Could not load previous auth settings.", "error");
        }
    };

    const handleFormSubmit = async (handler, successCallback, successMessage) => {
        if (isSubmitting) return;
        setIsSubmitting(true);
        // 1. Show a generic "in-progress" toast that doesn't auto-close
        const toastId = addToast('Processing request...', 'info', null);

        try {
            await handler();
            successCallback();
            fetchData(); // Refresh data on success

            // 2. Replace the "in-progress" toast with a success message
            removeToast(toastId);
            addToast(successMessage, 'success');

        } catch (err) {
            // 3. On error, replace the "in-progress" toast with an error message
            removeToast(toastId);
            addToast(err.message, 'error');
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleFingerprintSubmit = async (e) => {
        e.preventDefault();
        if (isSubmitting) return;

        setIsSubmitting(true);
        setIsFingerprintModalOpen(false); 
        
        const inProgressToastId = addToast(
            'Fingerprint task submitted. Awaiting completion...', 
            'info', 
            null
        );

        try {
            const formData = new FormData(e.target);
            const body = {
                url: formData.get('url'),
                output_filename: formData.get('output_filename'),
                use_authentication: formData.get('use_authentication') === 'on',
                allow_redirects: formData.get('allow_redirects') === 'on',
            };

            // 1. Make the initial request to start the task
            const response = await api.submitGenerationTask('/generate/fingerprint', body);
            
            // 2. Start polling with the returned task_id
            const successMessage = `Fingerprint '${body.output_filename}.json' created successfully.`;
            pollTaskStatus(response.task_id, inProgressToastId, successMessage);

        } catch (err) {
            // This catches errors from the INITIAL submission only
            removeToast(inProgressToastId);
            addToast(err.message, 'error');
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleTestSubmit = async (e) => {
        e.preventDefault();
        if (isSubmitting) return;
        
        setIsSubmitting(true);
        setIsTestModalOpen(false);

        const inProgressToastId = addToast(
            'Test generation submitted. Awaiting completion...', 
            'info', 
            null
        );

        try {
            const formData = new FormData(e.target);
            const body = {
                description: formData.get('description'),
                file_name: formData.get('file_name'),
                fingerprint_filename: formData.get('fingerprint_filename'),
                requires_login: formData.get('requires_login') === 'on',
            };

            // 1. Initial request
            const response = await api.submitGenerationTask('/generate/test', body);
            
            // 2. Start polling
            const successMessage = `Test '${body.file_name}' created successfully.`;
            pollTaskStatus(response.task_id, inProgressToastId, successMessage);

        } catch (err) {
            removeToast(inProgressToastId);
            addToast(err.message, 'error');
        } finally {
            setIsSubmitting(false);
        }
    };
        
    const handleAutoAuthSubmit = (e) => {
        e.preventDefault();
        handleFormSubmit(
            () => api.submitAutoAuth(autoAuthForm),
            () => setIsAutoAuthModalOpen(false),
            'Auth state generation started successfully.' // <-- Pass the message
        );
    };
    
    const handleDeleteFile = async (filename, type) => {
        if (!window.confirm(`Are you sure you want to delete ${filename}?`)) return;
        const toastId = addToast(`Deleting ${filename}...`, 'info', null);
        try {
            await api.deleteFile(filename, type);
            removeToast(toastId);
            addToast(`${filename} deleted successfully.`, 'success');
            fetchData();
        } catch (err) {
            removeToast(toastId);
            addToast(err.message, 'error');
        }
    };

    const handleViewFile = async (filename, type) => {
        setIsViewerLoading(true);
        setTestResult(null);
        setViewerContent({});
        setIsViewerModalOpen(true);
        try {
            const data = await api.fetchFileContent(filename, type);
            if (type === 'report') {
                // If it's a report, parse the content and set it as a testResult
                const reportJson = JSON.parse(data.content);
                setTestResult(reportJson);
                setViewerContent({ filename });
            }
            else { setViewerContent({ filename, content: data.content, type }); }

        } catch (err) {
            addToast(err.message, 'error');
            setIsViewerModalOpen(false);
        } finally {
            setIsViewerLoading(false);
        }
    };
    
    const handleRunTest = async (filename) => {
        setIsViewerLoading(true);
        setViewerContent({ filename, content: null, type: 'test' });
        setTestResult(null);
        setIsViewerModalOpen(true);
        try {
            const result = await api.runTest(filename);
            setTestResult(result);
        } catch (err) {
            addToast(err.message, 'error');
            setIsViewerModalOpen(false);
        } finally {
            setIsViewerLoading(false);
        }
    };

    const pollTaskStatus = (taskId, inProgressToastId, successMessage) => {
        const intervalId = setInterval(async () => {
            try {
                const response = await api.checkTaskStatus(taskId);

                if (response.status === 'complete') {
                    clearInterval(intervalId);
                    removeToast(inProgressToastId);
                    addToast(successMessage, 'success');
                    fetchData();
                } else if (response.status === 'failed') {
                    clearInterval(intervalId);
                    removeToast(inProgressToastId);
                    addToast('The background task failed. Please check server logs.', 'error');
                }
                // If the status is 'pending', the interval continues automatically.

            } catch (err) {
                // Error handling for polling request
                clearInterval(intervalId);
                removeToast(inProgressToastId);
                addToast(`Error checking task status: ${err.message}`, 'error');
            }
        }, 3000); // Polling interval
    };

    const handleRunAllTests = async () => {
        const toastId = addToast('Starting full test suite run...', 'info', null);
        try {
            await api.runAllTests();
            removeToast(toastId);
            addToast('Test suite run started. Results will appear as they complete.', 'success');
        } catch (err) {
            removeToast(toastId);
            addToast(err.message, 'error');
        }
    };

    const handleSaveApiKey = async (apiKey) => {
        setIsSubmitting(true);
        try {
            const result = await api.saveApiKey(apiKey);
            addToast(result.message, 'success');
            setIsSettingsModalOpen(false);
            setApiKeyStatus({ is_set: true }); // Optimistically update status
        } catch (err) {
            addToast(err.message, 'error');
        } finally {
            setIsSubmitting(false);
        }
    };

    // --- RENDER LOGIC ---
    if (loading) return <div className="loading">Loading Dashboard...</div>;
    if (error) return <div className="error">{error}</div>;

    return (
        <div className="dashboard">
            <ToastContainer toasts={toasts} removeToast={removeToast} />
            <h1>IntelliTest Dashboard</h1>

            <div className="setup-container">
                {/* API Key Widget */}
                <div className="setup-widget">
                    <div className="widget-header">
                        <h4>API Key</h4>
                        <span className={`status-indicator ${apiKeyStatus.is_set ? 'status-success' : 'status-error'}`}>
                            {apiKeyStatus.is_set ? 'Set' : 'Not Set'}
                        </span>
                    </div>
                    <p className="widget-description">
                        The Google AI API key is used for all test and element generation.
                    </p>
                    <div className="widget-footer">
                        <button className="widget-btn" onClick={() => setIsSettingsModalOpen(true)}>
                            Settings
                        </button>
                    </div>
                </div>

                {/* Auth State Widget */}
                <div className="setup-widget">
                    <div className="widget-header">
                        <h4>Authentication State</h4>
                        <span className={`status-indicator ${!authState.exists || authState.is_expired ? 'status-error' : 'status-success'}`}>
                            {!authState.exists ? 'Missing' : authState.is_expired ? 'Expired' : 'Valid'}
                        </span>
                    </div>
                    <p className="widget-description">
                        A saved browser session used for tests that require a login.
                    </p>
                    <div className="widget-footer">
                        <button className="widget-btn" onClick={openAutoAuthModal}>
                            {authState.exists ? 'Update Auth State' : 'Set Auth State'}
                        </button>
                    </div>
                </div>
            </div>


            <AuthStatus authState={authState} onSetAuthState={openAutoAuthModal} />

            <div className="panels-container">
                <FilePanel 
                    title="Tests" 
                    files={tests} fileType="test" 
                    onCreate={() => setIsTestModalOpen(true)} 
                    onView={handleViewFile} 
                    onRun={handleRunTest} 
                    onDelete={handleDeleteFile} 
                    onRunAll={handleRunAllTests} />
                <FilePanel 
                    title="Page Fingerprints" 
                    files={fingerprints} fileType="fingerprint" 
                    onCreate={() => setIsFingerprintModalOpen(true)} 
                    onView={handleViewFile} 
                    onDelete={handleDeleteFile} />
                <FilePanel
                    title="Test Results"
                    files={reports}
                    fileType="report"
                    onCreate={null} 
                    onView={handleViewFile}
                    onDelete={handleDeleteFile} />
            </div>

            <CreateFingerprintModal 
                isOpen={isFingerprintModalOpen} 
                onClose={() => setIsFingerprintModalOpen(false)} 
                onSubmit={handleFingerprintSubmit} 
                isSubmitting={isSubmitting} />
            <CreateAuthStateModal 
                isOpen={isAutoAuthModalOpen}
                onClose={() => setIsAutoAuthModalOpen(false)} 
                onSubmit={handleAutoAuthSubmit}
                fingerprints={fingerprints} 
                isSubmitting={isSubmitting}
                formState={autoAuthForm}
                onFormChange={handleAutoAuthFormChange} />
            <CreateTestModal 
                isOpen={isTestModalOpen} 
                onClose={() => setIsTestModalOpen(false)} 
                onSubmit={handleTestSubmit} 
                fingerprints={fingerprints} 
                isSubmitting={isSubmitting} />
            <FileViewerModal 
                isOpen={isViewerModalOpen} 
                onClose={() => setIsViewerModalOpen(false)} 
                isLoading={isViewerLoading} 
                testResult={testResult} 
                content={viewerContent} />
            <SettingsModal 
                isOpen={isSettingsModalOpen}
                onClose={() => setIsSettingsModalOpen(false)}
                onSave={handleSaveApiKey}
                isSubmitting={isSubmitting} />
        </div>
    );
}

export default Dashboard;