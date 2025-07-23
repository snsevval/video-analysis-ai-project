// Global Variables
let selectedFile = null;
let currentTaskId = null;
let pollInterval = null;
let isProcessing = false;

// DOM Elements
const fileInput = document.getElementById('fileInput');
const uploadArea = document.getElementById('uploadArea');
const uploadText = document.getElementById('uploadText');
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const analysisPanel = document.getElementById('analysisPanel');
const resultsPanel = document.getElementById('resultsPanel');

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    updateSystemStatus();
});

function initializeEventListeners() {
    // File input change
    fileInput.addEventListener('change', handleFileSelect);
    
    // Drag and drop
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
    
    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });
}

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function handleDragOver(e) {
    uploadArea.style.backgroundColor = 'rgba(74, 144, 226, 0.1)';
    uploadArea.style.borderColor = 'var(--accent-blue)';
}

function handleDragLeave(e) {
    uploadArea.style.backgroundColor = '';
    uploadArea.style.borderColor = '';
}

function handleDrop(e) {
    uploadArea.style.backgroundColor = '';
    uploadArea.style.borderColor = '';
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileSelect({ target: { files: files } });
    }
}

function handleFileSelect(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    // Validate file type
    const allowedTypes = ['video/mp4', 'video/avi', 'video/mov', 'video/quicktime', 'video/x-msvideo', 'video/x-ms-wmv', 'video/x-flv', 'video/webm'];
    const fileExtension = file.name.split('.').pop().toLowerCase();
    const allowedExtensions = ['mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm'];
    
    if (!allowedTypes.includes(file.type) && !allowedExtensions.includes(fileExtension)) {
        showNotification('Geçersiz dosya formatı! Desteklenen formatlar: MP4, AVI, MOV, MKV, WMV, FLV, WEBM', 'error');
        return;
    }
    
    // Validate file size (500MB max)
    if (file.size > 500 * 1024 * 1024) {
        showNotification('Dosya boyutu çok büyük! Maksimum 500MB olabilir.', 'error');
        return;
    }
    
    selectedFile = file;
    updateFileStatus(file);
    startBtn.disabled = false;
    
    showNotification(`✅ ${file.name} başarıyla seçildi (${formatFileSize(file.size)})`, 'success');
}

function updateFileStatus(file) {
    uploadText.innerHTML = `
        <strong>${file.name}</strong><br>
        <small>Boyut: ${formatFileSize(file.size)}</small>
    `;
    uploadArea.style.backgroundColor = 'rgba(40, 167, 69, 0.1)';
    uploadArea.style.borderColor = 'var(--success-color)';
}

function startProcessing() {
    if (!selectedFile || isProcessing) return;
    
    // Reset panels
    resetAnalysisState();
    
    // Show analysis panel
    analysisPanel.style.display = 'block';
    resultsPanel.style.display = 'none';
    
    // Update UI
    startBtn.disabled = true;
    stopBtn.disabled = false;
    isProcessing = true;
    
    // Update analysis info
    document.getElementById('fileName').textContent = selectedFile.name;
    document.getElementById('statusText').textContent = 'Yükleniyor...';
    updateProgress('Video yükleniyor...', 0);
    
    // Upload video
    uploadVideo();
}

function uploadVideo() {
    const formData = new FormData();
    formData.append('video', selectedFile);
    
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            currentTaskId = data.task_id;
            document.getElementById('analysisId').textContent = currentTaskId.substring(0, 8) + '...';
            document.getElementById('statusText').textContent = 'Analiz başlatılıyor...';
            
            showNotification('Video başarıyla yüklendi! Analiz başlatılıyor...', 'info');
            startPolling();
        } else {
            throw new Error(data.message);
        }
    })
    .catch(error => {
        showNotification(`Hata: ${error.message}`, 'error');
        stopProcessing();
    });
}

function startPolling() {
    if (pollInterval) clearInterval(pollInterval);
    
    pollInterval = setInterval(() => {
        if (currentTaskId && isProcessing) {
            checkStatus();
        }
    }, 2000);
}

function checkStatus() {
    fetch(`/status/${currentTaskId}`)
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const status = data.data;
            updateAnalysisStatus(status);
            
            if (status.status === 'completed') {
                clearInterval(pollInterval);
                showResults(status);
                isProcessing = false;
                stopBtn.disabled = true;
            } else if (status.status === 'failed') {
                clearInterval(pollInterval);
                showNotification(`Analiz başarısız: ${status.message}`, 'error');
                stopProcessing();
            }
        }
    })
    .catch(error => {
        console.error('Status check error:', error);
        showNotification('Durum kontrolünde hata oluştu', 'error');
    });
}

function updateAnalysisStatus(status) {
    const progress = status.progress || 0;
    const message = status.message || 'İşleniyor...';
    
    document.getElementById('statusText').textContent = status.status === 'processing' ? 'İşleniyor...' : 'Hazırlanıyor...';
    updateProgress(message, progress);
    
    // Update danger status based on progress
    if (progress > 0) {
        updateDangerStatus('Analiz devam ediyor...', 'Video işleniyor', 'Orta');
    }
}

function updateProgress(message, percent) {
    document.getElementById('progressMessage').textContent = message;
    document.getElementById('progressPercent').textContent = `${Math.round(percent)}%`;
    document.getElementById('progressBar').style.width = `${percent}%`;
}

function showResults(status) {
    const result = status.result;
    const stats = result.stats;
    
    // Show results panel
    resultsPanel.style.display = 'block';
    
    // Update statistics
    document.getElementById('statFrames').textContent = stats.processed_frames || 0;
    document.getElementById('statAlarms').textContent = stats.total_alarms || 0;
    document.getElementById('statDuration').textContent = Math.round((stats.total_frames || 0) / 30); // Assuming 30 FPS
    document.getElementById('statDangerous').textContent = stats.max_danger_level || 0;
    
    // Enable download buttons
    document.getElementById('downloadVideoBtn').disabled = false;
    document.getElementById('downloadDbBtn').disabled = false;
    
    // Update status
    document.getElementById('statusText').textContent = 'Tamamlandı';
    updateProgress('Analiz başarıyla tamamlandı!', 100);
    
    // Update danger status
    const dangerLevel = stats.max_danger_level || 0;
    const riskLevel = dangerLevel >= 7 ? 'Yüksek' : dangerLevel >= 4 ? 'Orta' : 'Düşük';
    updateDangerStatus(
        stats.total_alarms > 0 ? `${stats.total_alarms} alarm tespit edildi` : 'Tehlike tespit edilmedi',
        'Video analizi',
        riskLevel
    );
    
    // Update database status
    updateDatabaseStatus('Güncel', 'Az önce', `${stats.processed_frames} frame`);
    
    showNotification('🎉 Video analizi başarıyla tamamlandı!', 'success');
    
    // Reset for new analysis
    startBtn.disabled = false;
    startBtn.innerHTML = '<i class="fas fa-play me-2"></i>Yeni Analiz Başlat';
}

function stopProcessing() {
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
    
    isProcessing = false;
    startBtn.disabled = false;
    stopBtn.disabled = true;
    
    // Reset UI
    document.getElementById('statusText').textContent = 'Durduruldu';
    updateProgress('Analiz durduruldu', 0);
    
    // Reset danger status
    updateDangerStatus('Beklemede...', '-', 'Normal');
    
    showNotification('Analiz durduruldu', 'warning');
}

function downloadVideo() {
    if (!currentTaskId) {
        showNotification('İndirilebilir video bulunamadı', 'error');
        return;
    }
    
    const downloadUrl = `/download/video/${currentTaskId}`;
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = 'analyzed_video.mp4';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    showNotification('Video indiriliyor...', 'info');
}

function downloadDatabase() {
    if (!currentTaskId) {
        showNotification('İndirilebilir veritabanı bulunamadı', 'error');
        return;
    }
    
    const downloadUrl = `/download/database/${currentTaskId}`;
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = 'analysis_database.db';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    showNotification('Veritabanı indiriliyor...', 'info');
}

function resetAnalysisState() {
    document.getElementById('analysisId').textContent = '-';
    document.getElementById('fileName').textContent = '-';
    document.getElementById('statusText').textContent = '-';
    updateProgress('Hazırlanıyor...', 0);
}

// Utility Functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function updateSystemStatus(cpu = 45, ram = 67, gpu = 78) {
    document.getElementById('systemStatusText').textContent = 'Aktif ve çalışıyor';
    document.querySelector('#systemStatus small').textContent = `CPU: ${cpu}% | RAM: ${ram}% | GPU: ${gpu}%`;
    
    const avgUsage = (cpu + ram + gpu) / 3;
    document.getElementById('systemProgressBar').style.width = `${avgUsage}%`;
}

function updateDangerStatus(text, location, level) {
    document.getElementById('dangerText').textContent = text;
    document.getElementById('dangerLocation').textContent = location;
    document.getElementById('dangerLevel').textContent = `Risk Seviyesi: ${level}`;
    
    const dangerCard = document.getElementById('dangerStatus');
    dangerCard.className = 'status-card';
    
    if (level === 'Yüksek') {
        dangerCard.classList.add('danger');
    } else if (level === 'Orta') {
        dangerCard.classList.add('warning');
    } else {
        dangerCard.classList.add('success');
    }
}

function updateDatabaseStatus(status, lastUpdate, recordCount) {
    document.getElementById('dbStatusText').textContent = status;
    document.getElementById('dbLastUpdate').textContent = `Son güncelleme: ${lastUpdate}`;
    document.getElementById('dbRecordCount').textContent = `Toplam: ${recordCount}`;
}

// Notification System
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
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

// Additional Functions for existing buttons
function showDatabase() {
    // Placeholder for database view
    showNotification('Veritabanı görüntüleme özelliği geliştiriliyor...', 'info');
}

function analyzeVideo() {
    // Trigger file input
    fileInput.click();
}

function exportData() {
    if (!currentTaskId) {
        showNotification('Henüz analiz edilen bir video yok', 'warning');
        return;
    }
    
    // Download both files
    downloadVideo();
    setTimeout(() => downloadDatabase(), 1000);
}

// Floating particles animation (optional)
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

// Initialize particles
createFloatingParticles();