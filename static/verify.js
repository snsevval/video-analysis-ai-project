// ============= EMAIL VERIFICATION PAGE JAVASCRIPT =============

// Floating particles
function createFloatingParticles() {
    const particleContainer = document.querySelector('.floating-particles');
    if (!particleContainer) return;
    
    for (let i = 0; i < 30; i++) {
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

// Code input handling
function initializeCodeInputs() {
    const inputs = document.querySelectorAll('.code-input');
    
    inputs.forEach((input, index) => {
        // Only allow numbers
        input.addEventListener('input', function(e) {
            const value = e.target.value;
            if (!/^\d*$/.test(value)) {
                e.target.value = '';
                return;
            }
            
            // Auto-focus to next input
            if (value && index < inputs.length - 1) {
                inputs[index + 1].focus();
            }
        });
        
        // Handle backspace
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Backspace' && !e.target.value && index > 0) {
                inputs[index - 1].focus();
            }
        });
        
        // Handle paste
        input.addEventListener('paste', function(e) {
            e.preventDefault();
            const pasteData = e.clipboardData.getData('text');
            const digits = pasteData.replace(/\D/g, '').split('');
            
            digits.forEach((digit, i) => {
                if (i < inputs.length) {
                    inputs[i].value = digit;
                }
            });
            
            // Focus last filled input or next empty
            const lastIndex = Math.min(digits.length, inputs.length) - 1;
            if (lastIndex >= 0) {
                inputs[lastIndex].focus();
            }
        });
    });
}

// Get verification code from inputs
function getVerificationCode() {
    const inputs = document.querySelectorAll('.code-input');
    let code = '';
    inputs.forEach(input => {
        code += input.value;
    });
    return code;
}

// Clear all inputs
function clearCodeInputs() {
    const inputs = document.querySelectorAll('.code-input');
    inputs.forEach(input => {
        input.value = '';
    });
    inputs[0].focus();
}

// Verify form submission
function initializeVerifyForm() {
    const verifyForm = document.getElementById('verifyForm');
    const verifyBtn = document.getElementById('verifyBtn');
    
    verifyForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const code = getVerificationCode();
        
        if (code.length !== 6) {
            showNotification('❌ 6 haneli kodu tam olarak girin!', 'error');
            return;
        }
        
        // Disable form
        verifyBtn.disabled = true;
        verifyBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Doğrulanıyor...';
        
        // Send verification request
        const formData = new FormData();
        formData.append('code', code);
        
        fetch('/verify_code', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('✅ ' + data.message, 'success');
                setTimeout(() => {
                    window.location.href = data.redirect || '/dashboard';
                }, 1500);
            } else {
                showNotification('❌ ' + data.message, 'error');
                clearCodeInputs();
            }
        })
        .catch(error => {
            showNotification('❌ Bağlantı hatası: ' + error.message, 'error');
            clearCodeInputs();
        })
        .finally(() => {
            verifyBtn.disabled = false;
            verifyBtn.innerHTML = '<i class="fas fa-check-circle me-2"></i>Kodu Doğrula';
        });
    });
}

// Resend code functionality
function initializeResendButton() {
    const resendBtn = document.getElementById('resendBtn');
    let resendCooldown = 0;
    
    function updateResendButton() {
        if (resendCooldown > 0) {
            resendBtn.disabled = true;
            resendBtn.innerHTML = `<i class="fas fa-clock me-2"></i>Tekrar Gönder (${resendCooldown}s)`;
            resendCooldown--;
            setTimeout(updateResendButton, 1000);
        } else {
            resendBtn.disabled = false;
            resendBtn.innerHTML = '<i class="fas fa-redo me-2"></i>Yeni Kod Gönder';
        }
    }
    
    resendBtn.addEventListener('click', function() {
        if (resendCooldown > 0) return;
        
        resendBtn.disabled = true;
        resendBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Gönderiliyor...';
        
        fetch('/resend_code', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('✅ ' + data.message, 'success');
                clearCodeInputs();
                resendCooldown = 120; // 2 minute cooldown
                updateResendButton();
            } else {
                showNotification('❌ ' + data.message, 'error');
                resendBtn.disabled = false;
                resendBtn.innerHTML = '<i class="fas fa-redo me-2"></i>Yeni Kod Gönder';
            }
        })
        .catch(error => {
            showNotification('❌ Bağlantı hatası: ' + error.message, 'error');
            resendBtn.disabled = false;
            resendBtn.innerHTML = '<i class="fas fa-redo me-2"></i>Yeni Kod Gönder';
        });
    });
}

// Notification system
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

// Auto-expire timer
function startExpirationTimer() {
    let timeLeft = 10 * 60; // 10 minutes in seconds
    
    function updateTimer() {
        if (timeLeft <= 0) {
            showNotification('⏰ Doğrulama kodunuzun süresi doldu. Yeni kod isteyin.', 'warning');
            return;
        }
        
        const minutes = Math.floor(timeLeft / 60);
        const seconds = timeLeft % 60;
        
        const timerElement = document.querySelector('.login-security-text');
        if (timerElement) {
            timerElement.innerHTML = `
                <i class="fas fa-clock me-1"></i>
                Kodunuz ${minutes}:${seconds.toString().padStart(2, '0')} içinde geçersiz olacak
            `;
        }
        
        timeLeft--;
        setTimeout(updateTimer, 1000);
    }
    
    updateTimer();
}

// Initialize everything when DOM loads
document.addEventListener('DOMContentLoaded', function() {
    createFloatingParticles();
    initializeCodeInputs();
    initializeVerifyForm();
    initializeResendButton();
    startExpirationTimer();
    
    // Auto-focus first input
    const firstInput = document.getElementById('digit1');
    if (firstInput) {
        setTimeout(() => firstInput.focus(), 100);
    }
    
    // Add fade-in animation
    document.querySelector('.main-container').style.opacity = '0';
    setTimeout(() => {
        document.querySelector('.main-container').style.transition = 'opacity 0.5s ease';
        document.querySelector('.main-container').style.opacity = '1';
    }, 100);
});