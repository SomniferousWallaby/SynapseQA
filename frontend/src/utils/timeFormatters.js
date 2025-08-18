export function formatTimeAgo(isoString) {
    if (!isoString) return '';
    const date = new Date(isoString);
    const now = new Date();
    const seconds = Math.round((now - date) / 1000);
    const minutes = Math.round(seconds / 60);
    const hours = Math.round(minutes / 60);
    const days = Math.round(hours / 24);

    if (seconds < 60) return `${seconds} second${seconds === 1 ? '' : 's'} ago`;
    if (minutes < 60) return `${minutes} minute${minutes === 1 ? '' : 's'} ago`;
    if (hours < 24) return `${hours} hour${hours === 1 ? '' : 's'} ago`;
    return `${days} day${days === 1 ? '' : 's'} ago`;
}

export function formatTimeUntil(isoString) {
    if (!isoString) return '';
    const date = new Date(isoString);
    const now = new Date();
    const seconds = Math.round((date - now) / 1000);
    const minutes = Math.round(seconds / 60);
    const hours = Math.round(minutes / 60);
    const days = Math.round(hours / 24);

    if (seconds < 0) return 'already'; // Should be caught by is_expired, but a good fallback.
    if (seconds < 60) return `in ${seconds} second${seconds === 1 ? '' : 's'}`;
    if (minutes < 60) return `in ${minutes} minute${minutes === 1 ? '' : 's'}`;
    if (hours < 24) return `in ${hours} hour${hours === 1 ? '' : 's'}`;
    return `in ${days} day${days === 1 ? '' : 's'}`;
}