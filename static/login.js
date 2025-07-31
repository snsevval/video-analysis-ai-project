// ============= LOGIN PAGE JAVASCRIPT =============

function createFloatingParticles() {
    const particleContainer = document.querySelector('.floating-particles');
    if (!particleContainer) return;
    
    for (let i = 0; i < 50; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.cssText = `
            position: absolute;
            width: 2px;
            height: 2px;
            background: rgba(74, 144, 226, 0.3);
            border-radius: 50%;
            left: ${Math.random() * 100}%;
            top: ${Math.random() * 100}%;
            animation: float ${5 + Math.random() * 10}s infinite linear;
        `;
        particleContainer.appendChild(particle);
    }
}

function initializeLoginForm() {
    const loginForm = document.getElementById('loginForm');
    const emailInput = document.getElementById('email');
    
    if (!loginForm || !emailInput) return;
    
    loginForm.addEventListener('submit', function(e) {
        const email = emailInput.value.trim();
        
        if (!email || !isValidEmail(email)) {
            e.preventDefault();
            showNotification('❌ Geçerli bir e-mail adresi girin!', 'error');
            emailInput.focus();
            return false;
        }
        
        showNotification('🔐 Giriş yapılıyor...', 'info');
        return true;
    });
}

function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function showNotification(message, type = 'info') {
    const container = document.getElementById('notificationContainer');
    if (!container) return;
    
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    
    const icons = {
        success: 'fas fa-check-circle',
        error: 'fas fa-exclamation-circle',
        warning: 'fas fa-exclamation-triangle',
        info: 'fas fa-info-circle'
    };
    
    notification.innerHTML = `
        <i class="${icons[type]} me-2"></i>
        <span>${message}</span>
        <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
    `;
    
    container.appendChild(notification);
    
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

function initializeEmailEffects() {
    const emailInput = document.getElementById('email');
    if (!emailInput) return;
    
    emailInput.addEventListener('focus', function() {
        this.style.backgroundColor = 'rgba(74, 144, 226, 0.1)';
        this.style.borderColor = 'var(--accent-blue)';
        this.style.transform = 'translateY(-2px)';
    });

    emailInput.addEventListener('blur', function() {
        this.style.backgroundColor = 'rgba(74, 144, 226, 0.05)';
        this.style.borderColor = 'var(--border-color)';
        this.style.transform = 'translateY(0)';
    });

    emailInput.addEventListener('mouseover', function() {
        if (this !== document.activeElement) {
            this.style.borderColor = 'var(--accent-blue)';
            this.style.backgroundColor = 'rgba(74, 144, 226, 0.1)';
            this.style.transform = 'translateY(-2px)';
        }
    });

    emailInput.addEventListener('mouseleave', function() {
        if (this !== document.activeElement) {
            this.style.backgroundColor = 'rgba(74, 144, 226, 0.05)';
            this.style.borderColor = 'var(--border-color)';
            this.style.transform = 'translateY(0)';
        }
    });
}

document.addEventListener('DOMContentLoaded', function() {
    createFloatingParticles();
    initializeLoginForm();
    initializeEmailEffects();
    
    const emailInput = document.getElementById('email');
    if (emailInput) {
        setTimeout(() => emailInput.focus(), 100);
    }
});
// ============= EMAIL VERIFICATION FUNCTIONS =============

function sendVerificationCode() {
    const email = document.getElementById('email').value;
    
    if (!email || !isValidEmail(email)) {
        showNotification('❌ Geçerli bir email adresi girin!', 'error');
        return;
    }
    
    showNotification('📧 Doğrulama kodu gönderiliyor...', 'info');
    
    fetch('/send_verification', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email: email })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('✅ ' + data.message, 'success');
            document.getElementById('emailForm').style.display = 'none';
            document.getElementById('verificationForm').style.display = 'block';
            
            // Doğrulama koduna odaklan
            setTimeout(() => {
                document.getElementById('verificationCode').focus();
            }, 500);
        } else {
            showNotification('❌ ' + data.message, 'error');
        }
    })
    .catch(error => {
        showNotification('❌ Bağlantı hatası!', 'error');
        console.error('Error:', error);
    });
}

function verifyAndLogin() {
    const code = document.getElementById('verificationCode').value;
    
    if (!code || code.length !== 6) {
        showNotification('❌ 6 haneli doğrulama kodunu girin!', 'error');
        return;
    }
    
    showNotification('🔐 Doğrulama yapılıyor...', 'info');
    
    fetch('/verify_and_login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code: code })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('✅ ' + data.message, 'success');
            setTimeout(() => {
                window.location.href = data.redirect;
            }, 1500);
        } else {
            showNotification('❌ ' + data.message, 'error');
        }
    })
    .catch(error => {
        showNotification('❌ Bağlantı hatası!', 'error');
        console.error('Error:', error);
    });
}

function resendCode() {
    showNotification('📧 Yeni kod gönderiliyor...', 'info');
    
    fetch('/resend_code', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('✅ ' + data.message, 'success');
            document.getElementById('verificationCode').value = '';
            document.getElementById('verificationCode').focus();
        } else {
            showNotification('❌ ' + data.message, 'error');
        }
    })
    .catch(error => {
        showNotification('❌ Bağlantı hatası!', 'error');
        console.error('Error:', error);
    });
}

function backToEmail() {
    document.getElementById('verificationForm').style.display = 'none';
    document.getElementById('emailForm').style.display = 'block';
    document.getElementById('verificationCode').value = '';
    
    // Email inputa odaklan
    setTimeout(() => {
        document.getElementById('email').focus();
    }, 300);
}