// ===========================
// Admin Mode JavaScript
// ===========================

async function loadAdminPanel() {
    try {
        const response = await authenticatedFetch(`${API_BASE_URL}/admin/status`);
        if (!response) return;

        const data = await response.json();

        document.getElementById('model-status').textContent = data.model_status || 'Unknown';
        document.getElementById('db-status').textContent = data.db_status || 'Unknown';
        document.getElementById('system-version').textContent = data.version || '1.0.0';
        document.getElementById('ram-usage').textContent = data.ram_usage || 'N/A';
        document.getElementById('storage-usage').textContent = data.storage_usage || 'N/A';

        // Style status values
        const modelEl = document.getElementById('model-status');
        const dbEl = document.getElementById('db-status');
        modelEl.className = 'status-value' + (data.model_status === 'Aktif' ? '' : ' warning');
        dbEl.className = 'status-value' + (data.db_status === 'Terhubung' ? '' : ' error');
    } catch (error) {
        console.error('Error loading admin panel:', error);
    }
}

async function updateModel() {
    if (!confirm('Apakah Anda yakin ingin mengupdate model AI? Proses ini memerlukan waktu.')) return;

    try {
        const response = await authenticatedFetch(`${API_BASE_URL}/admin/update-model`, { method: 'POST' });
        if (!response) return;
        const data = await response.json();
        alert(data.message || 'Update berhasil');
    } catch (error) {
        console.error('Error updating model:', error);
        alert('Gagal mengupdate model');
    }
}

async function updateCurriculum() {
    if (!confirm('Apakah Anda yakin ingin mengupdate kurikulum?')) return;

    try {
        const response = await authenticatedFetch(`${API_BASE_URL}/admin/update-curriculum`, { method: 'POST' });
        if (!response) return;
        const data = await response.json();
        alert(data.message || 'Update berhasil');
    } catch (error) {
        console.error('Error updating curriculum:', error);
        alert('Gagal mengupdate kurikulum');
    }
}

async function createBackup() {
    try {
        const response = await authenticatedFetch(`${API_BASE_URL}/admin/backup`, { method: 'POST' });
        if (!response) return;
        const data = await response.json();
        alert(data.message || 'Backup berhasil dibuat');
    } catch (error) {
        console.error('Error creating backup:', error);
        alert('Gagal membuat backup');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    loadAdminPanel();
    setInterval(loadAdminPanel, 30000);
});
