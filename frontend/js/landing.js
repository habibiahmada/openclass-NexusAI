// ===========================
// Landing Page JavaScript
// ===========================

const API_BASE_URL = 'http://localhost:8000/api';

// Role configuration
const roleConfig = {
    siswa: { icon: '🎓', title: 'Login Siswa', endpoint: '/siswa' },
    guru:  { icon: '👨‍🏫', title: 'Login Guru',  endpoint: '/guru'  },
    admin: { icon: '⚙️', title: 'Login Admin', endpoint: '/admin' }
};

// ===========================
// Navbar Scroll
// ===========================
window.addEventListener('scroll', () => {
    const navbar = document.getElementById('navbar');
    if (window.scrollY > 50) {
        navbar.classList.add('scrolled');
    } else {
        navbar.classList.remove('scrolled');
    }
});

// ===========================
// Scroll Animations (Intersection Observer)
// ===========================
const observerOptions = { threshold: 0.1, rootMargin: '0px 0px -50px 0px' };
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('visible');
            observer.unobserve(entry.target);
        }
    });
}, observerOptions);

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.fade-up, .fade-in').forEach(el => observer.observe(el));
});

// ===========================
// Smooth Scroll
// ===========================
function scrollToRoles() {
    document.getElementById('roles').scrollIntoView({ behavior: 'smooth' });
}

// ===========================
// Login Modal
// ===========================
function showLoginForm(role) {
    const modal = document.getElementById('login-modal');
    const modalIcon = document.getElementById('modal-icon');
    const modalTitle = document.getElementById('modal-title');
    const roleInput = document.getElementById('role-input');

    const config = roleConfig[role];
    modalIcon.textContent = config.icon;
    modalTitle.textContent = config.title;
    roleInput.value = role;

    document.getElementById('login-form').reset();
    document.getElementById('error-message').style.display = 'none';

    modal.classList.add('active');
}

function closeLoginForm() {
    document.getElementById('login-modal').classList.remove('active');
}

// Close on backdrop click
window.addEventListener('click', (e) => {
    const modal = document.getElementById('login-modal');
    if (e.target === modal) closeLoginForm();
});

// Close on ESC
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeLoginForm();
});

// ===========================
// Login Handler
// ===========================
async function handleLogin(event) {
    event.preventDefault();

    const form = event.target;
    const formData = new FormData(form);
    const role = formData.get('role');
    const username = formData.get('username');
    const password = formData.get('password');
    const remember = formData.get('remember') === 'on';

    const submitBtn = document.getElementById('submit-btn');
    const btnText = document.getElementById('btn-text');
    const btnLoader = document.getElementById('btn-loader');
    const errorMessage = document.getElementById('error-message');

    submitBtn.disabled = true;
    btnText.style.display = 'none';
    btnLoader.style.display = 'inline-block';
    errorMessage.style.display = 'none';

    try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, role })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            localStorage.setItem('auth_token', data.token);
            localStorage.setItem('user_role', role);
            localStorage.setItem('username', username);
            if (remember) localStorage.setItem('remember_me', 'true');

            window.location.href = roleConfig[role].endpoint;
        } else {
            errorMessage.textContent = data.message || 'Login gagal. Periksa username dan password Anda.';
            errorMessage.style.display = 'block';
        }
    } catch (error) {
        console.error('Login error:', error);
        errorMessage.textContent = 'Terjadi kesalahan. Pastikan server berjalan dengan baik.';
        errorMessage.style.display = 'block';
    } finally {
        submitBtn.disabled = false;
        btnText.style.display = 'inline-block';
        btnLoader.style.display = 'none';
    }
}

// ===========================
// Network Status
// ===========================
function checkNetworkStatus() {
    const indicator = document.getElementById('offline-indicator');
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
// Auto-login
// ===========================
function checkAutoLogin() {
    const token = localStorage.getItem('auth_token');
    const role = localStorage.getItem('user_role');
    const rememberMe = localStorage.getItem('remember_me');

    if (token && role && rememberMe === 'true') {
        fetch(`${API_BASE_URL}/auth/verify`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            }
        })
        .then(res => res.json())
        .then(data => {
            if (data.valid) {
                window.location.href = roleConfig[role].endpoint;
            }
        })
        .catch(err => console.log('Auto-login failed:', err));
    }
}

// ===========================
// Init
// ===========================
document.addEventListener('DOMContentLoaded', () => {
    checkNetworkStatus();
    checkAutoLogin();
    setInterval(checkNetworkStatus, 30000);
});
