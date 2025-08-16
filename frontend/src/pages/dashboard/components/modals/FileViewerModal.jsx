import React from 'react';
import Modal from '../../../../components/modal/Modal';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { a11yDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

const FileViewerModal = ({ isOpen, onClose, isLoading, testResult, content }) => {
    // Determine the title based on whether we have test results
    const title = testResult 
        ? `Test Results: ${content.filename}` 
        : `Viewing: ${content.filename}`;

    return (
        <Modal 
            isOpen={isOpen} 
            onClose={onClose} 
            title={title}
            isLarge={true}
        >
            {isLoading ? (
                <div className="loading">Loading...</div>
            ) : testResult ? (
                <div className="test-results-container">
                    <h3>Summary</h3>
                    <div className="test-results-summary">
                        <span className="summary-item total">Total: {testResult.summary.total || 0}</span>
                        <span className="summary-item passed">Passed: {testResult.summary.passed || 0}</span>
                        <span className="summary-item failed">Failed: {testResult.summary.failed || 0}</span>
                        <span className="summary-item skipped">Skipped: {testResult.summary.skipped || 0}</span>
                    </div>
                    <h3>Details</h3>
                    {testResult.tests && testResult.tests.map(test => (
                        <div key={test.nodeid} className={`test-outcome ${test.outcome}`}>
                            <span className="outcome-status">{test.outcome.toUpperCase()}</span>
                            <span className="outcome-nodeid">{test.nodeid}</span>
                            {test.outcome === 'failed' && test.longrepr && (
                                <pre className="test-error-details">{test.longrepr}</pre>
                            )}
                        </div>
                    ))}
                </div>
            ) : (
                <SyntaxHighlighter
                    language={content.type === 'test' ? 'python' : 'json'}
                    style={a11yDark}
                    showLineNumbers={true}
                    customStyle={{
                        margin: 0,
                        borderRadius: '8px',
                        maxHeight: '70vh',
                    }}
                >
                    {content.content || ''}
                </SyntaxHighlighter>
            )}
        </Modal>
    );
};

export default FileViewerModal;