// ===========================
// Student Mode JavaScript
// ===========================

const state = {
    chatHistory: [],
    currentSubject: 'all',
    isProcessing: false
};

const elements = {
    chatMessages: document.getElementById('chat-messages'),
    userInput: document.getElementById('user-input'),
    sendBtn: document.getElementById('send-btn'),
    subjectFilter: document.getElementById('subject-filter'),
    actionButtons: document.querySelectorAll('.action-btn')
};

// ===========================
// Chat Functions
// ===========================
function addMessage(content, type = 'user', source = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = type === 'user' ? '👤' : '🤖';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = formatMessage(content);

    if (source && type === 'assistant') {
        const sourceDiv = document.createElement('div');
        sourceDiv.className = 'message-source';
        sourceDiv.innerHTML = `📚 Sumber: ${source}`;
        contentDiv.appendChild(sourceDiv);
    }

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);
    elements.chatMessages.appendChild(messageDiv);
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;

    state.chatHistory.push({ content, type, source, timestamp: new Date() });
}

function formatMessage(text) {
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n/g, '<br>');
}

async function sendMessage() {
    const message = elements.userInput.value.trim();
    if (!message || state.isProcessing) return;

    addMessage(message, 'user');
    elements.userInput.value = '';

    state.isProcessing = true;
    elements.sendBtn.disabled = true;
    elements.sendBtn.innerHTML = '<span>Memproses...</span>';

    try {
        const response = await authenticatedFetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            body: JSON.stringify({
                message: message,
                subject_filter: state.currentSubject,
                history: state.chatHistory.slice(-5)
            })
        });

        if (!response) return;
        if (!response.ok) throw new Error('Network response was not ok');

        const data = await response.json();
        addMessage(data.response, 'assistant', data.source);
    } catch (error) {
        console.error('Error:', error);
        addMessage('Maaf, terjadi kesalahan. Pastikan server lokal berjalan dengan baik.', 'assistant');
    } finally {
        state.isProcessing = false;
        elements.sendBtn.disabled = false;
        elements.sendBtn.innerHTML = '<span>Kirim</span><span>➤</span>';
        elements.userInput.focus();
    }
}

// ===========================
// Quick Actions
// ===========================
function handleQuickAction(action) {
    const prompts = {
        ringkas: 'Tolong ringkas materi tentang ',
        contoh: 'Berikan contoh soal tentang ',
        latihan: 'Buatkan latihan soal tentang ',
        jelaskan: 'Jelaskan konsep '
    };
    elements.userInput.value = prompts[action] || '';
    elements.userInput.focus();
}

// ===========================
// Event Listeners
// ===========================
document.addEventListener('DOMContentLoaded', () => {
    elements.sendBtn.addEventListener('click', sendMessage);

    elements.userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    elements.subjectFilter.addEventListener('change', (e) => {
        state.currentSubject = e.target.value;
    });

    elements.actionButtons.forEach(btn => {
        btn.addEventListener('click', () => handleQuickAction(btn.dataset.action));
    });
});
