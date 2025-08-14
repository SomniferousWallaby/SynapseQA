import React, { useState, useEffect } from 'react';
import './Dashboard.css';

// Vite exposes environment variables via `import.meta.env`
// Only variables prefixed with VITE_ are exposed to the client.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

function Dashboard() {
    const [tests, setTests] = useState([]);
    const [fingerprints, setFingerprints] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchData = async () => {
        try {
            setLoading(true);
            setError(null);

            const [testsResponse, fingerprintsResponse] = await Promise.all([
                fetch(`${API_BASE_URL}/files/tests`),
                fetch(`${API_BASE_URL}/files/fingerprints`)
            ]);

            if (!testsResponse.ok || !fingerprintsResponse.ok) {
                throw new Error('Network response was not ok. Is the backend API running?');
            }

            const testsData = await testsResponse.json();
            const fingerprintsData = await fingerprintsResponse.json();

            setTests(testsData);
            setFingerprints(fingerprintsData);

        } catch (err) {
            setError(err.message);
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []); // Empty dependency array means this runs once on mount

    if (loading) {
        return <div className="loading">Loading Dashboard...</div>;
    }

    if (error) {
        return <div className="error">{error}</div>;
    }

    return (
        <div className="dashboard">
            <h1>intelliTest Dashboard</h1>
            <div className="panels-container">
                <div className="panel">
                    <h2>Available Tests</h2>
                    <button className="create-btn">Create New Test</button>
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
                    <button className="create-btn">Create New Fingerprint</button>
                    <ul className="file-list">
                        {fingerprints.length > 0 ? (
                            fingerprints.map(fp => <li key={fp}>{fp}</li>)
                        ) : (
                            <li>No fingerprints found.</li>
                        )}
                    </ul>
                </div>
            </div>
        </div>
    );
}

export default Dashboard;
