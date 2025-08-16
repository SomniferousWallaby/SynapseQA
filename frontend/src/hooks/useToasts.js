import { useState, useCallback } from 'react';

export const useToasts = () => {
    const [toasts, setToasts] = useState([]);

    const removeToast = useCallback((id) => {
        setToasts(prevToasts => prevToasts.filter(toast => toast.id !== id));
    }, []);

    const addToast = useCallback((message, type = 'info', duration) => {
        const id = Date.now() + Math.random();
        setToasts(prevToasts => [...prevToasts, { id, message, type }]);

        const finalDuration = duration !== undefined ? duration : (type === 'error' ? null : 5000);

        if (finalDuration !== null) {
            setTimeout(() => removeToast(id), finalDuration);
        }
        return id;
    }, [removeToast]);

    return { toasts, addToast, removeToast };
};