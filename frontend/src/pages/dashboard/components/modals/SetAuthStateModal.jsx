import React from 'react';
import Modal from '../../../../components/modal/Modal';
const CreateAuthStateModal = ({ isOpen, onClose, onSubmit, fingerprints, isSubmitting, formState, onFormChange }) => {
    return (
        <Modal isOpen={isOpen} onClose={onClose} title="Create Auth State">
            <form onSubmit={onSubmit} className="modal-form">
                <label htmlFor="login_url">Login Page URL</label>
                <input 
                    type="url" 
                    id="login_url" 
                    name="login_url" 
                    placeholder="https://example.com/login" 
                    value={formState.login_url}
                    onChange={onFormChange}
                    required 
                />

                <label htmlFor="login_instructions">Login Instructions</label>
                <textarea 
                    id="login_instructions" 
                    name="login_instructions" 
                    rows="3" 
                    placeholder="Describe the login process in plain english." 
                    value={formState.login_instructions}
                    onChange={onFormChange}
                    required
                ></textarea>    

                <label htmlFor="username">Username (Optional)</label>
                <input 
                    type="text" 
                    id="username" 
                    name="username" 
                    placeholder="Defaults to TEST_USER in .env" 
                    value={formState.username}
                    onChange={onFormChange}
                />

                <label htmlFor="password">Password (Optional)</label>
                <input 
                    type="password" 
                    id="password" 
                    name="password" 
                    placeholder="Defaults to PASSWORD in .env" 
                    value={formState.password}
                    onChange={onFormChange}
                />
                
                <label htmlFor="fingerprint_filename">Fingerprint File (Optional)</label>
                <select id="fingerprint_filename" name="fingerprint_filename" value={formState.fingerprint_filename} onChange={onFormChange}>
                    <option value="">None</option>
                    {fingerprints.map(fp => (
                        <option key={fp} value={fp}>{fp}</option>
                    ))}
                </select>

                <div className="checkbox-group">
                    <input
                        type="checkbox"
                        id="headless"
                        name="headless"
                        checked={formState.headless}
                        onChange={onFormChange}
                    />
                    <label htmlFor="headless">Run in Headless Mode</label>
                </div>

                <button type="submit" className="submit-btn" disabled={isSubmitting}>
                    {isSubmitting ? 'Generating...' : 'Generate Auth State'}
                </button>
            </form>
        </Modal>
    );
};
        
export default CreateAuthStateModal;