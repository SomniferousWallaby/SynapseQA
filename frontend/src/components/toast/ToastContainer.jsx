import React from 'react';
import './Toast.css';

// Internal Toast component
const Toast = ({ message, type, onClose }) => (
    <div className={`toast ${type}`}>
        <span>{message}</span>
        <button onClick={onClose} className="toast-close-btn">&times;</button>
    </div>
);

const ToastContainer = ({ toasts, removeToast }) => {
    if (!toasts.length) return null;

    return (
        <div className="toast-container">
            {toasts.map(toast => (
                <Toast
                    key={toast.id}
                    message={toast.message}
                    type={toast.type}
                    onClose={() => removeToast(toast.id)}
                />
            ))}
        </div>
    );
};

export default ToastContainer;

