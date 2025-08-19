import React, { useState } from 'react';
import Modal from '../../../../components/modal/Modal';

const SettingsModal = ({ isOpen, onClose, onSave, isSubmitting }) => {
    const [apiKey, setApiKey] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        onSave(apiKey);
    };

    return (
        <Modal isOpen={isOpen} onClose={onClose} title="Application Settings">
            <form onSubmit={handleSubmit} className="modal-form">
                <label htmlFor="api_key">Google AI API Key</label>
                <input
                    type="password"
                    id="api_key"
                    name="api_key"
                    placeholder="Enter your API key"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    required
                />
                <div style={{ fontSize: '0.8rem', color: '#666', marginTop: '-0.5rem' }}>
                    Your key is saved to the backend `.env` file and is not stored in the browser.
                </div>
                <button type="submit" className="submit-btn" disabled={isSubmitting}>
                    {isSubmitting ? 'Saving...' : 'Save Key'}
                </button>
            </form>
        </Modal>
    );
};

export default SettingsModal;