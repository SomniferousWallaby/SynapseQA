import React from 'react';
import Modal from '../../../../components/modal/Modal';
const CreateFingerprintModal = ({ isOpen, onClose, onSubmit, isSubmitting }) => {
    return (
        <Modal isOpen={isOpen} onClose={onClose} title="Create New Fingerprint">
            <form onSubmit={onSubmit} className="modal-form">
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
    );
};

export default CreateFingerprintModal;