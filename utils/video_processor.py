import os
import cv2
import json
import subprocess
from utils.ascii_converter import ASCIIConverter

class VideoProcessor:
    def __init__(self, video_path, output_dir, width=80):
        self.video_path = video_path
        self.output_dir = output_dir
        self.width = width
        self.converter = ASCIIConverter(width=width)
        
        os.makedirs(output_dir, exist_ok=True)
        
    def get_video_info(self):
        """Extract video metadata"""
        cap = cv2.VideoCapture(self.video_path)
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        
        # Get thumbnail
        success, frame = cap.read()
        thumbnail_path = None
        if success:
            thumbnail_path = os.path.join(self.output_dir, "thumbnail.jpg")
            cv2.imwrite(thumbnail_path, frame)
        
        cap.release()
        
        return {
            "fps": fps,
            "frame_count": frame_count,
            "duration": duration,
            "width": self.width,
            "thumbnail": thumbnail_path
        }
    
    def extract_audio(self):
        """Extract audio from video"""
        audio_path = os.path.join(self.output_dir, "audio.mp3")
        
        try:
            cmd = [
                'ffmpeg', '-i', self.video_path,
                '-q:a', '0', '-map', 'a',
                audio_path, '-y'
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            return audio_path
        except subprocess.CalledProcessError:
            # Fallback to WAV if MP3 fails
            audio_path = os.path.join(self.output_dir, "audio.wav")
            cmd = [
                'ffmpeg', '-i', self.video_path,
                '-vn', '-acodec', 'pcm_s16le',
                '-ar', '44100', '-ac', '2',
                audio_path, '-y'
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            return audio_path
    
    def generate_ascii_frames(self):
        """Generate ASCII frames from video"""
        cap = cv2.VideoCapture(self.video_path)
        frame_number = 0
        frames_dir = os.path.join(self.output_dir, "frames")
        os.makedirs(frames_dir, exist_ok=True)
        
        frame_paths = []
        
        while True:
            success, frame = cap.read()
            if not success:
                break
                
            ascii_art = self.converter.convert_frame(frame)
            frame_filename = f"frame_{frame_number:06d}.txt"
            frame_path = os.path.join(frames_dir, frame_filename)
            
            with open(frame_path, 'w', encoding='utf-8') as f:
                f.write(ascii_art)
            
            frame_paths.append(frame_filename)
            frame_number += 1
        
        cap.release()
        return frame_paths
    
    def process_video(self):
        """Main processing function"""
        print(f"Processing video: {self.video_path}")
        
        # Get video info
        metadata = self.get_video_info()
        print("Extracted video metadata")
        
        # Extract audio
        audio_path = self.extract_audio()
        metadata['audio_path'] = audio_path
        print("Extracted audio")
        
        # Generate ASCII frames
        frame_paths = self.generate_ascii_frames()
        metadata['frame_count'] = len(frame_paths)
        metadata['frame_paths'] = frame_paths
        print(f"Generated {len(frame_paths)} ASCII frames")
        
        # Save metadata
        metadata_path = os.path.join(self.output_dir, "metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print("Processing complete")
        return metadata