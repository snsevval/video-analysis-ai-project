from flask import Flask, request, jsonify, render_template, send_file, url_for, session, redirect
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
import threading
import requests
import json
import sqlite3
import hashlib
import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import timedelta  # Bu zaten var mı kontrol et
from process import analyze_video  
import io
import zipfile
import tempfile
from email.mime.application import MIMEApplication
import os
from dotenv import load_dotenv


app = Flask(__name__)
load_dotenv()  # .env dosyasını yükle

app.secret_key = os.getenv('SECRET_KEY')

# gizle
SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = int(os.getenv('SMTP_PORT'))
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm'}

# Klasörleri oluştur
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs('static', exist_ok=True)
os.makedirs('templates', exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

# Global dictionary to track processing status
processing_status = {}
# ============= DATABASE INITIALIZATION =============
def init_db():
    """Veritabanını başlat - Users ve Verification codes"""
    conn = sqlite3.connect('securityvision_users.db')
    cursor = conn.cursor()
    
    # Users tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            is_verified INTEGER DEFAULT 0,
            last_login TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Verification codes tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS verification_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            code TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            used INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized")
    
# ============= EMAIL VERIFICATION FUNCTIONS =============
def generate_verification_code():
    """6 haneli doğrulama kodu oluştur"""
    return ''.join(random.choices(string.digits, k=6))

def send_verification_email(email, code):
    """Doğrulama kodunu email ile gönder"""
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = email
        msg['Subject'] = 'SecurityVision - Email Doğrulama Kodu'
        
        body = f"""
Merhaba,

SecurityVision sistemine giriş yapmak için aşağıdaki doğrulama kodunu kullanın:

🔐 Doğrulama Kodu: {code}

Bu kod 10 dakika geçerlidir.

Eğer bu işlemi siz yapmadıysanız, bu emaili görmezden gelebilirsiniz.

SecurityVision Güvenlik Sistemi
        """
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"📧 Verification email sent to: {email}")
        return True
    except Exception as e:
        print(f"❌ Email sending error: {e}")
        return False

def save_verification_code(email, code):
    """Doğrulama kodunu veritabanına kaydet"""
    conn = sqlite3.connect('securityvision_users.db')
    cursor = conn.cursor()
   
    cursor.execute('DELETE FROM verification_codes WHERE email = ?', (email,))
    
    # Yeni kod ekle (10 dakika geçerli)
    expires_at = datetime.now() + timedelta(minutes=10)
    cursor.execute('''
        INSERT INTO verification_codes (email, code, expires_at)
        VALUES (?, ?, ?)
    ''', (email, code, expires_at))
    
    conn.commit()
    conn.close()

def verify_code(email, code):
    """Doğrulama kodunu kontrol et"""
    conn = sqlite3.connect('securityvision_users.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM verification_codes 
        WHERE email = ? AND code = ? AND used = 0 AND expires_at > ?
    ''', (email, code, datetime.now()))
    
    result = cursor.fetchone()
    
    if result:
        # Kodu kullanıldı olarak işaretle
        cursor.execute('''
            UPDATE verification_codes 
            SET used = 1 
            WHERE email = ? AND code = ?
        ''', (email, code))
        conn.commit()
        conn.close()
        return True
    
    conn.close()
    return False

def create_or_update_user(email):
    """Kullanıcıyı oluştur veya güncelle"""
    conn = sqlite3.connect('securityvision_users.db')
    cursor = conn.cursor()
    
    # Kullanıcı var mı kontrol et
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    
    if user:
        # Mevcut kullanıcıyı doğrulanmış olarak işaretle
        cursor.execute('''
            UPDATE users 
            SET is_verified = 1, last_login = ? 
            WHERE email = ?
        ''', (datetime.now(), email))
    else:
        # Yeni kullanıcı oluştur
        cursor.execute('''
            INSERT INTO users (email, is_verified, last_login)
            VALUES (?, 1, ?)
        ''', (email, datetime.now()))
    
    conn.commit()
    conn.close()  

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def progress_callback(task_id, progress):
    """Progress callback function"""
    processing_status[task_id]['progress'] = progress
    print(f"Task {task_id}: {progress:.1f}% completed")

def analyze_video_background(task_id, video_path, output_dir):
    """Background video analysis task"""
    try:
        processing_status[task_id]['status'] = 'processing'
        processing_status[task_id]['message'] = 'Video analysis started...'
        
        # Progress callback wrapper
        def progress_wrapper(progress):
            progress_callback(task_id, progress)
        
        # Analyze video
        result = analyze_video(video_path, output_dir, progress_wrapper)
        
        # Update status
        if result['success']:
            processing_status[task_id]['status'] = 'completed'
            processing_status[task_id]['result'] = result
            processing_status[task_id]['message'] = 'Video analysis completed successfully!'
        else:
            processing_status[task_id]['status'] = 'failed'
            processing_status[task_id]['error'] = result['message']
            processing_status[task_id]['message'] = f'Analysis failed: {result["message"]}'
            
    except Exception as e:
        processing_status[task_id]['status'] = 'failed'
        processing_status[task_id]['error'] = str(e)
        processing_status[task_id]['message'] = f'Error during analysis: {str(e)}'
        print(f"Background analysis error: {e}")

# ============= LOGIN SYSTEM ROUTES =============
@app.route('/')
def index():
    """Login page"""
    return render_template('index.html')

@app.route('/send_verification', methods=['POST'])
def send_verification():
    """Email doğrulama kodu gönder - YENİ ROUTE"""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email or '@' not in email or '.' not in email:
            return jsonify({
                'success': False,
                'message': 'Geçerli bir email adresi girin!'
            }), 400
        
        # Doğrulama kodu oluştur
        code = generate_verification_code()
        save_verification_code(email, code)
        
        # Email gönder
        if send_verification_email(email, code):
            session['temp_email'] = email
            return jsonify({
                'success': True,
                'message': 'Doğrulama kodu email adresinize gönderildi!'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Email gönderilirken hata oluştu. Lütfen tekrar deneyin.'
            }), 500
            
    except Exception as e:
        print(f"Send verification error: {e}")
        return jsonify({
            'success': False,
            'message': 'Beklenmeyen hata oluştu.'
        }), 500

@app.route('/verify_and_login', methods=['POST'])
def verify_and_login():
    """Doğrulama kodunu kontrol et ve giriş yap - YENİ ROUTE"""
    try:
        data = request.get_json()
        code = data.get('code')
        email = session.get('temp_email')
        
        if not email:
            return jsonify({
                'success': False,
                'message': 'Session süresi doldu. Lütfen tekrar deneyin.'
            }), 400
        
        if not code:
            return jsonify({
                'success': False,
                'message': 'Doğrulama kodunu girin!'
            }), 400
        
        # Kodu doğrula
        if verify_code(email, code):
            # Kullanıcıyı oluştur/güncelle
            create_or_update_user(email)
            
            # Session'a kaydet
            session['user_email'] = email
            session['login_time'] = datetime.now().isoformat()
            session.pop('temp_email', None)
            
            print(f"✅ User verified and logged in: {email}")
            
            return jsonify({
                'success': True,
                'message': 'Doğrulama başarılı! Yönlendiriliyorsunuz...',
                'redirect': url_for('dashboard')
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Geçersiz veya süresi dolmuş kod!'
            }), 400
            
    except Exception as e:
        print(f"Verify and login error: {e}")
        return jsonify({
            'success': False,
            'message': 'Beklenmeyen hata oluştu.'
        }), 500

@app.route('/resend_code', methods=['POST'])
def resend_code():
    """Doğrulama kodunu yeniden gönder"""
    try:
        email = session.get('temp_email')
        
        if not email:
            return jsonify({
                'success': False,
                'message': 'Session süresi doldu. Lütfen tekrar deneyin.'
            }), 400
        
        # Yeni kod oluştur
        code = generate_verification_code()
        save_verification_code(email, code)
        
        # Email gönder
        if send_verification_email(email, code):
            return jsonify({
                'success': True,
                'message': 'Yeni doğrulama kodu gönderildi!'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Email gönderilirken hata oluştu.'
            }), 500
            
    except Exception as e:
        print(f"Resend code error: {e}")
        return jsonify({
            'success': False,
            'message': 'Beklenmeyen hata oluştu.'
        }), 500
@app.route('/logout')
def logout():
    """Handle logout"""
    email = session.get('user_email', 'Unknown')
    session.clear()
    print(f"👋 User logged out: {email}")
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    """Main SecurityVision page - requires login"""
    if 'user_email' not in session:
        print("❌ Unauthorized access attempt to dashboard")
        return redirect(url_for('index'))
    
    user_email = session.get('user_email')
    print(f"✅ Dashboard access: {user_email}")
    return render_template('dashboard.html')

# ============= VIDEO ANALYSIS ROUTES =============
@app.route('/upload', methods=['POST'])
def upload_video():
    """Handle video upload and start analysis"""
    # Session kontrolü
    if 'user_email' not in session:
        return jsonify({
            'success': False,
            'message': 'Login required'
        }), 401
    
    try:
        # Check if file is present
        if 'video' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No video file provided'
            }), 400

        file = request.files['video']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'No video file selected'
            }), 400

        # Check file extension
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'message': f'Invalid file type. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400

        # Generate unique task ID and filename
        task_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = secure_filename(file.filename)
        filename = f"{timestamp}_{filename}"
        
        # Save uploaded file
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Create output directory for this task
        output_dir = os.path.join(app.config['OUTPUT_FOLDER'], task_id)
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize processing status
        processing_status[task_id] = {
            'status': 'uploaded',
            'progress': 0,
            'message': 'Video uploaded successfully, starting analysis...',
            'filename': filename,
            'task_id': task_id,
            'user_email': session.get('user_email'),  # Kullanıcı bilgisi ekle
            'start_time': datetime.now().isoformat()
        }
        
        # Start background analysis
        thread = threading.Thread(
            target=analyze_video_background,
            args=(task_id, file_path, output_dir)
        )
        thread.daemon = True
        thread.start()
        
        print(f"📤 Video uploaded by {session.get('user_email')}: {filename}")
        
        return jsonify({
            'success': True,
            'message': 'Video uploaded and analysis started',
            'task_id': task_id,
            'filename': filename
        })
        
    except Exception as e:
        print(f"Upload error: {e}")
        return jsonify({
            'success': False,
            'message': f'Upload failed: {str(e)}'
        }), 500

@app.route('/status/<task_id>')
def get_status(task_id):
    """Get analysis status"""
    # Session kontrolü
    if 'user_email' not in session:
        return jsonify({
            'success': False,
            'message': 'Login required'
        }), 401
    
    if task_id not in processing_status:
        return jsonify({
            'success': False,
            'message': 'Task not found'
        }), 404
    
    status = processing_status[task_id]
    
    # Add download links if completed
    if status['status'] == 'completed' and 'result' in status:
        result = status['result']
        status['download_links'] = {
            'video': url_for('download_video', task_id=task_id),
            'database': url_for('download_database', task_id=task_id)
        }
    
    return jsonify({
        'success': True,
        'data': status
    })

@app.route('/download/video/<task_id>')
def download_video(task_id):
    """Download analyzed video"""
    # Session kontrolü
    if 'user_email' not in session:
        return jsonify({'error': 'Login required'}), 401
    
    if task_id not in processing_status:
        return jsonify({'error': 'Task not found'}), 404
    
    status = processing_status[task_id]
    if status['status'] != 'completed':
        return jsonify({'error': 'Analysis not completed'}), 400
    
    try:
        video_path = status['result']['files']['analyzed_video']
        if os.path.exists(video_path):
            print(f"📥 Video download by {session.get('user_email')}: {task_id}")
            return send_file(video_path, as_attachment=True)
        else:
            return jsonify({'error': 'Video file not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/database/<task_id>')
def download_database(task_id):
    """Download analysis database"""
    # Session kontrolü
    if 'user_email' not in session:
        return jsonify({'error': 'Login required'}), 401
    
    if task_id not in processing_status:
        return jsonify({'error': 'Task not found'}), 404
    
    status = processing_status[task_id]
    if status['status'] != 'completed':
        return jsonify({'error': 'Analysis not completed'}), 400
    
    try:
        db_path = status['result']['files']['database']
        if os.path.exists(db_path):
            print(f"📥 Database download by {session.get('user_email')}: {task_id}")
            return send_file(db_path, as_attachment=True)
        else:
            return jsonify({'error': 'Database file not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/results/<task_id>')
def get_results(task_id):
    """Get detailed analysis results"""
    # Session kontrolü
    if 'user_email' not in session:
        return jsonify({
            'success': False,
            'message': 'Login required'
        }), 401
    
    if task_id not in processing_status:
        return jsonify({
            'success': False,
            'message': 'Task not found'
        }), 404
    
    status = processing_status[task_id]
    if status['status'] != 'completed':
        return jsonify({
            'success': False,
            'message': 'Analysis not completed yet'
        }), 400
    
    return jsonify({
        'success': True,
        'data': status['result']
    })

@app.route('/cleanup/<task_id>', methods=['DELETE'])
def cleanup_task(task_id):
    """Clean up task files and data"""
    # Session kontrolü
    if 'user_email' not in session:
        return jsonify({'error': 'Login required'}), 401
    
    try:
        if task_id in processing_status:
            # Delete uploaded video
            if 'filename' in processing_status[task_id]:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], processing_status[task_id]['filename'])
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            # Delete output directory
            output_dir = os.path.join(app.config['OUTPUT_FOLDER'], task_id)
            if os.path.exists(output_dir):
                import shutil
                shutil.rmtree(output_dir)
            
            # Remove from memory
            del processing_status[task_id]
            
            print(f"🗑️ Task cleaned up by {session.get('user_email')}: {task_id}")
            
            return jsonify({
                'success': True,
                'message': 'Task cleaned up successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Task not found'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Cleanup failed: {str(e)}'
        }), 500

# ============= LLM RAPOR SİSTEMİ =============
@app.route('/generate_report', methods=['POST'])
def generate_report():
    """ANA SAYFA için LLM raporu oluştur"""
    # Session kontrolü
    if 'user_email' not in session:
        return jsonify({'error': 'Login required'}), 401
    
    try:
        data = request.get_json()
        db_file = data.get('db_file')
        
        if not db_file:
            return jsonify({'error': 'Database file not specified'}), 400
        
        print(f"🤖 LLM Report request by {session.get('user_email')}: {db_file}")
        
        # Ana sayfa formatı: "task_id/analysis.db" veya "task_id/alarm_analysis.db"
        if '/' in db_file:
            # "e4e0cd34-f23b-4324-84b7-06ba2b7e343e/analysis.db" formatı
            db_path = os.path.join(OUTPUT_FOLDER, db_file)
        else:
            # Sadece task_id verilmiş, database dosyasını ara
            task_folder = os.path.join(OUTPUT_FOLDER, db_file)
            possible_files = ['analysis.db', 'alarm_analysis.db']
            db_path = None
            
            for filename in possible_files:
                test_path = os.path.join(task_folder, filename)
                if os.path.exists(test_path):
                    db_path = test_path
                    break
        
        print(f"Aranan path: {db_path}")
        
        if not db_path or not os.path.exists(db_path):
            return jsonify({'error': f'Database file not found: {db_path}'}), 404
        
        print(f"Database analizi başlıyor...")
        data_summary = analyze_database(db_path)
        print(f"Database analizi tamamlandı: {len(data_summary.get('detailed_alarms', []))} alarm")

        print(f"LLM raporu başlıyor...")
        report = generate_llm_report(data_summary)
        print(f"LLM raporu tamamlandı: {len(report)} karakter")
        
        # ZIP oluştur ve email gönder
        user_email = session.get('user_email')
        if user_email:
            create_and_send_results_zip(user_email, db_file.split('/')[0], report, {
                'total_alarms': data_summary['total_alarms'],
                'video_duration': data_summary['video_duration'], 
                'critical_moments': len(data_summary['critical_moments'])
            })
            print(f"📦 ZIP results sent to {user_email}")
        
        return jsonify({
            'success': True,
            'report': report,
            'db_file': db_file,
            'stats': {
                'total_alarms': data_summary['total_alarms'],
                'video_duration': data_summary['video_duration'],
                'critical_moments': len(data_summary['critical_moments'])
            }
        })
        
    except Exception as e:
        print(f"LLM Report Error: {e}")
        return jsonify({'error': str(e)}), 500

def analyze_database(db_path):
    """Database'i DETAYLI analiz et - kişi bazlı alarm verisi"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. GENEL İSTATİSTİKLER
        cursor.execute("SELECT COUNT(*) FROM video_analysis")
        total_frames = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM alarm_events")
        total_alarms = cursor.fetchone()[0]
        
        cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM video_analysis")
        time_range = cursor.fetchone()
        video_duration = time_range[1] - time_range[0] if time_range[0] and time_range[1] else 0
        
        # 2. DETAYLI ALARM ANALİZİ (zaman + kişi + sebep)
        cursor.execute("""
            SELECT 
                ae.timestamp,
                ae.formatted_time,
                ae.dangerous_person_id,
                ae.dangerous_person_emotion,
                ae.dangerous_person_speed,
                ae.alarm_reason,
                ae.danger_level,
                ae.nearby_persons
            FROM alarm_events ae
            ORDER BY ae.timestamp
        """)
        
        detailed_alarms = []
        for row in cursor.fetchall():
            nearby_list = eval(row[7]) if row[7] and row[7] != '[]' else []
            detailed_alarms.append({
                'time': row[1],  # formatted_time
                'timestamp': row[0],
                'person_id': row[2],
                'emotion': row[3],
                'speed': round(row[4], 1) if row[4] else 0,
                'reason': row[5],
                'danger_level': row[6],
                'nearby_count': len(nearby_list),
                'nearby_persons': nearby_list
            })
        
        # 3. KRİTİK ANLAR (Danger Level >= 7)
        cursor.execute("""
            SELECT 
                ae.formatted_time,
                ae.dangerous_person_emotion,
                ae.dangerous_person_speed,
                ae.danger_level,
                ae.alarm_reason,
                ae.nearby_persons
            FROM alarm_events ae
            WHERE ae.danger_level >= 7
            ORDER BY ae.danger_level DESC, ae.timestamp
        """)
        
        critical_moments = []
        for row in cursor.fetchall():
            nearby_list = eval(row[5]) if row[5] and row[5] != '[]' else []
            critical_moments.append({
                'time': row[0],
                'emotion': row[1],
                'speed': round(row[2], 1) if row[2] else 0,
                'danger_level': row[3],
                'reason': row[4],
                'nearby_count': len(nearby_list)
            })
        
        # 4. DUYGU BAZLI İSTATİSTİKLER
        cursor.execute("""
            SELECT 
                dangerous_person_emotion,
                COUNT(*) as count,
                AVG(danger_level) as avg_danger,
                MAX(danger_level) as max_danger
            FROM alarm_events
            GROUP BY dangerous_person_emotion
            ORDER BY count DESC
        """)
        
        emotion_stats = {}
        for row in cursor.fetchall():
            emotion_stats[row[0]] = {
                'count': row[1],
                'avg_danger': round(row[2], 1),
                'max_danger': row[3]
            }
        
        # 5. ZAMAN BAZLI PATTERN ANALİZİ
        cursor.execute("""
            SELECT 
                CAST(timestamp AS INTEGER) as second,
                COUNT(*) as alarm_count,
                MAX(danger_level) as max_danger
            FROM alarm_events
            GROUP BY CAST(timestamp AS INTEGER)
            HAVING alarm_count > 1
            ORDER BY alarm_count DESC
            LIMIT 5
        """)
        
        time_patterns = []
        for row in cursor.fetchall():
            time_patterns.append({
                'second': row[0],
                'time_formatted': f"{row[0]//60:02d}:{row[0]%60:02d}",
                'alarm_count': row[1],
                'max_danger': row[2]
            })
        
        return {
            'total_frames': total_frames,
            'total_alarms': total_alarms,
            'video_duration': video_duration,
            'detailed_alarms': detailed_alarms,
            'critical_moments': critical_moments,
            'emotion_stats': emotion_stats,
            'time_patterns': time_patterns
        }
        
    finally:
        conn.close()

def generate_llm_report(data_summary):
    """Kısa DURUM RAPORU - Alarm odaklı"""
    
    prompt = f"""
Video güvenlik durum raporu hazırla.

GENEL DURUM:
- Video süresi: {data_summary['video_duration']:.0f} saniye
- Toplam alarm: {data_summary['total_alarms']} adet
- Kritik durum: {len(data_summary['critical_moments'])} adet

ALARM DETAYLARI:
"""
    
    # Alarm detaylarını ekle
    for i, alarm in enumerate(data_summary['detailed_alarms'][:5], 1):
        prompt += f"""
{alarm['time']} - Kişi ID: {alarm['person_id']} | Duygu: {alarm['emotion']} | Hız: {alarm['speed']:.0f} | Tehlike: {alarm['danger_level']} | Yakında: {alarm['nearby_count']} kişi
"""

    prompt += f"""

KRITIK ANLAR:
"""
    
    for moment in data_summary['critical_moments'][:3]:
        prompt += f"{moment['time']} - {moment['emotion']} duygu, {moment['speed']:.0f} hız, seviye {moment['danger_level']}, {moment['nearby_count']} kişi yakında\n"

    prompt += f"""

RAPOR İSTEĞİ:
Zaman sırasına göre alarm durumlarını analiz et. Hangi zaman aralıklarında yoğunluk var? Tekrarlayan pattern var mı? Kısa ve net durum raporu ver.

Türkçe, 2-3 paragraf.
"""

    try:
        response = requests.post('http://localhost:11434/api/generate', 
                               json={
                                   'model': 'llama3.2:3b',
                                   'prompt': prompt,
                                   'stream': False
                               },
                               timeout=10000)
        
        if response.status_code == 200:
            result = response.json()
            return result['response']
        else:
            return f"LLM API Hatası: {response.status_code} - {response.text}"
            
    except requests.exceptions.RequestException as e:
        return f"🔌 Bağlantı Hatası: Ollama sunucusu çalışmıyor olabilir.\n\nHata: {str(e)}\n\nÇözüm:\n1. Yeni terminal açın\n2. 'ollama serve' komutunu çalıştırın\n3. Tekrar deneyin"
    except Exception as e:
        return f"Beklenmeyen Hata: {str(e)}"
 
def create_and_send_results_zip(user_email, task_id, report_content, stats):
    """3 dosyayı zipleyip email ile gönder"""
    try:
        # Dosya yolları
        output_dir = os.path.join(OUTPUT_FOLDER, task_id)
        video_file = None
        db_file = None
        
        # Video dosyasını bul
        for file in os.listdir(output_dir):
            if file.endswith('.mp4'):
                video_file = os.path.join(output_dir, file)
                break
        
        # Database dosyasını bul
        for file in os.listdir(output_dir):
            if file.endswith('.db'):
                db_file = os.path.join(output_dir, file)
                break
        
        if not video_file or not db_file:
            print(f"❌ Video veya DB dosyası bulunamadı: {output_dir}")
            return False
        
        # TXT raporu oluştur
        txt_content = f"""🤖 SECURITYVISION LLM GÜVENLİK RAPORU
=====================================
Oluşturma Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}
Analiz ID: {task_id}

📊 İSTATİSTİKLER:
- Toplam Alarm: {stats.get('total_alarms', 0)}
- Video Süresi: {stats.get('video_duration', 0):.0f} saniye
- Kritik Durum: {stats.get('critical_moments', 0)}

📝 DETAYLI ANALİZ:
{report_content}

=====================================
Bu rapor SecurityVision Video Güvenlik & Tehlike Tespit Sistemi 
tarafından yapay zeka ile otomatik olarak oluşturulmuştur.
"""
        
        # Geçici ZIP dosyası oluştur
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
            zip_path = temp_zip.name
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Video ekle
                zipf.write(video_file, f'SecurityVision_Video_{task_id[:8]}.mp4')
                
                # Database ekle
                zipf.write(db_file, f'SecurityVision_Database_{task_id[:8]}.db')
                
                # TXT raporu ekle
                zipf.writestr(f'SecurityVision_Rapor_{task_id[:8]}.txt', txt_content)
        
        # Email gönder
        if send_zip_email(user_email, zip_path, task_id, stats):
            os.unlink(zip_path)  # Geçici zip dosyasını sil
            return True
        else:
            os.unlink(zip_path)
            return False
            
    except Exception as e:
        print(f"❌ ZIP creation error: {e}")
        return False

def send_zip_email(user_email, zip_path, task_id, stats):
    """ZIP dosyasını email ile gönder"""
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = user_email
        msg['Subject'] = f'SecurityVision - Video Analiz Sonuçları ({task_id[:8]})'
        
        # Email body
        body = f"""
Merhaba,

SecurityVision video analiziniz başarıyla tamamlandı! 🎉

📊 ÖZET:
- Analiz ID: {task_id[:8]}...
- Toplam Alarm: {stats.get('total_alarms', 0)}
- Video Süresi: {stats.get('video_duration', 0):.0f} saniye
- Kritik Durum: {stats.get('critical_moments', 0)}

📎 EK DOSYALAR:
Ekli ZIP dosyasında 3 adet sonuç dosyası bulunmaktadır:
- Analiz edilmiş video (.mp4)
- Detaylı veri tabanı (.db) 
- LLM güvenlik raporu (.txt)

İyi günler!
SecurityVision Güvenlik Sistemi
        """
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # ZIP dosyasını ekle
        with open(zip_path, 'rb') as f:
            zip_data = f.read()
            
        zip_attachment = MIMEApplication(zip_data, _subtype='zip')
        zip_attachment.add_header('Content-Disposition', 'attachment', 
                                filename=f'SecurityVision_Results_{task_id[:8]}.zip')
        msg.attach(zip_attachment)
        
        # Email gönder
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"📧 ZIP report sent to: {user_email}")
        return True
        
    except Exception as e:
        print(f"❌ ZIP email error: {e}")
        return False
# ============= UTILITY ROUTES =============
@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'active_tasks': len(processing_status),
        'logged_in': 'user_email' in session
    })

@app.route('/user_info')
def user_info():
    """Get current user info"""
    if 'user_email' not in session:
        return jsonify({'logged_in': False})
    
    return jsonify({
        'logged_in': True,
        'email': session.get('user_email'),
        'login_time': session.get('login_time')
    })

# ============= ERROR HANDLERS =============
@app.errorhandler(413)
def too_large(e):
    return jsonify({
        'success': False,
        'message': 'File too large. Maximum size is 500MB.'
    }), 413

@app.errorhandler(500)
def internal_error(e):
    return jsonify({
        'success': False,
        'message': 'Internal server error'
    }), 500

@app.errorhandler(401)
def unauthorized(e):
    return jsonify({
        'success': False,
        'message': 'Login required'
    }), 401

if __name__ == '__main__':
    init_db()  # ← BU SATIRI EKLEYİN
    print("🚀 SecurityVision Server Starting...")
    print("📁 Upload folder:", UPLOAD_FOLDER)
    print("📁 Output folder:", OUTPUT_FOLDER)
    print("🎥 Allowed formats:", ", ".join(ALLOWED_EXTENSIONS))
    print("💾 Max file size: 500MB")
    print("🔐 Login system: ENABLED")
    print("🌐 Server running on: http://localhost:5000")
    print("📧 Login page: http://localhost:5000/")
    print("🎛️ Dashboard: http://localhost:5000/dashboard")
    
    app.run(debug=True, host='0.0.0.0', port=5000)