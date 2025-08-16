import { useState, useEffect, useCallback } from 'react';
import * as api from '../../../services/apiService'; // Adjust path if needed

export const useDashboardData = (addToast) => {
    const [tests, setTests] = useState([]);
    const [fingerprints, setFingerprints] = useState([]);
    const [authState, setAuthState] = useState({});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // useCallback prevents this function from being recreated on every render
    const fetchData = useCallback(async () => {
        try {
            setLoading(true);
            const { tests, fingerprints, authState } = await api.fetchDashboardData();
            setTests(tests);
            setFingerprints(fingerprints);
            setAuthState(authState);
        } catch (err) {
            setError(err.message);
            // We pass addToast in so the hook can report errors
            if (addToast) {
                addToast(err.message, 'error');
            }
        } finally {
            setLoading(false);
        }
    }, [addToast]); // Dependency array for useCallback

    // This useEffect runs once when the hook is first used
    useEffect(() => {
        fetchData();
    }, [fetchData]);

    // The hook returns its state and the function to refetch data
    return { tests, fingerprints, authState, loading, error, fetchData };
};