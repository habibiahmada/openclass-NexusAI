// Admin Dashboard JavaScript

// Auto-refresh interval (30 seconds)
const REFRESH_INTERVAL = 30000;
let refreshTimer = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    console.log('Admin Dashboard initialized');
    loadDashboard();
    startAutoRefresh();
});

// Load all dashboard data
async function loadDashboard() {
    try {
        showLoading('Loading dashboard data...');
        
        // Load all sections in parallel
        await Promise.all([
            loadAWSStatus(),
            loadSystemHealth(),
            loadRecentActivity()
        ]);
        
        updateLastRefreshTime();
        hideLoading();
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showNotification('Failed to load dashboard data', 'error');
        hideLoading();
    }
}

// Load AWS Services Status
async function loadAWSStatus() {
    try {
        const response = await fetch('/api/admin/aws-status');
        const data = await response.json();
        
        // S3 Status
        updateStatusBadge('s3-status', data.s3.connected);
        document.getElementById('s3-bucket').textContent = data.s3.bucket || 'Not configured';
        document.getElementById('s3-last-upload').textContent = formatDate(data.s3.last_upload);
        document.getElementById('s3-total-files').textContent = data.s3.total_files || '0';
        document.getElementById('s3-storage').textContent = formatBytes(data.s3.storage_bytes);
        
        // Bedrock Status
        updateStatusBadge('bedrock-status', data.bedrock.connected);
        document.getElementById('bedrock-strategy').textContent = data.bedrock.strategy || 'Not configured';
        document.getElementById('bedrock-model').textContent = data.bedrock.model_id || '--';
        document.getElementById('bedrock-fallback').textContent = data.bedrock.fallback_enabled ? 'Enabled' : 'Disabled';
        document.getElementById('bedrock-region').textContent = data.bedrock.region || '--';
        
        // CloudFront Status
        updateStatusBadge('cloudfront-status', data.cloudfront.configured);
        document.getElementById('cloudfront-dist').textContent = data.cloudfront.distribution_id || 'Not configured';
        document.getElementById('cloudfront-domain').textContent = data.cloudfront.domain || '--';
        document.getElementById('cloudfront-invalidation').textContent = formatDate(data.cloudfront.last_invalidation);
        
        // Lambda Status
        updateStatusBadge('lambda-status', data.lambda.deployed);
        document.getElementById('lambda-function').textContent = data.lambda.function_name || 'Not deployed';
        document.getElementById('lambda-last-exec').textContent = formatDate(data.lambda.last_execution);
        document.getElementById('lambda-success-rate').textContent = data.lambda.success_rate ? `${data.lambda.success_rate}%` : '--';
        document.getElementById('lambda-duration').textContent = data.lambda.avg_duration ? `${data.lambda.avg_duration}ms` : '--';
        
    } catch (error) {
        console.error('Error loading AWS status:', error);
        showNotification('Failed to load AWS status', 'error');
    }
}

// Load System Health
async function loadSystemHealth() {
    try {
        const response = await fetch('/api/admin/system-health');
        const data = await response.json();
        
        // PostgreSQL
        updateStatusBadge('postgres-status', data.postgresql.connected);
        document.getElementById('postgres-connection').textContent = data.postgresql.connected ? 'Connected' : 'Disconnected';
        document.getElementById('postgres-latency').textContent = data.postgresql.latency ? `${data.postgresql.latency}ms` : '--';
        document.getElementById('postgres-connections').textContent = data.postgresql.active_connections || '0';
        document.getElementById('postgres-size').textContent = formatBytes(data.postgresql.database_size);
        
        // ChromaDB
        updateStatusBadge('chromadb-status', data.chromadb.connected);
        document.getElementById('chromadb-collections').textContent = data.chromadb.collections || '0';
        document.getElementById('chromadb-documents').textContent = data.chromadb.total_documents || '0';
        document.getElementById('chromadb-size').textContent = formatBytes(data.chromadb.storage_size);
        document.getElementById('chromadb-last-update').textContent = formatDate(data.chromadb.last_update);
        
        // LLM Model
        updateStatusBadge('llm-status', data.llm.loaded);
        document.getElementById('llm-model').textContent = data.llm.model_name || 'Not loaded';
        document.getElementById('llm-loaded').textContent = data.llm.loaded ? 'Loaded' : 'Not loaded';
        document.getElementById('llm-memory').textContent = formatBytes(data.llm.memory_usage);
        document.getElementById('llm-inference-time').textContent = data.llm.avg_inference_time ? `${data.llm.avg_inference_time}ms` : '--';
        
        // System Resources
        const resourcesStatus = data.resources.disk_usage < 80 && data.resources.ram_usage < 80;
        updateStatusBadge('resources-status', resourcesStatus);
        document.getElementById('cpu-usage').textContent = `${data.resources.cpu_usage}%`;
        document.getElementById('ram-usage').textContent = `${data.resources.ram_usage}%`;
        document.getElementById('disk-space').textContent = `${data.resources.disk_usage}% (${formatBytes(data.resources.disk_free)} free)`;
        document.getElementById('system-uptime').textContent = formatUptime(data.resources.uptime_seconds);
        
    } catch (error) {
        console.error('Error loading system health:', error);
        showNotification('Failed to load system health', 'error');
    }
}

// Load Recent Activity
async function loadRecentActivity() {
    try {
        const response = await fetch('/api/admin/recent-activity');
        const data = await response.json();
        
        // ETL Pipeline Runs
        renderActivityList('etl-runs-list', data.etl_runs, (run) => `
            <div class="activity-item">
                <div>${run.job_id}</div>
                <div class="time">${formatDate(run.started_at)}</div>
                <span class="status ${run.status}">${run.status}</span>
            </div>
        `);
        
        // VKP Updates
        renderActivityList('vkp-updates-list', data.vkp_updates, (update) => `
            <div class="activity-item">
                <div>${update.subject} Kelas ${update.grade} v${update.version}</div>
                <div class="time">${formatDate(update.installed_at)}</div>
            </div>
        `);
        
        // Telemetry Uploads
        renderActivityList('telemetry-uploads-list', data.telemetry_uploads, (upload) => `
            <div class="activity-item">
                <div>Metrics uploaded: ${upload.metrics_count} records</div>
                <div class="time">${formatDate(upload.uploaded_at)}</div>
            </div>
        `);
        
        // Backups
        renderActivityList('backups-list', data.backups, (backup) => `
            <div class="activity-item">
                <div>${backup.type} backup (${formatBytes(backup.size)})</div>
                <div class="time">${formatDate(backup.created_at)}</div>
            </div>
        `);
        
    } catch (error) {
        console.error('Error loading recent activity:', error);
        showNotification('Failed to load recent activity', 'error');
    }
}

// Render activity list
function renderActivityList(elementId, items, template) {
    const container = document.getElementById(elementId);
    
    if (!items || items.length === 0) {
        container.innerHTML = '<p class="loading">No recent activity</p>';
        return;
    }
    
    container.innerHTML = items.map(template).join('');
}

// Update status badge
function updateStatusBadge(elementId, isConnected) {
    const badge = document.getElementById(elementId);
    badge.className = 'status-badge';
    
    if (isConnected) {
        badge.classList.add('status-connected');
        badge.textContent = 'Connected';
    } else {
        badge.classList.add('status-disconnected');
        badge.textContent = 'Disconnected';
    }
}

// Quick Actions
async function checkVKPUpdates() {
    try {
        showLoading('Checking for VKP updates...');
        
        const response = await fetch('/api/admin/check-vkp-updates', {
            method: 'POST'
        });
        const data = await response.json();
        
        hideLoading();
        
        if (data.updates_available && data.updates_available.length > 0) {
            showNotification(`${data.updates_available.length} VKP updates available!`, 'info');
            // Refresh activity
            loadRecentActivity();
        } else {
            showNotification('No VKP updates available', 'success');
        }
    } catch (error) {
        console.error('Error checking VKP updates:', error);
        hideLoading();
        showNotification('Failed to check for updates', 'error');
    }
}

async function runETLPipeline() {
    if (!confirm('Run ETL pipeline now? This may take several minutes.')) {
        return;
    }
    
    try {
        showLoading('Starting ETL pipeline...');
        
        const response = await fetch('/api/admin/run-etl', {
            method: 'POST'
        });
        const data = await response.json();
        
        hideLoading();
        
        if (data.success) {
            showNotification('ETL pipeline started successfully', 'success');
            // Redirect to job history
            setTimeout(() => {
                window.location.href = 'job_history.html';
            }, 2000);
        } else {
            showNotification('Failed to start ETL pipeline', 'error');
        }
    } catch (error) {
        console.error('Error running ETL pipeline:', error);
        hideLoading();
        showNotification('Failed to start ETL pipeline', 'error');
    }
}

async function invalidateCache() {
    if (!confirm('Invalidate CloudFront cache? This will clear all cached content.')) {
        return;
    }
    
    try {
        showLoading('Invalidating CloudFront cache...');
        
        const response = await fetch('/api/admin/invalidate-cache', {
            method: 'POST'
        });
        const data = await response.json();
        
        hideLoading();
        
        if (data.invalidation_id) {
            showNotification('Cache invalidation started', 'success');
            loadAWSStatus();
        } else {
            showNotification('Failed to invalidate cache', 'error');
        }
    } catch (error) {
        console.error('Error invalidating cache:', error);
        hideLoading();
        showNotification('Failed to invalidate cache', 'error');
    }
}

async function runManualBackup() {
    if (!confirm('Run manual backup now? This may take a few minutes.')) {
        return;
    }
    
    try {
        showLoading('Creating backup...');
        
        const response = await fetch('/api/admin/run-backup', {
            method: 'POST'
        });
        const data = await response.json();
        
        hideLoading();
        
        if (data.success) {
            showNotification('Backup created successfully', 'success');
            loadRecentActivity();
        } else {
            showNotification('Failed to create backup', 'error');
        }
    } catch (error) {
        console.error('Error creating backup:', error);
        hideLoading();
        showNotification('Failed to create backup', 'error');
    }
}

function viewJobHistory() {
    window.location.href = 'job_history.html';
}

function openSettings() {
    window.location.href = 'settings.html';
}

// Refresh dashboard
function refreshDashboard() {
    loadDashboard();
}

// Auto-refresh
function startAutoRefresh() {
    if (refreshTimer) {
        clearInterval(refreshTimer);
    }
    
    refreshTimer = setInterval(() => {
        loadDashboard();
    }, REFRESH_INTERVAL);
}

function stopAutoRefresh() {
    if (refreshTimer) {
        clearInterval(refreshTimer);
        refreshTimer = null;
    }
}

// Update last refresh time
function updateLastRefreshTime() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('id-ID');
    document.getElementById('last-refresh').textContent = `Last refresh: ${timeString}`;
}

// Utility functions
function formatDate(dateString) {
    if (!dateString) return '--';
    
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    // Less than 1 minute
    if (diff < 60000) {
        return 'Just now';
    }
    
    // Less than 1 hour
    if (diff < 3600000) {
        const minutes = Math.floor(diff / 60000);
        return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    }
    
    // Less than 24 hours
    if (diff < 86400000) {
        const hours = Math.floor(diff / 3600000);
        return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    }
    
    // More than 24 hours
    return date.toLocaleDateString('id-ID', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatBytes(bytes) {
    if (!bytes || bytes === 0) return '0 B';
    
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function formatUptime(seconds) {
    if (!seconds) return '--';
    
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) {
        return `${days}d ${hours}h ${minutes}m`;
    } else if (hours > 0) {
        return `${hours}h ${minutes}m`;
    } else {
        return `${minutes}m`;
    }
}

function showLoading(message) {
    const modal = document.getElementById('loading-modal');
    const messageEl = document.getElementById('loading-message');
    messageEl.textContent = message;
    modal.style.display = 'flex';
}

function hideLoading() {
    const modal = document.getElementById('loading-modal');
    modal.style.display = 'none';
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    stopAutoRefresh();
});
