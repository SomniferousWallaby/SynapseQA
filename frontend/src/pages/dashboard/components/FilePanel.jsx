import React from 'react';

// Icon components are clean and well-defined.
const ViewIcon = () => <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>;
const RunIcon = () => <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>;
const DeleteIcon = () => <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>;

const FilePanel = ({ title, files = [], fileType, onCreate, onView, onRun, onDelete, onRunAll, className = '' }) => {
    const panelClasses = `panel ${className}`;
    return (
        <div className={panelClasses}>
            <div className="panel-header">
                <h2>{title}</h2>
                <div className="panel-header-actions">
                    {onRunAll && (
                        <button className="create-btn run-all-btn" onClick={onRunAll}>Run All</button>
                    )}
                    {onCreate && (
                        <button className="create-btn" onClick={onCreate}>
                            Create New {fileType === 'test' ? 'Test' : 'Fingerprint'}
                        </button>
                    )}
                </div>
            </div>
            <ul className="file-list">
                {files.length > 0 ? (
                    files.map(file => (
                        <li key={file} className="file-item">
                            <span>{file}</span>
                            <div className="file-actions">
                                {onRun && (
                                    <button className="action-btn run-btn" title="Run Test" onClick={() => onRun(file)}>
                                        <RunIcon />
                                    </button>
                                )}
                                <button className="action-btn view-btn" title="View File" onClick={() => onView(file, fileType)}>
                                    <ViewIcon />
                                </button>
                                <button className="action-btn delete-btn" title="Delete File" onClick={() => onDelete(file, fileType)}>
                                    <DeleteIcon />
                                </button>
                            </div>
                        </li>
                    ))
                ) : (
                    <li>No {title.toLowerCase()} found.</li>
                )}
            </ul>
        </div>
    );
};

export default FilePanel;