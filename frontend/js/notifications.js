// Toast Notification System

function showNotification(message, type = 'info', duration = 5000) {
    const container = document.getElementById('toast-container');
    
    if (!container) {
        console.error('Toast container not found');
        return;
    }
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    const icon = getNotificationIcon(type);
    
    toast.innerHTML = `
        <div class="toast-icon">${icon}</div>
        <div class="toast-message">${message}</div>
        <button class="toast-close" onclick="this.parentElement.remove()">×</button>
    `;
    
    container.appendChild(toast);
    
    // Auto-remove after duration
    if (duration > 0) {
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }
    
    return toast;
}

function getNotificationIcon(type) {
    const icons = {
        'success': '✓',
        'error': '✗',
        'warning': '⚠',
        'info': 'ℹ'
    };
    return icons[type] || icons['info'];
}

function showSuccessNotification(message, duration = 5000) {
    return showNotification(message, 'success', duration);
}

function showErrorNotification(message, duration = 5000) {
    return showNotification(message, 'error', duration);
}

function showWarningNotification(message, duration = 5000) {
    return showNotification(message, 'warning', duration);
}

function showInfoNotification(message, duration = 5000) {
    return showNotification(message, 'info', duration);
}

// Persistent notification (doesn't auto-close)
function showPersistentNotification(message, type = 'info') {
    return showNotification(message, type, 0);
}

// Clear all notifications
function clearAllNotifications() {
    const container = document.getElementById('toast-container');
    if (container) {
        container.innerHTML = '';
    }
}

// Add slideOut animation to CSS if not exists
if (!document.querySelector('style[data-toast-animations]')) {
    const style = document.createElement('style');
    style.setAttribute('data-toast-animations', 'true');
    style.textContent = `
        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(400px);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
}
