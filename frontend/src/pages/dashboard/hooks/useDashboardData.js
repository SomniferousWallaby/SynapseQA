import { useState, useEffect, useCallback } from 'react';
import * as api from '../../../services/apiService'; // Adjust path if needed

export const useDashboardData = (addToast) => {
    const [tests, setTests] = useState([]);
    const [fingerprints, setFingerprints] = useState([]);
    const [authState, setAuthState] = useState({});
    const [reports, setReports] = useState([]); // This state is correct
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchData = useCallback(async () => {
        try {
            setLoading(true);

            // Fetch all data in parallel, just once.
            const [dashboardData, reportsData] = await Promise.all([
                api.fetchDashboardData(),
                api.fetchReports()
            ]);

            // Set all the state from the results
            setTests(dashboardData.tests);
            setFingerprints(dashboardData.fingerprints);
            setAuthState(dashboardData.authState);
            setReports(reportsData);

        } catch (err) {
            setError(err.message);
            if (addToast) {
                addToast(err.message, 'error');
            }
        } finally {
            setLoading(false);
        }
    }, [addToast]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    // 👇 ADD 'reports' to the return object 👇
    return { tests, fingerprints, authState, reports, loading, error, fetchData };
};