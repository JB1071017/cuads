import os
import uuid
import json
from flask import Flask, render_template, request, jsonify, send_file, Response, stream_with_context
from werkzeug.utils import secure_filename
from config import Config, create_folders
from background_processor import processor  # Changed from tasks

app = Flask(__name__)
app.config.from_object(Config)
create_folders()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload')
def upload_page():
    return render_template('upload.html')

@app.route('/preview/<video_id>')
def preview_page(video_id):
    return render_template('preview.html', video_id=video_id)

@app.route('/manage')
def manage_page():
    return render_template('manage.html')

@app.route('/api/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file'}), 400
    
    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        # Generate unique ID
        video_id = str(uuid.uuid4())
        upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], video_id)
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        video_path = os.path.join(upload_dir, filename)
        file.save(video_path)
        
        # Start background processing (no Redis needed!)
        processor.process_video(video_path, upload_dir, video_id)
        
        return jsonify({
            'video_id': video_id,
            'status': 'processing',
            'stream_url': f'/stream/{video_id}',
            'audio_url': f'/audio/{video_id}',
            'curl_command': f'curl -N {request.host_url}stream/{video_id}'
        })
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/api/status/<video_id>')
def get_processing_status(video_id):
    status_info = processor.get_status(video_id)
    return jsonify(status_info)

@app.route('/stream/<video_id>')
def stream_ascii(video_id):
    """Stream ASCII video to terminal"""
    if video_id == 'jb':
        video_dir = app.config['OWNER_FOLDER']
    else:
        video_dir = os.path.join(app.config['UPLOAD_FOLDER'], video_id)
    
    metadata_path = os.path.join(video_dir, 'metadata.json')
    
    if not os.path.exists(metadata_path):
        return "Video not found", 404
    
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    fps = metadata.get('fps', 24)
    frame_delay = 1.0 / fps
    
    def generate():
        frames_dir = os.path.join(video_dir, 'frames')
        frame_paths = metadata.get('frame_paths', [])
        
        while True:  # Loop forever
            for frame_file in frame_paths:
                frame_path = os.path.join(frames_dir, frame_file)
                if os.path.exists(frame_path):
                    with open(frame_path, 'r', encoding='utf-8') as f:
                        frame_content = f.read()
                    
                    # ANSI clear screen and home cursor
                    yield '\033[2J\033[H' + frame_content
                    
                    import time
                    time.sleep(frame_delay)
    
    return Response(stream_with_context(generate()),
                   mimetype='text/plain',
                   headers={'Cache-Control': 'no-cache'})

@app.route('/audio/<video_id>')
def stream_audio(video_id):
    if video_id == 'jb':
        video_dir = app.config['OWNER_FOLDER']
    else:
        video_dir = os.path.join(app.config['UPLOAD_FOLDER'], video_id)
    
    # Try to find audio file
    audio_extensions = ['.mp3', '.wav']
    for ext in audio_extensions:
        audio_path = os.path.join(video_dir, f'audio{ext}')
        if os.path.exists(audio_path):
            return send_file(audio_path, mimetype='audio/mpeg')
    
    return "Audio not found", 404

@app.route('/info/<video_id>')
def video_info(video_id):
    if video_id == 'jb':
        video_dir = app.config['OWNER_FOLDER']
    else:
        video_dir = os.path.join(app.config['UPLOAD_FOLDER'], video_id)
    
    metadata_path = os.path.join(video_dir, 'metadata.json')
    
    if not os.path.exists(metadata_path):
        return jsonify({'error': 'Video not found'}), 404
    
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    return jsonify(metadata)

@app.route('/api/videos')
def list_videos():
    """List all processed videos"""
    videos = []
    
    # Add owner stream if it exists
    owner_metadata_path = os.path.join(app.config['OWNER_FOLDER'], 'metadata.json')
    if os.path.exists(owner_metadata_path):
        with open(owner_metadata_path, 'r') as f:
            owner_meta = json.load(f)
        videos.append({
            'id': 'owner',
            'name': 'Default Stream',
            'duration': owner_meta.get('duration', 0),
            'fps': owner_meta.get('fps', 24),
            'status': 'completed'
        })
    
    # Add uploaded videos
    for video_id in os.listdir(app.config['UPLOAD_FOLDER']):
        video_dir = os.path.join(app.config['UPLOAD_FOLDER'], video_id)
        metadata_path = os.path.join(video_dir, 'metadata.json')
        
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            videos.append({
                'id': video_id,
                'name': f'Uploaded Video {video_id[:8]}',
                'duration': metadata.get('duration', 0),
                'fps': metadata.get('fps', 24),
                'status': 'completed'
            })
        else:
            # Check if still processing
            status_info = processor.get_status(video_id)
            if status_info['status'] != 'not_found':
                videos.append({
                    'id': video_id,
                    'name': f'Uploaded Video {video_id[:8]}',
                    'status': status_info['status']
                })
    
    return jsonify(videos)

# Create a simple owner video on startup
def create_sample_owner_video():
    """Create a simple text-based animation for owner stream"""
    owner_dir = app.config['OWNER_FOLDER']
    os.makedirs(owner_dir, exist_ok=True)
    
    frames_dir = os.path.join(owner_dir, 'frames')
    os.makedirs(frames_dir, exist_ok=True)
    
    # Create a simple ASCII animation
    frame_count = 100
    fps = 10
    
    for i in range(frame_count):
        frame_content = []
        frame_content.append(" " * 40 + "ASCII VIDEO STREAMER")
        frame_content.append(" " * 38 + "=" * 25)
        frame_content.append("")
        
        # Create animated text
        for j in range(15):
            line = " " * 20
            for k in range(40):
                if (i + j + k) % 4 == 0:
                    line += "#"
                else:
                    line += " "
            frame_content.append(line)
        
        frame_content.append("")
        frame_content.append(" " * 35 + f"Frame: {i+1:03d}/{frame_count}")
        frame_content.append(" " * 30 + "Streaming ASCII Art...")
        frame_content.append("")
        frame_content.append(" " * 25 + "Upload your own video at:")
        frame_content.append(" " * 25 + "http://127.0.0.1:5000/upload")
        
        frame_text = "\n".join(frame_content)
        
        frame_filename = f"frame_{i:06d}.txt"
        frame_path = os.path.join(frames_dir, frame_filename)
        
        with open(frame_path, 'w', encoding='utf-8') as f:
            f.write(frame_text)
    
    # Create metadata
    metadata = {
        "fps": fps,
        "frame_count": frame_count,
        "duration": frame_count / fps,
        "width": 80,
        "frame_paths": [f"frame_{i:06d}.txt" for i in range(frame_count)]
    }
    
    metadata_path = os.path.join(owner_dir, 'metadata.json')
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print("✅ Owner stream created with sample animation!")

# Create owner video when app starts
with app.app_context():
    create_sample_owner_video()

if __name__ == '__main__':
    print("🚀 Starting ASCII Video Streamer...")
    print("📺 Owner stream: curl -N http://127.0.0.1:5000/stream/owner")
    print("🌐 Web interface: http://127.0.0.1:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)