import React from 'react';
import Modal from '../../../../components/modal/Modal';
const CreateTestModal = ({ isOpen, onClose, onSubmit, fingerprints, isSubmitting }) => {
    return (
        <Modal isOpen={isOpen} onClose={onClose} title="Create New Test File">
            <form onSubmit={onSubmit} className="modal-form">
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
                    <label htmlFor="requires_login">Requires Login (uses Auth State for logging in)</label>
                </div>

                <button type="submit" className="submit-btn" disabled={isSubmitting}>
                    {isSubmitting ? 'Generating...' : 'Generate Test'}
                </button>
            </form>
        </Modal>
    );
};

export default CreateTestModal;