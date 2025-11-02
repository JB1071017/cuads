import os
import threading
import time
from utils.video_processor import VideoProcessor

class BackgroundProcessor:
    def __init__(self):
        self.tasks = {}
        self.results = {}
    
    def process_video(self, video_path, output_dir, video_id):
        """Process video in background thread"""
        def task():
            try:
                print(f"Starting processing for {video_id}")
                processor = VideoProcessor(video_path, output_dir)
                metadata = processor.process_video()
                
                # Clean up uploaded original video
                if os.path.exists(video_path):
                    os.remove(video_path)
                
                self.results[video_id] = {
                    'status': 'completed',
                    'metadata': metadata
                }
                print(f"Completed processing for {video_id}")
                
            except Exception as e:
                # Clean up on error
                if os.path.exists(video_path):
                    os.remove(video_path)
                self.results[video_id] = {
                    'status': 'error',
                    'error': str(e)
                }
                print(f"Error processing {video_id}: {e}")
        
        # Start background thread
        thread = threading.Thread(target=task)
        thread.daemon = True
        thread.start()
        
        self.tasks[video_id] = {
            'thread': thread,
            'start_time': time.time()
        }
    
    def get_status(self, video_id):
        """Get processing status"""
        if video_id in self.results:
            return self.results[video_id]
        elif video_id in self.tasks:
            return {'status': 'processing'}
        else:
            return {'status': 'not_found'}

# Global processor instance
processor = BackgroundProcessor()