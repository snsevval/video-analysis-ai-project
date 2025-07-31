// ============= KAYITLAR SAYFASI JAVASCRIPT =============

// Global değişkenler
let allUsers = [];
let allCodes = [];
let refreshInterval = null;

// Sayfa yüklendiğinde
document.addEventListener('DOMContentLoaded', function() {
    console.log('📋 Kayıtlar sayfası yüklendi');
    
    // Admin kontrolü yap
    checkAdminAccess();
    loadAllData();
    createFloatingParticles();
    
    // Her 30 saniyede bir otomatik yenile
    refreshInterval = setInterval(loadAllData, 30000);
});

// Sayfa kapatılırken interval'i temizle
window.addEventListener('beforeunload', function() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
});

// ============= YETKİ KONTROL =============
function checkAdminAccess() {
    fetch('/check_admin_status')
        .then(response => response.json())
        .then(data => {
            if (!data.logged_in) {
                showNotification('❌ Giriş yapmalısınız!', 'error');
                setTimeout(() => window.location.href = '/', 2000);
            } else if (!data.is_admin) {
                showNotification('❌ Bu sayfaya erişim yetkiniz yok!', 'error');
                setTimeout(() => window.location.href = '/dashboard', 2000);
            } else {
                console.log('✅ Admin erişimi onaylandı:', data.email);
                document.getElementById('userEmail').textContent = data.email;
                document.getElementById('currentAdmin').textContent = data.email;
            }
        })
        .catch(error => {
            showNotification('❌ Yetki kontrolü başarısız!', 'error');
            console.error('Admin check error:', error);
        });
}

// ============= VERİ YÜKLEMELERİ =============
function loadAllData() {
    fetch('/admin/users_data')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
            allUsers = data.users || [];
            allCodes = data.codes || [];
            
            updateStatistics(data.stats || {});
            displayUsers(allUsers);
            displayCodes(allCodes);
            displayAnalysisHistory(data.analysis_history || []);
            
            console.log('📊 Veriler güncellendi:', {
                users: allUsers.length,
                codes: allCodes.length,
                stats: data.stats
            });
        })
        .catch(error => {
            showNotification(`❌ Veri yükleme hatası: ${error.message}`, 'error');
            console.error('Data loading error:', error);
            displayEmptyState();
        });
}

function displayEmptyState() {
    document.getElementById('usersList').innerHTML = '<div class="no-data">Veri yüklenirken hata oluştu</div>';
    document.getElementById('codesList').innerHTML = '<div class="no-data">Veri yüklenirken hata oluştu</div>';
    document.getElementById('analysisHistory').innerHTML = '<div class="no-data">Veri yüklenirken hata oluştu</div>';
}

// ============= İSTATİSTİK GÜNCELLEMELERİ =============
function updateStatistics(stats) {
    const animateNumber = (elementId, targetValue) => {
        const element = document.getElementById(elementId);
        const currentValue = parseInt(element.textContent) || 0;
        const increment = Math.ceil((targetValue - currentValue) / 10);
        
        if (currentValue < targetValue) {
            element.textContent = Math.min(currentValue + increment, targetValue);
            setTimeout(() => animateNumber(elementId, targetValue), 50);
        }
    };
    
    animateNumber('totalUsers', stats.total_users || 0);
    animateNumber('verifiedUsers', stats.verified_users || 0);
    animateNumber('todayCodes', stats.today_codes || 0);
    animateNumber('activeUsers', stats.today_logins || 0);
}

// ============= KULLANICI LİSTESİ =============
function displayUsers(users) {
    const container = document.getElementById('usersList');
    
    if (!users || users.length === 0) {
        container.innerHTML = '<div class="no-data">Henüz kullanıcı kaydı yok</div>';
        return;
    }

    const usersHtml = users.map((user, index) => {
        const verifiedClass = user.verified ? 'verified' : 'not-verified';
        const verifiedIcon = user.verified ? '✅' : '❌';
        const adminBadge = user.is_admin ? '<span class="admin-badge">👑 ADMIN</span>' : '';
        const lastLogin = user.last_login ? formatDate(user.last_login) : 'Hiç giriş yapmamış';
        
        return `
            <div class="record-item" style="animation-delay: ${index * 0.1}s">
                <div class="record-header">
                    <div>
                        <strong>${user.email}</strong>
                        ${adminBadge}
                    </div>
                    <div class="status-pill ${user.verified ? 'success' : 'danger'}">
                        ${user.verified ? 'Aktif' : 'Beklemede'}
                    </div>
                </div>
                <div class="record-details">
                    <span class="${verifiedClass}">${verifiedIcon} ${user.verified ? 'Doğrulandı' : 'Doğrulanmadı'}</span><br>
                    <small><i class="fas fa-clock me-1"></i>Son giriş: ${lastLogin}</small><br>
                    <small><i class="fas fa-calendar me-1"></i>Kayıt: ${formatDate(user.created_at)}</small>
                </div>
            </div>
        `;
    }).join('');

    container.innerHTML = usersHtml;
}

// ============= DOĞRULAMA KODLARI =============
function displayCodes(codes) {
    const container = document.getElementById('codesList');
    
    if (!codes || codes.length === 0) {
        container.innerHTML = '<div class="no-data">Henüz doğrulama kodu yok</div>';
        return;
    }

    const codesHtml = codes.slice(0, 15).map((code, index) => {
        let statusClass = 'code-pending';
        let statusText = '⏳ Bekliyor';
        let statusPill = 'warning';
        
        if (code.used) {
            statusClass = 'code-used';
            statusText = '✅ Kullanıldı';
            statusPill = 'success';
        } else if (new Date(code.expires_at) < new Date()) {
            statusClass = 'code-expired';
            statusText = '⏰ Süresi doldu';
            statusPill = 'danger';
        }

        const timeRemaining = code.used ? '' : getTimeRemaining(code.expires_at);

        return `
            <div class="record-item" style="animation-delay: ${index * 0.1}s">
                <div class="record-header">
                    <div>
                        <strong>${maskEmail(code.email)}</strong>
                    </div>
                    <div class="code-display">
                        ${code.code}
                    </div>
                </div>
                <div class="record-details">
                    <div class="status-pill ${statusPill}">${statusText}</div>
                    ${timeRemaining ? `<br><small><i class="fas fa-hourglass-half me-1"></i>${timeRemaining}</small>` : ''}
                    <br><small><i class="fas fa-paper-plane me-1"></i>Gönderilme: ${formatDate(code.created_at)}</small>
                    <br><small><i class="fas fa-clock me-1"></i>Bitiş: ${formatDate(code.expires_at)}</small>
                </div>
            </div>
        `;
    }).join('');

    container.innerHTML = codesHtml;
}

// ============= VİDEO ANALİZ GEÇMİŞİ =============
function displayAnalysisHistory(history) {
    const container = document.getElementById('analysisHistory');
    
    if (!history || history.length === 0) {
        container.innerHTML = '<div class="no-data">Henüz video analizi yapılmamış</div>';
        return;
    }

    const historyHtml = history.map((item, index) => `
        <div class="record-item" style="animation-delay: ${index * 0.1}s">
            <div class="record-header">
                <strong>${item.user_email}</strong>
                <span class="status-pill success">Tamamlandı</span>
            </div>
            <div class="record-details">
                <i class="fas fa-video me-1"></i>Video: ${item.video_name}<br>
                <i class="fas fa-calendar me-1"></i>Tarih: ${formatDate(item.created_at)}
            </div>
        </div>
    `).join('');

    container.innerHTML = historyHtml;
}

// ============= YÖNETİM FONKSİYONLARI =============
function cleanOldCodes() {
    if (!confirm('⚠️ 24 saatten eski doğrulama kodlarını silmek istediğinizden emin misiniz?\n\nBu işlem geri alınamaz.')) {
        return;
    }

    const button = event.target;
    const originalText = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Temizleniyor...';

    fetch('/admin/cleanup_old_codes', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(`🧹 ${data.message}`, 'success');
            loadAllData();
        } else {
            showNotification(`❌ ${data.error}`, 'error');
        }
    })
    .catch(error => {
        showNotification(`❌ Temizlik hatası: ${error.message}`, 'error');
    })
    .finally(() => {
        button.disabled = false;
        button.innerHTML = originalText;
    });
}

function exportUsers() {
    if (!allUsers || allUsers.length === 0) {
        showNotification('❌ Henüz kullanıcı verisi yok', 'warning');
        return;
    }

    const button = event.target;
    const originalText = button.innerHTML;
    button.disabled = true;
    button.classList.add('btn-exporting');

    try {
        const csvContent = generateUsersCSV(allUsers);
        const timestamp = new Date().toLocaleString('tr-TR').replace(/[/:]/g, '-').replace(/,/g, '');
        const filename = `SecurityVision_Kullanicilar_${timestamp}.csv`;
        
        downloadCSV(csvContent, filename);
        showNotification('📊 Kullanıcı listesi indiriliyor...', 'success');
        
        setTimeout(() => {
            button.disabled = false;
            button.classList.remove('btn-exporting');
            button.innerHTML = originalText;
        }, 2000);
        
    } catch (error) {
        showNotification(`❌ Export hatası: ${error.message}`, 'error');
        button.disabled = false;
        button.classList.remove('btn-exporting');
        button.innerHTML = originalText;
    }
}

function refreshData() {
    const button = event.target;
    const originalText = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Yenileniyor...';
    
    showNotification('🔄 Veriler yenileniyor...', 'info');
    
    loadAllData();
    
    setTimeout(() => {
        button.disabled = false;
        button.innerHTML = originalText;
    }, 2000);
}

// ============= CSV İŞLEMLERİ =============
function generateUsersCSV(users) {
    const headers = ['Email', 'Doğrulandı', 'Admin', 'Son Giriş', 'Kayıt Tarihi'];
    const rows = users.map(user => [
        user.email,
        user.verified ? 'Evet' : 'Hayır',
        user.is_admin ? 'Evet' : 'Hayır',
        user.last_login ? formatDate(user.last_login) : 'Hiç',
        formatDate(user.created_at)
    ]);

    const csvContent = [headers, ...rows]
        .map(row => row.map(field => `"${field}"`).join(','))
        .join('\n');
    
    // BOM ekle (Türkçe karakterler için)
    return '\ufeff' + csvContent;
}

function downloadCSV(content, filename) {
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
}

// ============= YARDIMCI FONKSİYONLAR =============
function formatDate(dateString) {
    if (!dateString) return 'Belirtilmemiş';
    
    try {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);
        
        if (diffMins < 1) return 'Az önce';
        if (diffMins < 60) return `${diffMins} dakika önce`;
        if (diffHours < 24) return `${diffHours} saat önce`;
        if (diffDays < 7) return `${diffDays} gün önce`;
        
        return date.toLocaleString('tr-TR', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch (error) {
        return 'Geçersiz tarih';
    }
}

function maskEmail(email) {
    if (!email || !email.includes('@')) return email;
    
    const [username, domain] = email.split('@');
    if (username.length <= 2) return email;
    
    const maskedUsername = username[0] + '*'.repeat(username.length - 2) + username[username.length - 1];
    return `${maskedUsername}@${domain}`;
}

function getTimeRemaining(expiresAt) {
    if (!expiresAt) return '';
    
    try {
        const now = new Date();
        const expiry = new Date(expiresAt);
        const diffMs = expiry - now;
        
        if (diffMs <= 0) return 'Süresi doldu';
        
        const minutes = Math.floor(diffMs / 60000);
        const seconds = Math.floor((diffMs % 60000) / 1000);
        
        if (minutes > 0) {
            return `${minutes} dk ${seconds} sn kaldı`;
        } else {
            return `${seconds} saniye kaldı`;
        }
    } catch (error) {
        return '';
    }
}

// ============= NOTİFİKASYON SİSTEMİ =============
function showNotification(message, type = 'info') {
    const container = document.getElementById('notificationContainer');
    
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
    
    // Otomatik kaldır
    setTimeout(() => {
        if (notification.parentElement) {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => notification.remove(), 300);
        }
    }, 5000);
    
    // Maximum 5 notification
    const notifications = container.querySelectorAll('.notification');
    if (notifications.length > 5) {
        notifications[0].remove();
    }
}

// ============= FLOATING PARTICLES =============
function createFloatingParticles() {
    const particleContainer = document.querySelector('.floating-particles');
    if (!particleContainer) return;
    
    // Önceki partikülleri temizle
    particleContainer.innerHTML = '';
    
    for (let i = 0; i < 30; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.cssText = `
            position: absolute;
            width: ${Math.random() * 3 + 1}px;
            height: ${Math.random() * 3 + 1}px;
            background: rgba(74, 144, 226, ${Math.random() * 0.5 + 0.2});
            border-radius: 50%;
            left: ${Math.random() * 100}%;
            top: ${Math.random() * 100}%;
            animation: float ${Math.random() * 15 + 10}s infinite linear;
            animation-delay: ${Math.random() * 5}s;
        `;
        particleContainer.appendChild(particle);
    }
}

// ============= KEYBOARD SHORTCUTS =============
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + R: Refresh data
    if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
        e.preventDefault();
        refreshData();
    }
    
    // Ctrl/Cmd + E: Export users
    if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
        e.preventDefault();
        exportUsers();
    }
    
    // Ctrl/Cmd + Delete: Clean old codes (admin only)
    if ((e.ctrlKey || e.metaKey) && e.key === 'Delete') {
        e.preventDefault();
        cleanOldCodes();
    }
});

// ============= VISIBILITY API =============
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        // Sayfa gizlendiğinde interval'i durdur
        if (refreshInterval) {
            clearInterval(refreshInterval);
            refreshInterval = null;
        }
    } else {
        // Sayfa görünür olduğunda tekrar başlat
        if (!refreshInterval) {
            refreshInterval = setInterval(loadAllData, 30000);
            loadAllData(); // Hemen bir kez yükle
        }
    }
});

// ============= ERROR HANDLING =============
window.addEventListener('error', function(e) {
    console.error('JavaScript Hatası:', e.error);
    showNotification('⚠️ Beklenmeyen bir hata oluştu', 'error');
});

window.addEventListener('unhandledrejection', function(e) {
    console.error('Promise Hatası:', e.reason);
    showNotification('⚠️ Ağ bağlantısı hatası', 'error');
});

// ============= DEBUGGING =============
if (window.location.hostname === 'localhost') {
    window.kayitlarDebug = {
        allUsers: () => allUsers,
        allCodes: () => allCodes,
        refreshData: refreshData,
        loadAllData: loadAllData,
        version: '1.0.0'
    };
    console.log('🔧 Debug modu aktif. Kullanım: kayitlarDebug.refreshData()');
}