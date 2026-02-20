// ===========================
// Common Utilities (All Roles)
// ===========================

const API_BASE_URL = 'http://localhost:8000/api';

// ===========================
// Authentication Check
// ===========================
function checkAuth() {
    const token = localStorage.getItem('auth_token');
    const role = localStorage.getItem('user_role');
    if (!token || !role) {
        window.location.href = '/';
        return null;
    }
    return { token, role };
}

// ===========================
// Logout
// ===========================
async function handleLogout() {
    const auth = checkAuth();
    if (!auth) return;

    try {
        await fetch(`${API_BASE_URL}/auth/logout`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${auth.token}` }
        });
    } catch (error) {
        console.error('Logout error:', error);
    }

    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_role');
    localStorage.removeItem('username');
    localStorage.removeItem('remember_me');
    window.location.href = '/';
}

// ===========================
// Authenticated Fetch
// ===========================
async function authenticatedFetch(url, options = {}) {
    const auth = checkAuth();
    if (!auth) return null;

    const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${auth.token}`,
        ...options.headers
    };

    try {
        const response = await fetch(url, { ...options, headers });
        if (response.status === 401) {
            alert('Sesi Anda telah berakhir. Silakan login kembali.');
            handleLogout();
            return null;
        }
        if (response.status === 403) {
            alert('Anda tidak memiliki akses ke resource ini.');
            return null;
        }
        return response;
    } catch (error) {
        console.error('API call error:', error);
        throw error;
    }
}

// ===========================
// Network Status
// ===========================
function checkNetworkStatus() {
    const indicator = document.getElementById('offline-indicator');
    if (!indicator) return;

    fetch(`${API_BASE_URL}/health`)
        .then(response => {
            if (response.ok) {
                indicator.classList.remove('error');
                indicator.innerHTML = '<span class="status-dot"></span>Offline Aktif';
            }
        })
        .catch(() => {
            indicator.classList.add('error');
            indicator.innerHTML = '<span class="status-dot"></span>Server Terputus';
        });
}

// ===========================
// Display User Info
// ===========================
function displayUserInfo() {
    const username = localStorage.getItem('username');
    const el = document.getElementById('user-name');
    if (el && username) {
        el.textContent = username.charAt(0).toUpperCase() + username.slice(1);
    }
}

// ===========================
// Init
// ===========================
document.addEventListener('DOMContentLoaded', () => {
    const auth = checkAuth();
    if (!auth) return;
    displayUserInfo();
    checkNetworkStatus();
    setInterval(checkNetworkStatus, 30000);
});
