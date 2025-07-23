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

if __name__ == '__main__':
    print("🚀 Video Analysis Server Starting...")
    print("📁 Upload folder:", UPLOAD_FOLDER)
    print("📁 Output folder:", OUTPUT_FOLDER)
    print("🎥 Allowed formats:", ", ".join(ALLOWED_EXTENSIONS))
    print("💾 Max file size: 500MB")
    print("🌐 Server running on: http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)