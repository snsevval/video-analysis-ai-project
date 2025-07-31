// ============= ADMIN CONTROL SYSTEM =============
// SecurityVision Admin Status Controller
// Bu dosya dashboard ve diğer sayfalarda admin kontrolü yapar

// Global admin durumu
let currentUser = {
    logged_in: false,
    email: null,
    is_admin: false,
    login_time: null
};

// Admin durumunu kontrol et
function checkAdminStatus() {
    return fetch('/check_admin_status')
        .then(response => response.json())
        .then(data => {
            // Global user durumunu güncelle
            currentUser = {
                logged_in: data.logged_in || false,
                email: data.email || null,
                is_admin: data.is_admin || false,
                login_time: data.login_time || null
            };
            
            if (data.logged_in) {
                // Kullanıcı email'ini göster
                updateUserEmail(data.email);
                
                // Admin ise Kayıtlar linkini göster
                if (data.is_admin) {
                    showAdminLinks();
                    console.log('✅ Admin erişimi - Kayıtlar linki aktif');
                } else {
                    hideAdminLinks();
                    console.log('👤 Normal kullanıcı - Admin paneli gizli');
                }
                
                // Admin badge göster (varsa)
                showAdminBadge(data.is_admin);
                
            } else {
                // Giriş yapılmamışsa login sayfasına yönlendir
                console.log('❌ Giriş yapılmamış, yönlendiriliyor...');
                redirectToLogin();
            }
            
            return currentUser;
        })
        .catch(error => {
            console.error('Admin kontrol hatası:', error);
            // Hata durumunda da login'e yönlendir
            redirectToLogin();
            throw error;
        });
}

// Kullanıcı email'ini navbar'da göster
function updateUserEmail(email) {
    const userEmailSpan = document.getElementById('userEmail');
    if (userEmailSpan && email) {
        userEmailSpan.textContent = email;
    }
    
    // Diğer yerlerde de email gösteriliyorsa
    const userDisplayElements = document.querySelectorAll('.user-display, .current-user');
    userDisplayElements.forEach(element => {
        if (element && email) {
            element.textContent = email;
        }
    });
}

// Admin linklerini göster
function showAdminLinks() {
    // Kayıtlar linki
    const kayitlarLink = document.getElementById('kayitlarLink');
    if (kayitlarLink) {
        kayitlarLink.style.display = 'block';
    }
    
    // Diğer admin linkleri (varsa)
    const adminElements = document.querySelectorAll('.admin-only, [data-admin-only]');
    adminElements.forEach(element => {
        element.style.display = 'block';
    });
}

// Admin linklerini gizle
function hideAdminLinks() {
    // Kayıtlar linki
    const kayitlarLink = document.getElementById('kayitlarLink');
    if (kayitlarLink) {
        kayitlarLink.style.display = 'none';
    }
    
    // Diğer admin linkleri (varsa)
    const adminElements = document.querySelectorAll('.admin-only, [data-admin-only]');
    adminElements.forEach(element => {
        element.style.display = 'none';
    });
}

// Admin badge göster/gizle
function showAdminBadge(isAdmin) {
    const adminBadge = document.getElementById('adminBadge');
    if (adminBadge) {
        if (isAdmin) {
            adminBadge.style.display = 'inline-block';
            adminBadge.innerHTML = '<i class="fas fa-crown me-1"></i>ADMIN';
        } else {
            adminBadge.style.display = 'none';
        }
    }
}

// Login sayfasına yönlendir
function redirectToLogin() {
    // Mevcut sayfa login değilse yönlendir
    if (!window.location.pathname.includes('/') || window.location.pathname !== '/') {
        setTimeout(() => {
            window.location.href = '/';
        }, 1000);
    }
}

// Admin yetkisi kontrol et (sayfa erişimi için)
function requireAdmin() {
    return checkAdminStatus().then(user => {
        if (!user.is_admin) {
            console.log('❌ Admin yetkisi gerekli');
            alert('Bu sayfaya erişim yetkiniz yok!');
            window.location.href = '/dashboard';
            return false;
        }
        return true;
    });
}

// Kullanıcı bilgilerini al
function getCurrentUser() {
    return currentUser;
}

// Logout fonksiyonu
function performLogout() {
    if (confirm('Çıkış yapmak istediğinizden emin misiniz?')) {
        window.location.href = '/logout';
    }
}

// Sayfa yüklendiğinde otomatik kontrol
document.addEventListener('DOMContentLoaded', function() {
    // Admin kontrolünü çalıştır
    checkAdminStatus().catch(error => {
        console.error('Sayfa yüklenirken admin kontrol hatası:', error);
    });
    
    // Logout button'a event listener ekle (varsa)
    const logoutButtons = document.querySelectorAll('.logout-btn, [data-logout]');
    logoutButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            performLogout();
        });
    });
});

// Periyodik kontrol (5 dakikada bir)
setInterval(function() {
    checkAdminStatus().catch(error => {
        console.error('Periyodik admin kontrol hatası:', error);
    });
}, 5 * 60 * 1000); // 5 dakika

// Export functions for external use
window.AdminControl = {
    checkAdminStatus,
    getCurrentUser,
    requireAdmin,
    performLogout,
    updateUserEmail,
    showAdminLinks,
    hideAdminLinks
};

// Debug mode (localhost'ta)
if (window.location.hostname === 'localhost') {
    window.adminDebug = {
        currentUser: () => currentUser,
        checkStatus: checkAdminStatus,
        forceAdmin: () => showAdminLinks(),
        forceHide: () => hideAdminLinks()
    };
    console.log('🔧 Admin Debug Mode: adminDebug.checkStatus()');
}