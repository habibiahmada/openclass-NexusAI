// ===========================
// Teacher Mode JavaScript
// ===========================

async function loadTeacherDashboard() {
    try {
        const response = await authenticatedFetch(`${API_BASE_URL}/teacher/stats`);
        if (!response) return;

        const data = await response.json();

        document.getElementById('total-questions').textContent = data.total_questions || 0;
        document.getElementById('popular-topic').textContent = data.popular_topic || '-';
        document.getElementById('active-students').textContent = data.active_students || 0;

        if (data.topics && data.topics.length > 0) {
            const topicList = document.getElementById('topic-list');
            topicList.innerHTML = data.topics.map(topic => `
                <div class="topic-item">
                    <span class="topic-name">${topic.name}</span>
                    <span class="topic-count">${topic.count} pertanyaan</span>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading teacher dashboard:', error);
    }
}

async function exportReport(format) {
    try {
        const response = await authenticatedFetch(`${API_BASE_URL}/teacher/export?format=${format}`);
        if (!response) return;

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `laporan_${Date.now()}.${format}`;
        a.click();
    } catch (error) {
        console.error('Error exporting:', error);
        alert('Gagal mengekspor laporan');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    loadTeacherDashboard();
    setInterval(loadTeacherDashboard, 60000);
});
