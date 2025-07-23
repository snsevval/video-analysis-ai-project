from deepface import DeepFace
import cv2
import math
import numpy as np
from norfair import Detection, Tracker
import sqlite3
import json
from datetime import datetime
import time
import traceback
import os

def setup_database(db_path="alarm_analysis.db"):
    """Database setup with custom path"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Drop existing tables and recreate
    cursor.execute('DROP TABLE IF EXISTS video_analysis')
    cursor.execute('DROP TABLE IF EXISTS person_details')
    cursor.execute('DROP TABLE IF EXISTS person_distances')
    cursor.execute('DROP TABLE IF EXISTS alarm_events')

    # Main analysis table
    cursor.execute('''
        CREATE TABLE video_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL,
            formatted_time TEXT,
            person_count INTEGER,
            genders TEXT,
            emotions TEXT,
            speeds TEXT,
            angles TEXT,
            face_ids TEXT,
            distances TEXT,
            analysis_date TEXT,
            alarm_triggered INTEGER DEFAULT 0,
            alarm_reason TEXT
        )
    ''')

    # Detailed person table
    cursor.execute('''
        CREATE TABLE person_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL,
            face_id INTEGER,
            gender TEXT,
            emotion TEXT,
            speed REAL,
            angle REAL,
            bbox_area INTEGER,
            distance_category TEXT,
            x INTEGER,
            y INTEGER,
            width INTEGER,
            height INTEGER,
            danger_status TEXT DEFAULT 'normal',
            danger_level INTEGER DEFAULT 0,
            alarm_triggered INTEGER DEFAULT 0
        )
    ''')

    # Distance table
    cursor.execute('''
        CREATE TABLE person_distances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL,
            person1_id INTEGER,
            person2_id INTEGER,
            distance REAL,
            is_close INTEGER
        )
    ''')

    # Alarm events table
    cursor.execute('''
        CREATE TABLE alarm_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL,
            formatted_time TEXT,
            dangerous_person_id INTEGER,
            dangerous_person_emotion TEXT,
            dangerous_person_speed REAL,
            nearby_persons TEXT,
            alarm_reason TEXT,
            danger_level INTEGER,
            analysis_date TEXT
        )
    ''')

    conn.commit()
    return conn

def calculate_danger_level(emotion, speed, bbox_area):
    """Calculate danger level with clear scoring system (0-10)"""
    level = 0
    reasons = []

    # Emotion score (0-4)
    if emotion:
        if emotion.lower() == 'fear':
            level += 4
            reasons.append("Fear detected")
        elif emotion.lower() == 'angry':
            level += 3
            reasons.append("Anger detected")
        elif emotion.lower() == 'sad':
            level += 2
            reasons.append("Sadness detected")

    # Speed score (0-3)
    if speed > 100:
        level += 3
        reasons.append("Very high speed")
    elif speed > 60:
        level += 2
        reasons.append("High speed")
    elif speed > 30:
        level += 1
        reasons.append("Medium speed")

    # Proximity score (0-2)
    if bbox_area > 8000:
        level += 2
        reasons.append("Very close")
    elif bbox_area > 5000:
        level += 1
        reasons.append("Close")

    # Critical combination bonus
    if emotion and emotion.lower() == 'fear' and speed > 60:
        level += 1
        reasons.append("CRITICAL: Fear + High speed")

    # Cap at 10
    level = min(level, 10)

    # Determine if dangerous (level >= 5)
    is_dangerous = level >= 5
    reason = " | ".join(reasons) if reasons else "Normal"

    return is_dangerous, level, reason

def find_nearby_persons(current_person_idx, face_centers, face_ids, proximity_threshold=200):
    """Find nearby persons"""
    nearby_persons = []
    if current_person_idx >= len(face_centers):
        return nearby_persons

    current_x, current_y = face_centers[current_person_idx]

    for i, (x, y) in enumerate(face_centers):
        if i != current_person_idx:
            distance = math.sqrt((current_x - x)**2 + (current_y - y)**2)
            if distance < proximity_threshold:
                nearby_persons.append({
                    'id': face_ids[i] if i < len(face_ids) else -1,
                    'distance': distance,
                    'position': (x, y)
                })

    return nearby_persons

def save_alarm_event(conn, timestamp, formatted_time, dangerous_person_id, emotion, speed, nearby_persons, reason, danger_level):
    """Save alarm event to database"""
    try:
        cursor = conn.cursor()

        nearby_persons_json = json.dumps([{
            'id': person['id'],
            'distance': person['distance']
        } for person in nearby_persons])

        cursor.execute('''
            INSERT INTO alarm_events
            (timestamp, formatted_time, dangerous_person_id, dangerous_person_emotion, dangerous_person_speed,
             nearby_persons, alarm_reason, danger_level, analysis_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            timestamp,
            formatted_time,
            dangerous_person_id,
            emotion or '',
            speed,
            nearby_persons_json,
            reason,
            danger_level,
            datetime.now().isoformat()
        ))

        conn.commit()
    except Exception as e:
        print(f"Alarm save error: {e}")

def draw_alarm_warning(frame, alarm_active, alarm_count, max_danger_level):
    """Draw alarm warning with clean design"""
    if alarm_active:
        # Blinking border
        if int(time.time() * 4) % 2:
            cv2.rectangle(frame, (0, 0), (frame.shape[1], frame.shape[0]), (0, 0, 255), 8)

        # Clean alarm text
        alarm_text = f"ALARM! {alarm_count} DANGEROUS PERSON(S)"
        cv2.putText(frame, alarm_text, (50, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)

        # Danger level
        level_text = f"DANGER LEVEL: {max_danger_level}/10"
        cv2.putText(frame, level_text, (50, 120),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

def save_to_database(conn, timestamp, formatted_time, person_count, genders, emotions, speeds, angles, face_ids, distances, analysis_results, alarm_data=None):
    """Save analysis data to database"""
    try:
        cursor = conn.cursor()

        # Prepare alarm info
        alarm_triggered = 1 if alarm_data else 0
        alarm_reason = alarm_data.get('reason', '') if alarm_data else ''

        # Save main analysis data
        cursor.execute('''
            INSERT INTO video_analysis
            (timestamp, formatted_time, person_count, genders, emotions, speeds, angles, face_ids, distances, analysis_date, alarm_triggered, alarm_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            timestamp,
            formatted_time,
            person_count,
            json.dumps(genders),
            json.dumps(emotions),
            json.dumps(speeds),
            json.dumps(angles),
            json.dumps(face_ids),
            json.dumps(distances),
            datetime.now().isoformat(),
            alarm_triggered,
            alarm_reason
        ))

        # Save detailed person data
        for i, analysis in enumerate(analysis_results):
            if i < len(face_ids):
                region = analysis.get('region', {})

                # Check alarm status
                is_dangerous = 0
                danger_status = 'normal'
                danger_level = 0

                if alarm_data:
                    if face_ids[i] == alarm_data.get('dangerous_person_id'):
                        is_dangerous = 1
                        danger_status = 'dangerous'
                        danger_level = alarm_data.get('danger_level', 0)
                    elif face_ids[i] in [p['id'] for p in alarm_data.get('nearby_persons', [])]:
                        danger_status = 'at_risk'

                cursor.execute('''
                    INSERT INTO person_details
                    (timestamp, face_id, gender, emotion, speed, angle, bbox_area, distance_category, x, y, width, height, danger_status, danger_level, alarm_triggered)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    timestamp,
                    face_ids[i],
                    genders[i] if i < len(genders) else '',
                    emotions[i] if i < len(emotions) else '',
                    speeds[i] if i < len(speeds) else 0,
                    angles[i] if i < len(angles) else 0,
                    region.get('w', 0) * region.get('h', 0),
                    get_distance_category(region.get('w', 0) * region.get('h', 0)),
                    region.get('x', 0),
                    region.get('y', 0),
                    region.get('w', 0),
                    region.get('h', 0),
                    danger_status,
                    danger_level,
                    is_dangerous
                ))

        # Save distance data
        for dist_data in distances:
            if len(dist_data) >= 3:
                person1_idx, person2_idx, distance = dist_data[:3]
                if person1_idx < len(face_ids) and person2_idx < len(face_ids):
                    cursor.execute('''
                        INSERT INTO person_distances
                        (timestamp, person1_id, person2_id, distance, is_close)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        timestamp,
                        face_ids[person1_idx],
                        face_ids[person2_idx],
                        distance,
                        1 if distance < 150 else 0
                    ))

        conn.commit()

    except Exception as e:
        print(f"Database save error: {e}")

def format_time(seconds):
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 100)
    return f"{mins:02d}:{secs:02d}.{millis:02d}"

def calculate_normalized_speed(dx, dy, bbox_area, dt):
    """Calculate normalized speed"""
    if dt == 0 or bbox_area == 0:
        return 0.0

    pixel_speed = math.sqrt(dx**2 + dy**2) / dt
    base_area = 5000
    normalization_factor = math.sqrt(base_area / max(bbox_area, 1000))
    normalized_speed = pixel_speed * normalization_factor

    return normalized_speed

def get_distance_category(bbox_area):
    """Get distance category based on bbox area"""
    if bbox_area > 8000:
        return "Very Close"
    elif bbox_area > 5000:
        return "Close"
    elif bbox_area > 2500:
        return "Medium"
    elif bbox_area > 1200:
        return "Far"
    else:
        return "Very Far"

def get_danger_color(danger_level):
    """Get color based on danger level"""
    if danger_level >= 8:
        return (0, 0, 255)  # Red
    elif danger_level >= 6:
        return (0, 165, 255)  # Orange
    elif danger_level >= 4:
        return (0, 255, 255)  # Yellow
    else:
        return (0, 255, 0)  # Green

def print_database_stats(conn):
    """Print database statistics"""
    try:
        cursor = conn.cursor()

        print("\n" + "="*50)
        print("DATABASE STATISTICS")
        print("="*50)

        # Basic statistics
        cursor.execute("SELECT COUNT(*) FROM video_analysis")
        total_records = cursor.fetchone()[0]
        print(f"Total analysis records: {total_records}")

        cursor.execute("SELECT COUNT(*) FROM person_details")
        total_persons = cursor.fetchone()[0]
        print(f"Total person records: {total_persons}")

        cursor.execute("SELECT COUNT(*) FROM alarm_events")
        total_alarms = cursor.fetchone()[0]
        print(f"Total alarm events: {total_alarms}")

        # Security statistics
        cursor.execute("SELECT COUNT(*) FROM person_details WHERE danger_status = 'dangerous'")
        dangerous_persons = cursor.fetchone()[0]
        print(f"Dangerous person detections: {dangerous_persons}")

        cursor.execute("SELECT COUNT(*) FROM person_details WHERE danger_status = 'at_risk'")
        at_risk_persons = cursor.fetchone()[0]
        print(f"At risk person detections: {at_risk_persons}")

        cursor.execute("SELECT AVG(danger_level) FROM person_details WHERE danger_level > 0")
        avg_danger = cursor.fetchone()[0]
        if avg_danger:
            print(f"Average danger level: {avg_danger:.2f}")

        print("="*50)

    except Exception as e:
        print(f"Statistics error: {e}")

# ANA FONKSİYON - FLASK İÇİN
def analyze_video(video_path, output_dir="outputs", progress_callback=None):
    """
    Ana video analiz fonksiyonu - Flask'tan çağrılacak
    
    Args:
        video_path (str): İşlenecek video dosyasının yolu
        output_dir (str): Çıktı dosyalarının kaydedileceği klasör
        progress_callback (function): İlerleme durumunu bildirmek için callback fonksiyonu
    
    Returns:
        dict: Analiz sonuçları
    """
    try:
        # Çıktı klasörünü oluştur
        os.makedirs(output_dir, exist_ok=True)
        
        # Database path
        db_path = os.path.join(output_dir, "alarm_analysis.db")
        
        # Initialize database
        conn = setup_database(db_path)
        print("Database initialized successfully!")

        # Variables
        prev_positions = {}
        speed_history = {}

        # Video and tracker
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise Exception("Could not open video file!")

        tracker = Tracker(distance_function="euclidean", distance_threshold=40)

        # Video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Output video path
        video_filename = os.path.splitext(os.path.basename(video_path))[0]
        output_video_path = os.path.join(output_dir, f"{video_filename}_analyzed.mp4")
        
        # Output video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_video_path, fourcc, fps / 5, (1280, 720))

        frame_number = 0
        frame_results = []
        total_alarms = 0
        max_danger_detected = 0

        print("Video processing started...")

        while True:
            ret, frame = cap.read()
            if not ret:
                print("End of video")
                break

            # Progress callback
            if progress_callback:
                progress = (frame_number / total_frames) * 100
                progress_callback(progress)

            # Process every 5th frame
            if frame_number % 5 == 0:
                try:
                    # Resize frame
                    frame = cv2.resize(frame, (1280, 720))

                    # Calculate timestamp
                    timestamp = frame_number / fps
                    formatted_time = format_time(timestamp)

                    # Face analysis
                    analysis = DeepFace.analyze(frame,
                                              actions=['gender', 'emotion'],
                                              detector_backend="retinaface",
                                              enforce_detection=False)

                    if isinstance(analysis, dict):
                        analysis = [analysis]

                    if len(analysis) == 0:
                        # No person detected
                        cv2.putText(frame, f"{formatted_time} -> No person detected", (10, 30),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                        out.write(frame)
                        frame_number += 1
                        continue

                    # Calculate face centers and bbox areas
                    face_centers = []
                    bbox_areas = []

                    for person in analysis:
                        region = person.get('region', {})
                        x, y, w, h = region.get('x', 0), region.get('y', 0), region.get('w', 50), region.get('h', 50)
                        cx, cy = x + w // 2, y + h // 2
                        bbox_area = w * h

                        face_centers.append((cx, cy))
                        bbox_areas.append(bbox_area)

                    # Tracking
                    norfair_detections = [Detection(points=np.array([[cx, cy]])) for cx, cy in face_centers]
                    tracked_objects = tracker.update(detections=norfair_detections)

                    # Face ID matching
                    face_ids = []
                    for cx, cy in face_centers:
                        matched_id = -1
                        min_dist = float("inf")
                        for obj in tracked_objects:
                            if len(obj.estimate) > 0:
                                tx, ty = obj.estimate[0]
                                dist = math.hypot(tx - cx, ty - cy)
                                if dist < min_dist:
                                    min_dist = dist
                                    matched_id = obj.id
                        face_ids.append(matched_id)

                    # Motion analysis
                    genders, emotions, speeds, angles = [], [], [], []
                    alarm_active = False
                    alarm_count = 0
                    max_danger_level = 0
                    alarm_data = None
                    dangerous_persons = []

                    for i, person in enumerate(analysis):
                        dominant_gender = person.get('dominant_gender', '')
                        dominant_emotion = person.get('dominant_emotion', '')
                        region = person.get('region', {})
                        x, y, w, h = region.get('x', 0), region.get('y', 0), region.get('w', 50), region.get('h', 50)
                        cx, cy = x + w // 2, y + h // 2
                        bbox_area = w * h

                        matched_id = face_ids[i] if i < len(face_ids) else -1

                        # Speed calculation
                        if matched_id in prev_positions:
                            prev_data = prev_positions[matched_id]
                            px, py, prev_bbox_area, prev_timestamp = prev_data

                            dx = cx - px
                            dy = cy - py
                            dt = timestamp - prev_timestamp

                            if abs(dx) < 2 and abs(dy) < 2:
                                speed = 0.0
                                angle = 0.0
                            else:
                                speed = calculate_normalized_speed(dx, dy, bbox_area, dt)
                                angle = math.degrees(math.atan2(dy, dx))

                                # Speed smoothing
                                if matched_id not in speed_history:
                                    speed_history[matched_id] = []
                                speed_history[matched_id].append(speed)
                                if len(speed_history[matched_id]) > 5:
                                    speed_history[matched_id].pop(0)

                                smooth_speed = sum(speed_history[matched_id]) / len(speed_history[matched_id])
                                speed = smooth_speed

                                # Draw motion arrow
                                cv2.arrowedLine(frame, (int(px), int(py)), (int(cx), int(cy)), (0, 255, 0), 2, tipLength=0.3)
                        else:
                            speed = 0.0
                            angle = 0.0

                        # Danger level calculation
                        is_dangerous, danger_level, danger_reason = calculate_danger_level(dominant_emotion, speed, bbox_area)
                        max_danger_detected = max(max_danger_detected, danger_level)

                        # Choose box color based on danger level
                        box_color = get_danger_color(danger_level)
                        box_thickness = 3 if is_dangerous else 1

                        # Draw bounding box
                        cv2.rectangle(frame, (x, y), (x + w, y + h), box_color, box_thickness)

                        # Clean label - only essential info
                        distance_cat = get_distance_category(bbox_area)
                        label = f"ID:{matched_id} {dominant_gender} {dominant_emotion} {distance_cat}"
                        cv2.putText(frame, label, (x, y - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 2)

                        # Speed display
                        if speed > 0:
                            speed_color = get_danger_color(danger_level)
                            speed_text = f"{speed:.1f} px/s"
                            cv2.putText(frame, speed_text, (x, y - 30),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, speed_color, 2)

                        # Danger level display for dangerous persons
                        if is_dangerous:
                            level_text = f"DANGER: {danger_level}/10"
                            cv2.putText(frame, level_text, (x, y - 50),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

                        # Update position
                        prev_positions[matched_id] = (cx, cy, bbox_area, timestamp)

                        # Add to lists
                        genders.append(dominant_gender)
                        emotions.append(dominant_emotion)
                        speeds.append(speed)
                        angles.append(angle)

                        # Alarm processing
                        if is_dangerous:
                            alarm_active = True
                            alarm_count += 1
                            max_danger_level = max(max_danger_level, danger_level)

                            nearby_persons = find_nearby_persons(i, face_centers, face_ids)

                            dangerous_persons.append({
                                'id': matched_id,
                                'emotion': dominant_emotion,
                                'speed': speed,
                                'nearby_persons': nearby_persons,
                                'reason': danger_reason,
                                'danger_level': danger_level
                            })

                            # Save alarm event
                            save_alarm_event(conn, timestamp, formatted_time, matched_id,
                                           dominant_emotion, speed, nearby_persons, danger_reason, danger_level)

                            print(f"ALARM! Time: {formatted_time}, Person ID: {matched_id}, Level: {danger_level}")
                            total_alarms += 1

                    # Draw alarm warning
                    if alarm_active:
                        draw_alarm_warning(frame, True, alarm_count, max_danger_level)
                        alarm_data = {
                            'dangerous_person_id': dangerous_persons[0]['id'] if dangerous_persons else -1,
                            'nearby_persons': dangerous_persons[0]['nearby_persons'] if dangerous_persons else [],
                            'reason': f"{alarm_count} person(s) in dangerous state",
                            'danger_level': max_danger_level
                        }

                    # Distance checking
                    distances = []
                    if len(face_centers) > 1:
                        for i in range(len(face_centers)):
                            for j in range(i + 1, len(face_centers)):
                                x1, y1 = face_centers[i]
                                x2, y2 = face_centers[j]
                                distance = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

                                if distance < 150:
                                    mid_x, mid_y = (x1 + x2) // 2, (y1 + y2) // 2
                                    cv2.line(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                                    cv2.putText(frame, f"{int(distance)} px", (mid_x, mid_y),
                                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

                                distances.append((i, j, distance))

                    # Time information
                    cv2.putText(frame, f"{formatted_time} -> {len(analysis)} person(s)", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

                    # Save to database
                    person_count = len(analysis)
                    save_to_database(conn, timestamp, formatted_time, person_count, genders, emotions, speeds, angles, face_ids, distances, analysis, alarm_data)

                    frame_results.append((timestamp, person_count, genders, emotions, speeds, distances, face_ids))

                    # Progress
                    if len(frame_results) % 20 == 0:
                        print(f"Processed frames: {len(frame_results)}, Persons: {person_count}, Time: {formatted_time}")

                except Exception as e:
                    print(f"Frame {frame_number} error: {e}")
                    print(traceback.format_exc())
                    # Save error frame
                    cv2.putText(frame, f"{format_time(frame_number/fps)} -> ERROR", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            # Write frame to video
            out.write(frame)
            frame_number += 1

        # Clean up resources
        cap.release()
        out.release()

        # Statistics
        print_database_stats(conn)
        conn.close()

        # Return results
        results = {
            'success': True,
            'message': 'Video analysis completed successfully!',
            'stats': {
                'total_frames': frame_number,
                'processed_frames': len(frame_results),
                'total_alarms': total_alarms,
                'max_danger_level': max_danger_detected
            },
            'files': {
                'analyzed_video': output_video_path,
                'database': db_path
            }
        }
        
        print(f"\nAnalysis completed!")
        print(f"Video: {output_video_path}")
        print(f"Database: {db_path}")
        print(f"Processed frames: {len(frame_results)}")
        print(f"Total alarms: {total_alarms}")
        
        return results

    except Exception as e:
        print(f"Analysis error: {e}")
        print(traceback.format_exc())
        return {
            'success': False,
            'message': f'Video analysis failed: {str(e)}',
            'error': str(e)
        }

# Original main function - standalone kullanım için
def main():
    """Standalone kullanım için ana fonksiyon"""
    video_path = "test_video.mp4"  # Test videosu için
    result = analyze_video(video_path)
    
    if result['success']:
        print("Analysis successful!")
        print(f"Results: {result}")
    else:
        print(f"Analysis failed: {result['message']}")

if __name__ == "__main__":
    main()