from flask import Flask, request, jsonify, render_template, send_file, url_for
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
import threading
from process import analyze_video  # Sizin process.py dosyasından

app = Flask(__name__)

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

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_video():
    """Handle video upload and start analysis"""
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
            'start_time': datetime.now().isoformat()
        }
        
        # Start background analysis
        thread = threading.Thread(
            target=analyze_video_background,
            args=(task_id, file_path, output_dir)
        )
        thread.daemon = True
        thread.start()
        
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
    if task_id not in processing_status:
        return jsonify({'error': 'Task not found'}), 404
    
    status = processing_status[task_id]
    if status['status'] != 'completed':
        return jsonify({'error': 'Analysis not completed'}), 400
    
    try:
        video_path = status['result']['files']['analyzed_video']
        if os.path.exists(video_path):
            return send_file(video_path, as_attachment=True)
        else:
            return jsonify({'error': 'Video file not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/database/<task_id>')
def download_database(task_id):
    """Download analysis database"""
    if task_id not in processing_status:
        return jsonify({'error': 'Task not found'}), 404
    
    status = processing_status[task_id]
    if status['status'] != 'completed':
        return jsonify({'error': 'Analysis not completed'}), 400
    
    try:
        db_path = status['result']['files']['database']
        if os.path.exists(db_path):
            return send_file(db_path, as_attachment=True)
        else:
            return jsonify({'error': 'Database file not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/results/<task_id>')
def get_results(task_id):
    """Get detailed analysis results"""
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

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'active_tasks': len(processing_status)
    })

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
# ============= LLM RAPOR SİSTEMİ =============
import requests
import json
import sqlite3
from datetime import datetime


@app.route('/generate_report', methods=['POST'])
def generate_report():
    """ANA SAYFA için LLM raporu oluştur"""
    try:
        data = request.get_json()
        db_file = data.get('db_file')
        
        if not db_file:
            return jsonify({'error': 'Database file not specified'}), 400
        
        print(f"Gelen db_file: {db_file}")  # Debug için
        
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
        
        print(f"Aranan path: {db_path}")  # Debug için
        
        if not db_path or not os.path.exists(db_path):
            return jsonify({'error': f'Database file not found: {db_path}'}), 404
        
        
        print(f"Database analizi başlıyor...")
        data_summary = analyze_database(db_path)  # Database'den veri çek
        print(f"Database analizi tamamlandı: {len(data_summary.get('detailed_alarms', []))} alarm")

        print(f"LLM raporu başlıyor...")
        report = generate_llm_report(data_summary) # LLM'e rapor hazırlat
        print(f"LLM raporu tamamlandı: {len(report)} karakter")
        
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
{alarm['time']} - Kişi ID: {alarm['person_id']} | Cinsiyet: {alarm.get('gender', 'Bilinmiyor')} | Duygu: {alarm['emotion']} | Hız: {alarm['speed']:.0f} | Tehlike: {alarm['danger_level']} | Yakında: {alarm['nearby_count']} kişi
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

    # ... Ollama isteği

    try:
        response = requests.post('http://localhost:11434/api/generate', 
                               json={
                                   'model': 'llama3.2:3b',
                                   'prompt': prompt,
                                   'stream': False
                               },
                               timeout=300)
        
        if response.status_code == 200:
            result = response.json()
            return result['response']
        else:
            return f"LLM API Hatası: {response.status_code} - {response.text}"
            
    except requests.exceptions.RequestException as e:
        return f"🔌 Bağlantı Hatası: Ollama sunucusu çalışmıyor olabilir.\n\nHata: {str(e)}\n\nÇözüm:\n1. Yeni terminal açın\n2. 'ollama serve' komutunu çalıştırın\n3. Tekrar deneyin"
    except Exception as e:
        return f"Beklenmeyen Hata: {str(e)}"


if __name__ == '__main__':

    print("🚀 Video Analysis Server Starting...")
    print("📁 Upload folder:", UPLOAD_FOLDER)
    print("📁 Output folder:", OUTPUT_FOLDER)
    print("🎥 Allowed formats:", ", ".join(ALLOWED_EXTENSIONS))
    print("💾 Max file size: 500MB")
    print("🌐 Server running on: http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)