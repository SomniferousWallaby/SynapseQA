import React from 'react';
import './Modal.css';

const Modal = ({ isOpen, onClose, title, children, isLarge }) => {
    if (!isOpen) return null;

    const contentClasses = `modal-content ${isLarge ? 'modal-large' : ''}`;

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className={contentClasses} onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <h2 className="modal-title">{title}</h2>
                    <button onClick={onClose} className="modal-close-btn">&times;</button>
                </div>
                <div className="modal-body">
                    {children}
                </div>
            </div>
        </div>
    );
};

export default Modal;