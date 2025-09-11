from flask import Flask, request, jsonify, render_template, send_file, url_for, session, redirect
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime, timedelta
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
from process import analyze_video  
import io
import zipfile
import tempfile
from email.mime.application import MIMEApplication
from dotenv import load_dotenv
from functools import wraps

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'securityvision-fallback-key')

# Email Configuration
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

# Admin Configuration
ADMIN_EMAILS_STR = os.getenv('ADMIN_EMAILS', EMAIL_ADDRESS or 'admin@securityvision.com')
ADMIN_EMAILS = [email.strip() for email in ADMIN_EMAILS_STR.split(',') if email.strip()]

# App Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm'}

# Create directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs('static', exist_ok=True)
os.makedirs('templates', exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB

# Global variables
processing_status = {}

# ============= HELPER FUNCTIONS =============
def is_admin(email):
    """Check if email is admin"""
    return email in ADMIN_EMAILS

def admin_required(f):
    """Decorator for admin-only routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            return jsonify({'error': 'Login required'}), 401
        
        user_email = session.get('user_email')
        if not is_admin(user_email):
            print(f"❌ Admin access denied: {user_email}")
            return jsonify({'error': 'Admin access required'}), 403
        
        print(f"✅ Admin access granted: {user_email}")
        return f(*args, **kwargs)
    
    return decorated_function

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_login_log(email, status, ip_address):
    """Save login log to database"""
    try:
        conn = sqlite3.connect('securityvision_users.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS login_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                status TEXT NOT NULL,
                ip_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            INSERT INTO login_logs (email, status, ip_address)
            VALUES (?, ?, ?)
        ''', (email, status, ip_address))
        
        conn.commit()
        conn.close()
        print(f"✅ Login log saved: {email} - {status}")
    except Exception as e:
        print(f"❌ Login log error: {e}")

# ============= DATABASE FUNCTIONS =============
def init_db():
    """Initialize database"""
    conn = sqlite3.connect('securityvision_users.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            is_verified INTEGER DEFAULT 0,
            last_login TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Verification codes table
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
    
    # Login logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS login_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            status TEXT NOT NULL,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized")

def generate_verification_code():
    """Generate 6-digit verification code"""
    return ''.join(random.choices(string.digits, k=6))

def send_verification_email(email, code):
    """Send verification code via email"""
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = email
        msg['Subject'] = 'SecurityVision - Email Verification Code'
        
        body = f"""
Hello,

Use the following verification code to login to SecurityVision:

🔐 Verification Code: {code}

This code is valid for 10 minutes.

If you didn't request this, please ignore this email.

SecurityVision Security System
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
    """Save verification code to database"""
    conn = sqlite3.connect('securityvision_users.db')
    cursor = conn.cursor()
    
    # Delete old codes for this email
    cursor.execute('DELETE FROM verification_codes WHERE email = ?', (email,))
    
    # Add new code (valid for 10 minutes)
    expires_at = datetime.now() + timedelta(minutes=10)
    cursor.execute('''
        INSERT INTO verification_codes (email, code, expires_at)
        VALUES (?, ?, ?)
    ''', (email, code, expires_at))
    
    conn.commit()
    conn.close()

def verify_code(email, code):
    """Verify the code"""
    conn = sqlite3.connect('securityvision_users.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM verification_codes 
        WHERE email = ? AND code = ? AND used = 0 AND expires_at > ?
    ''', (email, code, datetime.now()))
    
    result = cursor.fetchone()
    
    if result:
        # Mark code as used
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
    """Create or update user"""
    conn = sqlite3.connect('securityvision_users.db')
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    
    if user:
        # Update existing user
        cursor.execute('''
            UPDATE users 
            SET is_verified = 1, last_login = ? 
            WHERE email = ?
        ''', (datetime.now(), email))
    else:
        # Create new user
        cursor.execute('''
            INSERT INTO users (email, is_verified, last_login)
            VALUES (?, 1, ?)
        ''', (email, datetime.now()))
    
    conn.commit()
    conn.close()

def progress_callback(task_id, progress):
    """Progress callback function"""
    processing_status[task_id]['progress'] = progress
    print(f"Task {task_id}: {progress:.1f}% completed")

def analyze_video_background(task_id, video_path, output_dir):
    """Background video analysis task"""
    try:
        processing_status[task_id]['status'] = 'processing'
        processing_status[task_id]['message'] = 'Video analysis started...'
        
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

# ============= ROUTES =============

# Auth Routes
@app.route('/')
def index():
    """Login page"""
    return render_template('index.html')

@app.route('/send_verification', methods=['POST'])
def send_verification():
    """Send verification code"""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email or '@' not in email or '.' not in email:
            return jsonify({
                'success': False,
                'message': 'Please enter a valid email address!'
            }), 400
        
        # Generate and save code
        code = generate_verification_code()
        save_verification_code(email, code)
        
        # Send email
        if send_verification_email(email, code):
            session['temp_email'] = email
            return jsonify({
                'success': True,
                'message': 'Verification code sent to your email!'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to send email. Please try again.'
            }), 500
            
    except Exception as e:
        print(f"Send verification error: {e}")
        return jsonify({
            'success': False,
            'message': 'An unexpected error occurred.'
        }), 500

@app.route('/verify_and_login', methods=['POST'])
def verify_and_login():
    """Verify code and login"""
    try:
        data = request.get_json()
        code = data.get('code')
        email = session.get('temp_email')
        
        ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', '127.0.0.1'))
        
        if not email:
            save_login_log('Unknown', 'failed', ip_address)
            return jsonify({
                'success': False,
                'message': 'Session expired. Please try again.'
            }), 400
        
        if not code:
            save_login_log(email, 'failed', ip_address)
            return jsonify({
                'success': False,
                'message': 'Please enter the verification code!'
            }), 400
        
        # Verify code
        if verify_code(email, code):
            # Create/update user
            create_or_update_user(email)
            
            # Create session
            session['user_email'] = email
            session['login_time'] = datetime.now().isoformat()
            session.pop('temp_email', None)
            
            # Log success
            save_login_log(email, 'success', ip_address)
            
            print(f"✅ User verified and logged in: {email}")
            
            return jsonify({
                'success': True,
                'message': 'Login successful! Redirecting...',
                'redirect': url_for('dashboard')
            })
        else:
            # Log failure
            save_login_log(email, 'failed', ip_address)
            return jsonify({
                'success': False,
                'message': 'Invalid or expired code!'
            }), 400
            
    except Exception as e:
        print(f"Verify and login error: {e}")
        save_login_log(email if 'email' in locals() else 'Unknown', 'error', 
                      ip_address if 'ip_address' in locals() else '127.0.0.1')
        return jsonify({
            'success': False,
            'message': 'An unexpected error occurred.'
        }), 500

@app.route('/resend_code', methods=['POST'])
def resend_code():
    """Resend verification code"""
    try:
        email = session.get('temp_email')
        
        if not email:
            return jsonify({
                'success': False,
                'message': 'Session expired. Please try again.'
            }), 400
        
        # Generate new code
        code = generate_verification_code()
        save_verification_code(email, code)
        
        # Send email
        if send_verification_email(email, code):
            return jsonify({
                'success': True,
                'message': 'New verification code sent!'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to send email.'
            }), 500
            
    except Exception as e:
        print(f"Resend code error: {e}")
        return jsonify({
            'success': False,
            'message': 'An unexpected error occurred.'
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
    """Main dashboard - requires login"""
    if 'user_email' not in session:
        print("❌ Unauthorized access attempt to dashboard")
        return redirect(url_for('index'))
    
    user_email = session.get('user_email')
    print(f"✅ Dashboard access: {user_email}")
    return render_template('dashboard.html')

# Admin Routes
@app.route('/kayitlar')
@admin_required
def kayitlar():
    """Records page - admin only"""
    return render_template('kayitlar.html')

@app.route('/check_admin_status')
def check_admin_status():
    """Check if user is admin"""
    if 'user_email' not in session:
        return jsonify({
            'logged_in': False, 
            'is_admin': False
        })
    
    user_email = session.get('user_email')
    return jsonify({
        'logged_in': True,
        'email': user_email,
        'is_admin': is_admin(user_email),
        'admin_emails': ADMIN_EMAILS if is_admin(user_email) else []
    })

@app.route('/admin/users_data')
@admin_required
def admin_users_data():
    """Get user data for admin"""
    try:
        conn = sqlite3.connect('securityvision_users.db')
        cursor = conn.cursor()
        
        # Get users
        cursor.execute("""
            SELECT email, is_verified, last_login, created_at
            FROM users 
            ORDER BY created_at DESC
        """)
        users = cursor.fetchall()
        
        # Get verification codes
        cursor.execute("""
            SELECT email, code, expires_at, used, created_at
            FROM verification_codes 
            ORDER BY created_at DESC 
            LIMIT 50
        """)
        codes = cursor.fetchall()
        
        # Get statistics
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_verified = 1")
        verified_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM verification_codes WHERE created_at LIKE ?", 
                      (f'{datetime.now().strftime("%Y-%m-%d")}%',))
        today_codes = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE last_login LIKE ?", 
                      (f'{datetime.now().strftime("%Y-%m-%d")}%',))
        today_logins = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'users': [
                {
                    'email': user[0],
                    'verified': bool(user[1]),
                    'last_login': user[2],
                    'created_at': user[3],
                    'is_admin': is_admin(user[0])
                } for user in users
            ],
            'codes': [
                {
                    'email': code[0],
                    'code': code[1],
                    'expires_at': code[2],
                    'used': bool(code[3]),
                    'created_at': code[4]
                } for code in codes
            ],
            'stats': {
                'total_users': total_users,
                'verified_users': verified_users,
                'today_codes': today_codes,
                'today_logins': today_logins,
                'admin_count': len(ADMIN_EMAILS)
            },
            'current_admin': session.get('user_email'),
            'admin_emails': ADMIN_EMAILS
        })
        
    except Exception as e:
        print(f"❌ Admin users data error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/cleanup_old_codes', methods=['POST'])
@admin_required
def cleanup_old_codes():
    """Clean up old verification codes"""
    try:
        conn = sqlite3.connect('securityvision_users.db')
        cursor = conn.cursor()
        
        # Delete codes older than 24 hours
        yesterday = datetime.now() - timedelta(days=1)
        cursor.execute("DELETE FROM verification_codes WHERE created_at < ?", (yesterday,))
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        print(f"🧹 Admin cleanup: {deleted_count} old codes deleted by {session.get('user_email')}")
        
        return jsonify({
            'success': True,
            'message': f'{deleted_count} old codes cleaned up'
        })
        
    except Exception as e:
        print(f"❌ Cleanup error: {e}")
        return jsonify({'error': str(e)}), 500

# Video Analysis Routes
@app.route('/upload', methods=['POST'])
def upload_video():
    """Handle video upload and start analysis"""
    if 'user_email' not in session:
        return jsonify({
            'success': False,
            'message': 'Login required'
        }), 401
    
    try:
        if 'video' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No video file provided'
            }), 400

        file = request.files['video']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'No video file selected'
            }), 400

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
        
        # Create output directory
        output_dir = os.path.join(app.config['OUTPUT_FOLDER'], task_id)
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize processing status
        processing_status[task_id] = {
            'status': 'uploaded',
            'progress': 0,
            'message': 'Video uploaded successfully, starting analysis...',
            'filename': filename,
            'task_id': task_id,
            'user_email': session.get('user_email'),
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

# Utility Routes
@app.route('/user_info')
def user_info():
    """Get current user info"""
    if 'user_email' not in session:
        return jsonify({'logged_in': False})
    
    user_email = session.get('user_email')
    return jsonify({
        'logged_in': True,
        'email': user_email,
        'login_time': session.get('login_time'),
        'is_admin': is_admin(user_email)
    })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'active_tasks': len(processing_status),
        'logged_in': 'user_email' in session
    })

# Error Handlers
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

# ============= MAIN =============
if __name__ == '__main__':
    init_db()
    print("🚀 SecurityVision Server Starting...")
    print("📁 Upload folder:", UPLOAD_FOLDER)
    print("📁 Output folder:", OUTPUT_FOLDER)
    print("🎥 Allowed formats:", ", ".join(ALLOWED_EXTENSIONS))
    print("💾 Max file size: 500MB")
    print("🔐 Login system: ENABLED")
    print("👑 Admin system: ENABLED")
    print(f"🔑 Admin emails: {ADMIN_EMAILS}")
    print("🌐 Server running on: http://localhost:5000")
    print("📧 Login page: http://localhost:5000/")
    print("🎛️ Dashboard: http://localhost:5000/dashboard")
    print("📋 Admin records: http://localhost:5000/kayitlar")
    
    app.run(debug=True, host='0.0.0.0', port=5000)