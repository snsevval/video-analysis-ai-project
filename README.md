# SecurityVision - Yapay Zeka Destekli Güvenlik Analiz Sistemi

<div align="center">

![SecurityVision](https://img.shields.io/badge/SecurityVision-AI%20Güvenlik-blue?style=for-the-badge&logo=shield&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0.0-green?style=for-the-badge&logo=flask&logoColor=white)
![AI](https://img.shields.io/badge/AI-DeepFace%20%2B%20Norfair-red?style=for-the-badge&logo=tensorflow&logoColor=white)
![LLM](https://img.shields.io/badge/LLM-Ollama%20Llama3.2-orange?style=for-the-badge&logo=meta&logoColor=white)

**Gerçek zamanlı tehlike tespiti, LLM destekli raporlama ve kapsamlı web paneli ile gelişmiş yapay zeka güvenlik analiz sistemi.**

[🚀 Hızlı Başlangıç](#-hızlı-başlangıç) • [📖 Özellikler](#-özellikler) • [🎯 Kullanım](#-kullanım-örnekleri) • [🔧 API](#-api-referansı)

</div>

---

## 🎯 Genel Bakış

SecurityVision, son teknoloji bilgisayar görme, makine öğrenmesi ve doğal dil işleme teknolojilerini birleştirerek kapsamlı video güvenlik çözümleri sunan kurumsal düzeyde, yapay zeka destekli bir güvenlik analiz platformudur. Sistem gerçek zamanlı tehlike tespiti, otomatik raporlama ve sezgisel web tabanlı yönetim sunar.

### 🌟 Ana Özellikler

- **🤖 Gelişmiş AI Pipeline**: DeepFace + Norfair + Özel Tehlike Tespit Algoritması
- **📱 Gerçek Zamanlı Analiz**: IP kameralar, telefon kameraları (IP Webcam/iVCam) ve video dosyaları
- **🧠 LLM Entegrasyonu**: Ollama destekli Türkçe güvenlik raporları (Llama 3.2:3B)
- **🌐 Modern Web Arayüzü**: Bootstrap 5 dark tema ile gerçek zamanlı güncellemeler
- **👑 Admin Paneli**: Kullanıcı yönetimi, analitik ve sistem izleme
- **📧 Email Sistemi**: Doğrulama kodları ve otomatik ZIP rapor teslimatı
- **⚡ Arka Plan İşleme**: İlerleme takibi ile çok threaded analiz

---

## 🚀 Özellikler

### 🎥 Video Analiz Motoru
- **Çoklu Format Desteği**: MP4, AVI, MOV, MKV, WMV, FLV, WEBM (500MB'a kadar)
- **Yüz Tespiti & Takibi**: RetinaFace + Norfair nesne takibi
- **Duygu Analizi**: Gerçek zamanlı duygu tanıma (korku, öfke, üzüntü, vb.)
- **Hareket Tespiti**: Hız hesaplama ve yörünge analizi
- **Yakınlık İzleme**: Kişiler arası mesafe ölçümü

### 🚨 Akıllı Tehlike Tespiti
- **Tehlike Seviyesi Skorlama**: 0-10 ölçeğinde tehdit değerlendirme algoritması
- **Çok Faktörlü Analiz**: Duygu + Hız + Yakınlık + Kritik kombinasyonlar
- **Otomatik Alarmlar**: Eşik tabanlı uyarı sistemi (seviye ≥ 7)
- **Gerçek Zamanlı Uyarılar**: Anlık tehlike bildirimleri

### 🧠 LLM Raporlama Sistemi
- **Ollama Entegrasyonu**: Llama 3.2:3B model ile Türkçe rapor üretimi
- **Kritik Alarm Analizi**: Seviye 7+ alarmların detaylı analizi
- **Otomatik Özetleme**: Kısa ve net güvenlik özetleri
- **Email Teslimatı**: ZIP formatında kapsamlı rapor gönderimi

### 🌐 Web Arayüzü
- **Modern Dashboard**: Bootstrap 5 ile responsive dark tema
- **Gerçek Zamanlı Güncellemeler**: AJAX polling ile canlı durum takibi
- **Drag & Drop Upload**: Sezgisel dosya yükleme arayüzü
- **İlerleme İzleme**: Detaylı analiz ilerlemesi ve durum bilgileri

### 👑 Admin & Kullanıcı Yönetimi
- **Email Doğrulama**: 6 haneli kod ile güvenli giriş sistemi
- **Admin Paneli**: Kullanıcı listesi, doğrulama kodları, istatistikler
- **Oturum Yönetimi**: Flask session tabanlı güvenli authentication
- **CSV Export**: Kullanıcı verilerini dışa aktarma

### 📱 Telefon Kamerası Desteği
- **IP Webcam (Android)**: `http://ip:8080/video` stream desteği
- **iVCam (iOS)**: iPhone kamerası entegrasyonu
- **Bağlantı Testi**: Otomatik IP/port kontrolü
- **Gerçek Zamanlı Stream**: Canlı kamera analizi

---

## 🛠️ Teknoloji Stack'i

### 🧠 AI/ML Kütüphaneleri
```
deepface==0.0.79          # Yüz tespiti ve duygu analizi
tensorflow==2.13.0        # Derin öğrenme framework
norfair==2.2.0            # Nesne takibi ve tracking
opencv-python==4.8.1.78   # Bilgisayar görme
numpy==1.24.3             # Bilimsel hesaplama
scikit-learn==1.3.0       # Makine öğrenmesi
```

### 🌐 Backend & Web
```
flask==3.0.0              # Web framework
werkzeug==3.0.1           # WSGI utilities
```

### 📊 Veri İşleme & Görselleştirme
```
pandas==2.0.3             # Veri manipülasyonu
matplotlib==3.7.2         # Grafik ve görselleştirme
Pillow==10.0.1            # Görüntü işleme
```

### 🤖 LLM Entegrasyonu
- **Ollama**: Yerel LLM sunucu (llama3.2:3b)
- **Custom Utils**: Prompt engineering ve veri çıkarma

---

## 📁 Proje Yapısı

```
SecurityVision/
├── 📄 app.py                    # Flask ana sunucu
├── 🧠 process.py                # Video analizi ve tehlike tespiti
├── 🤖 llm.py                    # Ollama LLM entegrasyonu
├── 🔧 utils.py                  # Veri çıkarma ve prompt üretimi
├── 📋 requirements.txt          # Python bağımlılıkları
├── ⚙️ .env                      # Konfigürasyon dosyası
├── 📂 uploads/                  # Yüklenen video dosyaları
├── 📂 outputs/                  # Analiz sonuçları
│   └── 📁 {task_id}/
│       ├── 🎥 analyzed_video.mp4
│       └── 💾 alarm_analysis.db
├── 📂 templates/                # HTML şablonları
│   ├── 🏠 index.html           # Giriş sayfası
│   ├── 📊 dashboard.html       # Ana kontrol paneli
│   ├── 👑 kayitlar.html        # Admin paneli
│   └── ✅ verify.html          # Email doğrulama
├── 📂 static/                   # CSS, JS ve statik dosyalar
│   ├── 🎨 style.css
│   ├── ⚡ scripts.js
│   ├── 👑 kayitlar.js
│   ├── 🔐 login.js
│   ├── ✅ verify.js
│   └── 🎬 video/
└── 📂 database/
    └── 🗃️ securityvision_users.db
```

---

## 🚀 Hızlı Başlangıç

### 1️⃣ Sistem Gereksinimleri

- **Python**: 3.8 veya üzeri
- **RAM**: En az 8GB (AI modelleri için)
- **Disk**: 5GB boş alan
- **GPU**: İsteğe bağlı (CUDA destekli)

### 2️⃣ Kurulum

```bash
# Repo'yu klonlayın
git clone https://github.com/username/SecurityVision.git
cd SecurityVision

# Virtual environment oluşturun
python -m venv .venv

# Virtual environment'ı aktifleştirin
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Bağımlılıkları yükleyin
pip install -r requirements.txt
```

### 3️⃣ LLM Kurulumu (Ollama)

```bash
# Ollama'yı indirin ve kurun
# https://ollama.ai/download

# Ollama servisini başlatın
ollama serve

# Llama 3.2:3B modelini indirin
ollama pull llama3.2:3b
```

### 4️⃣ Konfigürasyon

`.env` dosyası oluşturun:

```env
# Flask Konfigürasyonu
SECRET_KEY=your-super-secret-key-here

# SMTP Email Ayarları (Gmail örneği)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

# Admin Kullanıcıları (virgül ile ayrılmış)
ADMIN_EMAILS=admin1@gmail.com,admin2@gmail.com
```

> **Not**: Gmail için App Password oluşturmanız gerekir (2FA etkin olmalı)

### 5️⃣ Uygulamayı Başlatın

```bash
python app.py
```

🌐 **Tarayıcıda açın**: http://localhost:5000

---

## 🎯 Kullanım Örnekleri

### 📹 Video Dosyası Analizi

1. **Giriş Yapın**: Email adresinizi girin → 6 haneli doğrulama kodunu email'den alın
2. **Video Yükleyin**: Drag & drop veya dosya seçici ile video yükleyin
3. **Analizi Başlatın**: "Analizi Başlat" butonuna basın
4. **Sonuçları İzleyin**: Gerçek zamanlı ilerleme ve alarm bilgileri
5. **Rapor İndirin**: Analiz tamamlandığında video, database ve LLM raporu indirin

### 📱 Telefon Kamerası (Real-time)

#### Android (IP Webcam):
```bash
1. Google Play'den "IP Webcam" uygulamasını indirin
2. Uygulamayı açın → "Start server" basın  
3. Gösterilen IP adresini not edin (örn: 192.168.1.105)
4. SecurityVision'da IP'yi girin → "Bağlantı Test Et"
5. Başarılı olursa "📱 Telefon Analizi Başlat"
```

#### iOS (iVCam):
```bash
1. App Store'dan "iVCam" uygulamasını indirin
2. PC'de iVCam Client kurduğunuzdan emin olun
3. Aynı WiFi ağında olduğunuzu kontrol edin
4. iOS uygulamasındaki IP'yi SecurityVision'da kullanın
```

### 🤖 LLM Rapor Üretimi

```bash
1. Video analizi tamamlandıktan sonra "LLM Rapor" butonuna basın
2. Sistem kritik alarmları (seviye 7+) otomatik analiz eder
3. Ollama ile Türkçe özet rapor üretilir (1-2 dakika)
4. Rapor otomatik olarak .txt dosyası şeklinde indirilir
5. "📧 Email ile Gönder" ile ZIP paketi email'e gönderilir
```

### 👑 Admin Paneli

Admin kullanıcıları için özel özellikler:

- **Kullanıcı Yönetimi**: Tüm kayıtlı kullanıcıları görüntüleme
- **Doğrulama Kodları**: Son gönderilen kodları izleme
- **Sistem İstatistikleri**: Günlük aktivite ve kullanım metrikleri
- **Temizlik İşlemleri**: Eski kodları silme
- **CSV Export**: Kullanıcı verilerini dışa aktarma

---

## 🔧 API Referansı

### 🔐 Authentication Endpoints

#### Doğrulama Kodu Gönderme
```http
POST /send_verification
Content-Type: application/json

{
    "email": "user@example.com"
}

Response:
{
    "success": true,
    "message": "Doğrulama kodu email adresinize gönderildi!"
}
```

#### Giriş Yapma
```http
POST /verify_and_login
Content-Type: application/json

{
    "code": "123456"
}

Response:
{
    "success": true,
    "message": "Başarıyla giriş yaptınız!",
    "redirect": "/dashboard"
}
```

### 🎥 Video Analysis Endpoints

#### Video Yükleme
```http
POST /upload
Content-Type: multipart/form-data

Files: video (max 500MB)

Response:
{
    "success": true,
    "task_id": "task_1703123456",
    "filename": "20231221_143000_video.mp4"
}
```

#### Analiz Durumu Sorgulama
```http
GET /status/{task_id}

Response:
{
    "success": true,
    "data": {
        "status": "processing|completed|failed",
        "progress": 75.5,
        "message": "Analyzing frame 377/500",
        "result": {
            "total_frames": 500,
            "processed_frames": 377,
            "total_alarms": 3,
            "max_danger_level": 8
        },
        "download_links": {
            "video": "/download/video/task_123",
            "database": "/download/database/task_123"
        }
    }
}
```

#### Telefon Kamerası Analizi
```http
POST /start_phone_analysis
Content-Type: application/json

{
    "phone_ip": "192.168.1.105",
    "duration": 60
}

Response:
{
    "success": true,
    "task_id": "phone_task_123",
    "message": "Telefon kamerası analizi başlatıldı (60 saniye)"
}
```

### 🤖 LLM Reporting Endpoints

#### Kritik Rapor Üretme
```http
POST /generate_report
Content-Type: application/json

{
    "db_file": "task_123/alarm_analysis.db"
}

Response:
{
    "success": true,
    "report": "GÜVENLIK ANALİZ RAPORU\n\nÖZET:\nAnaliz süresince 3 kritik alarm tespit edildi...",
    "stats": {
        "total_critical": 3,
        "total_alarms": 5,
        "max_danger_level": 8
    }
}
```

#### Email ile ZIP Rapor Gönderme
```http
POST /generate_and_email_report
Content-Type: application/json

{
    "task_id": "task_123"
}

Response:
{
    "success": true,
    "message": "Analiz raporu email adresinize gönderildi",
    "stats": {...}
}
```

### 👑 Admin Endpoints

#### Kullanıcı Verilerini Getirme
```http
GET /admin/users_data
Authorization: Admin Required

Response:
{
    "users": [...],
    "codes": [...],
    "stats": {
        "total_users": 25,
        "verified_users": 23,
        "today_codes": 8,
        "today_logins": 12
    }
}
```

---

## 🧠 Tehlike Tespit Algoritması

### 📊 Skorlama Sistemi (0-10)

SecurityVision'ın tehlike tespit algoritması çok faktörlü bir yaklaşım kullanır:

```python
def calculate_danger_level(emotion, speed, bbox_area):
    level = 0
    reasons = []
    
    # 1. Duygu Faktörü (0-4 puan)
    if emotion == 'fear':      level += 4  # Korku
    elif emotion == 'angry':   level += 3  # Öfke  
    elif emotion == 'sad':     level += 2  # Üzüntü
    
    # 2. Hız Faktörü (0-3 puan)
    if speed > 100:    level += 3    # Çok hızlı hareket
    elif speed > 60:   level += 2    # Hızlı hareket
    elif speed > 30:   level += 1    # Orta hız
    
    # 3. Yakınlık Faktörü (0-2 puan)
    if bbox_area > 8000:   level += 2    # Çok yakın
    elif bbox_area > 5000: level += 1    # Yakın
    
    # 4. Kritik Kombinasyon Bonusu (+1 puan)
    if emotion == 'fear' and speed > 60:
        level += 1  # Korku + Hızlı hareket = Kritik!
    
    return min(level, 10)  # Maksimum 10
```

### 🚨 Alarm Eşikleri

| Seviye | Durum | Açıklama |
|--------|-------|----------|
| 0-2 | 🟢 Güvenli | Normal davranış |
| 3-4 | 🟡 Dikkat | Hafif anormallik |
| 5-6 | 🟠 Risk | Potansiyel tehlike |
| 7-8 | 🔴 Tehlikeli | **Alarm tetiklenir** |
| 9-10 | ⚠️ Kritik | **Acil müdahale** |

### 🎯 Gerçek Zamanlı İşleme

```python
# Her 5. frame işlenir (performans optimizasyonu)
if frame_number % 5 == 0:
    # 1. Yüz tespiti (RetinaFace)
    analysis = DeepFace.analyze(frame, actions=['gender', 'emotion'])
    
    # 2. Nesne takibi (Norfair)
    tracked_objects = tracker.update(detections)
    
    # 3. Hareket analizi
    speed = calculate_normalized_speed(dx, dy, bbox_area, dt)
    
    # 4. Tehlike değerlendirmesi
    is_dangerous, level, reason = calculate_danger_level(emotion, speed, bbox_area)
    
    # 5. Kritik alarm kaydı (level >= 7)
    if is_dangerous and level >= 7:
        save_alarm_event(conn, timestamp, person_id, emotion, speed, level)
```

---

## 💾 Veritabanı Şeması

### 🗃️ Ana Tablolar

#### `alarm_events` - Kritik Alarm Kayıtları
```sql
CREATE TABLE alarm_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL,                    -- Unix timestamp
    formatted_time TEXT,               -- "14:23:45" format
    dangerous_person_id INTEGER,       -- Tracking ID
    dangerous_person_emotion TEXT,     -- "fear", "angry", etc.
    dangerous_person_speed REAL,       -- Normalized speed
    nearby_persons TEXT,               -- JSON array
    alarm_reason TEXT,                 -- "Fear detected | High speed"
    danger_level INTEGER,              -- 0-10 skala
    analysis_date TEXT                 -- ISO datetime
);
```

#### `person_details` - Detaylı Kişi Analizi
```sql
CREATE TABLE person_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL,
    face_id INTEGER,                   -- Norfair tracking ID
    gender TEXT,                       -- "male", "female"
    emotion TEXT,                      -- Dominant emotion
    speed REAL,                        -- Pixel/second normalized
    angle REAL,                        -- Movement direction
    bbox_area INTEGER,                 -- Face bounding box area
    distance_category TEXT,            -- "Very Close", "Close", etc.
    x, y, width, height INTEGER,       -- Bounding box coordinates
    danger_status TEXT,                -- "normal", "dangerous", "at_risk"
    danger_level INTEGER,              -- 0-10 threat level
    alarm_triggered INTEGER            -- 1 if alarm, 0 if normal
);
```

#### `users` - Kullanıcı Yönetimi
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    is_verified INTEGER DEFAULT 0,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 📧 Email & ZIP Rapor Sistemi

### 📦 ZIP İçeriği

Analiz tamamlandığında email ile gönderilen ZIP paketi:

```
security_report_12345678_20231221_143000.zip
├── 📹 analyzed_video_12345678.mp4      # İşlenmiş video (alarmlar işaretli)
├── 💾 analysis_database_12345678.db    # SQLite veritabanı (tüm veriler)
├── 🤖 llm_security_report_12345678.txt # LLM güvenlik raporu
├── 📊 technical_data_12345678.txt      # Teknik analiz verileri
└── 📄 README.txt                       # Kullanım rehberi
```

### 🤖 LLM Rapor Örneği

```
🔴 SECURITYVISION KRİTİK GÜVENLİK RAPORU
==========================================
Oluşturma Tarihi: 21.12.2023 14:30:25
Analiz ID: 12345678
Rapor Türü: Kritik Alarmlar (Tehlike Seviyesi 7+)

📊 ÖZET İSTATİSTİKLER:
- Toplam Alarm: 12
- Kritik Alarm (7+): 3
- En Yüksek Tehlike: 9/10

📝 DETAYLI KRİTİK ALARM ANALİZİ:

ÖZET:
Video analizi süresince 3 kritik güvenlik alarmı tespit edilmiştir. 
En yüksek tehlike seviyesi 9/10 olarak kaydedilmiştir.

EN TEHLİKELİ DURUM:
02:34:15 zamanında kişi ID:7'de korku duygusu ve hızlı hareket 
kombinasyonu tespit edildi. Yakınında 2 kişi bulunmaktaydı.

ÖNERİLER:
1. 02:34-02:36 zaman aralığında detaylı inceleme yapılmalı
2. Kritik alarmların yaşandığı bölgelerde güvenlik arttırılmalı  
3. Benzer durum tespitinde anında müdahale protokolü uygulanmalı

==========================================
⚠️  Bu rapor SecurityVision tarafından Ollama LLM ile 
    otomatik oluşturulmuştur (Model: llama3.2:3b)
==========================================
```

---

## 🔧 Gelişmiş Konfigürasyon

### ⚡ Performans Optimizasyonu

```python
# process.py'de performans ayarları
FRAME_SKIP = 5              # Her 5. frame işle
MAX_SPEED_HISTORY = 5       # Son 5 hız değerini tut
PROXIMITY_THRESHOLD = 200   # Yakınlık eşiği (pixel)
DANGER_THRESHOLD = 7        # Alarm eşiği

# Ollama LLM ayarları
LLM_TIMEOUT = 600          # 10 dakika timeout
LLM_MAX_TOKENS = 800       # Maksimum token sayısı
LLM_TEMPERATURE = 0.6      # Yaratıcılık seviyesi
```

### 🔒 Güvenlik Ayarları

```env
# Flask güvenlik
SECRET_KEY=super-complex-secret-key-min-32-chars
SESSION_COOKIE_SECURE=True  # HTTPS için
SESSION_COOKIE_HTTPONLY=True

# Rate limiting (gelecek sürüm)
RATE_LIMIT_VERIFICATION=5   # 5 kod/saat
RATE_LIMIT_LOGIN=10         # 10 deneme/saat

# File upload güvenlik
MAX_FILE_SIZE=500MB
ALLOWED_EXTENSIONS=mp4,avi,mov,mkv,wmv,flv,webm
QUARANTINE_SUSPICIOUS=True
```

### 📊 Monitoring & Logging

```python
# Sistem logları
logs/
├── app.log                # Flask uygulama logları
├── analysis.log           # Video analiz logları  
├── llm.log                # LLM rapor logları
└── security.log           # Güvenlik olayları

# Log seviyeleri
DEBUG    # Geliştirme detayları
INFO     # Normal işlemler  
WARNING  # Uyarılar
ERROR    # Hatalar
CRITICAL # Kritik hatalar
```

---

## 🚨 Sorun Giderme

### ❌ Sık Karşılaşılan Hatalar

#### "Ollama servisi erişilebilir değil"
```bash
# Çözüm:
ollama serve                    # Terminal'de Ollama'yı başlatın
ollama run llama3.2:3b         # Modeli yükleyin
```

#### "Model bulunamadı"
```bash
# Çözüm:
ollama pull llama3.2:3b        # Modeli indirin
ollama list                    # Mevcut modelleri kontrol edin
```

#### "Email gönderim hatası"
```bash
# Gmail için:
1. Google hesabınızda 2FA'yı aktifleştirin
2. App Password oluşturun (16 karakterlik)
3. .env dosyasında EMAIL_PASSWORD'ü güncelleyin
```

#### "Video yükleme başarısız"
```bash
# Kontrol edilecekler:
1. Dosya boyutu: Max 500MB
2. Format: MP4, AVI, MOV, MKV, WMV, FLV, WEBM
3. Disk alanı: En az 2GB boş alan
```

#### "Telefon kamerasına bağlanılamıyor"
```bash
# Android (IP Webcam):
1. Aynı WiFi ağında olduğunuzdan emin olun
2. IP Webcam'de "Start Server" basılı olmalı
3. Güvenlik duvarı 8080 portunu açmalı

# iOS (iVCam):
1. PC'de iVCam Client kurulu olmalı
2. iPhone ve PC aynı ağda olmalı
3. iVCam uygulaması çalışır durumda olmalı
```

### 🐛 Debug Modu

```bash
# Geliştirme modunda çalıştırma
export FLASK_ENV=development
export FLASK_DEBUG=1
python app.py

# Detaylı log çıktısı
tail -f logs/app.log
```


## 🙏 Teşekkürler




</div>
