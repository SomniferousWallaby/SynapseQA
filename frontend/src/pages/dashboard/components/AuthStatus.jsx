import { formatTimeAgo, formatTimeUntil } from '../../../utils/timeFormatters';

function getAuthStateStatus(authState) {
    if (!authState.exists) return 'error'; 
    if (authState.is_expired) return 'error'; 
    if (!authState.expires_at) return 'warning';
    return 'success';
}

const AuthStatus = ({ authState, onSetAuthState }) => {
    return (
        <div className="status-container">
            <div className={`status-box ${getAuthStateStatus(authState)}`}>
                <strong>Auth State:</strong>
                {(() => {
                    if (!authState.exists) return ' Not Found';
                    const lastUpdated = `(Updated ${formatTimeAgo(authState.last_modified)})`;
                    if (authState.is_expired) return ` Expired ${lastUpdated}`;
                    if (!authState.expires_at) return ` Present, expiration unknown ${lastUpdated}`;
                    const expires = `(Expires ${formatTimeUntil(authState.expires_at)})`;
                    return ` Valid ${expires}`;
                })()}
            </div>
            <button className="create-btn auth-btn" onClick={onSetAuthState}>Set Auth State</button>
        </div>
    );
};

export default AuthStatus;