#!/usr/bin/env python3
"""
24/7 YouTube Live Stream Tool for GitHub Actions
PC বন্ধ থাকলেও চলবে!
"""

import subprocess
import time
import os
import sys
import signal
import requests
from datetime import datetime

class YouTubeLiveStreamer:
    def __init__(self):
        print("🎬 24/7 YouTube Live Streamer")
        print("=" * 60)
        print(f"⏰ Started at: {datetime.now()}")
        
        # Environment variables থেকে settings
        self.stream_key = os.getenv('YOUTUBE_STREAM_KEY')
        self.video_url = os.getenv('VIDEO_URL')
        self.video_quality = os.getenv('VIDEO_QUALITY', '720p')
        
        # Validate
        if not self.stream_key:
            print("❌ YOUTUBE_STREAM_KEY missing!")
            print("💡 Add it in GitHub Secrets!")
            sys.exit(1)
        
        if not self.video_url:
            print("❌ VIDEO_URL missing!")
            print("💡 Add it in GitHub Secrets!")
            sys.exit(1)
        
        # YouTube RTMP
        self.rtmp_url = f"rtmp://a.rtmp.youtube.com/live2/{self.stream_key}"
        
        # Quality settings
        self.qualities = {
            '360p': {'size': '640x360', 'bitrate': '800k', 'fps': 25},
            '480p': {'size': '854x480', 'bitrate': '1200k', 'fps': 25},
            '720p': {'size': '1280x720', 'bitrate': '2500k', 'fps': 30},
            '1080p': {'size': '1920x1080', 'bitrate': '4500k', 'fps': 30}
        }
        
        self.settings = self.qualities.get(self.video_quality, self.qualities['720p'])
        
        print(f"✅ Stream Key: {self.stream_key[:8]}...{self.stream_key[-4:]}")
        print(f"✅ Video URL: {self.video_url[:50]}...")
        print(f"✅ Quality: {self.video_quality}")
        print("=" * 60)
        
        self.process = None
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        signal.signal(signal.SIGINT, self.handle_shutdown)
    
    def handle_shutdown(self, signum, frame):
        print("\n⚠️ Shutdown signal received...")
        print("🔄 Stream will auto-restart in next workflow run!")
        if self.process:
            self.process.terminate()
        sys.exit(0)
    
    def download_video(self):
        """Video download করুন (যদি local না থাকে)"""
        print("📥 Checking video file...")
        
        video_file = "stream_video.mp4"
        
        if os.path.exists(video_file):
            file_size = os.path.getsize(video_file) / (1024 * 1024)  # MB
            print(f"✅ Video already exists: {video_file} ({file_size:.1f} MB)")
            return video_file
        
        print("📥 Downloading video from URL...")
        print("⏳ This may take a few minutes...")
        
        try:
            response = requests.get(self.video_url, stream=True, timeout=60)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(video_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            mb_downloaded = downloaded / (1024 * 1024)
                            mb_total = total_size / (1024 * 1024)
                            print(f"\r📥 Downloading: {progress:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)", 
                                  end="", flush=True)
            
            print(f"\n✅ Video downloaded successfully!")
            return video_file
            
        except Exception as e:
            print(f"\n❌ Download failed: {e}")
            print("\n💡 Tips:")
            print("  - Make sure VIDEO_URL is a direct download link")
            print("  - For Google Drive: use https://drive.google.com/uc?export=download&id=FILE_ID")
            print("  - For Dropbox: change ?dl=0 to ?dl=1")
            sys.exit(1)
    
    def check_ffmpeg(self):
        """FFmpeg check করুন"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, timeout=5)
            if result.returncode == 0:
                print("✅ FFmpeg found!")
                return True
        except:
            pass
        
        print("❌ FFmpeg not found!")
        print("💡 Installing FFmpeg...")
        return False
    
    def build_ffmpeg_command(self, video_file):
        """FFmpeg command তৈরি করুন - Optimized for stability"""
        cmd = [
            'ffmpeg',
            '-re',  # Real-time streaming
            '-stream_loop', '-1',  # Infinite loop
            '-i', video_file,
            
            # Video encoding - optimized for stability
            '-c:v', 'libx264',
            '-preset', 'veryfast',
            '-b:v', self.settings['bitrate'],
            '-maxrate', self.settings['bitrate'],
            '-bufsize', f"{int(self.settings['bitrate'][:-1]) * 2}k",
            '-s', self.settings['size'],
            '-r', str(self.settings['fps']),
            '-g', str(self.settings['fps'] * 2),  # Keyframe interval
            '-pix_fmt', 'yuv420p',
            
            # Audio encoding
            '-c:a', 'aac',
            '-b:a', '128k',
            '-ar', '44100',
            '-ac', '2',
            
            # Streaming optimizations for reconnection
            '-f', 'flv',
            '-flvflags', 'no_duration_filesize',
            '-reconnect', '1',
            '-reconnect_streamed', '1',
            '-reconnect_delay_max', '5',
            
            # Output
            self.rtmp_url
        ]
        
        return cmd
    
    def start_streaming(self):
        """Live streaming শুরু করুন"""
        
        # FFmpeg check
        if not self.check_ffmpeg():
            print("❌ Please install FFmpeg first!")
            sys.exit(1)
        
        # Video download/check
        video_file = self.download_video()
        
        # Build command
        cmd = self.build_ffmpeg_command(video_file)
        
        print("\n" + "=" * 60)
        print("🚀 Starting 24/7 YouTube Live Stream")
        print("=" * 60)
        print(f"📺 Quality: {self.video_quality}")
        print(f"♾️  Loop mode: ENABLED")
        print(f"🔄 Auto-reconnect: ENABLED")
        print(f"⏰ Duration: Will run for ~5.5 hours")
        print(f"🔁 Next restart: Automatic (via GitHub Actions)")
        print("=" * 60)
        print("💡 Your PC can be OFF - this runs on GitHub servers!")
        print("=" * 60 + "\n")
        
        retry_count = 0
        max_retries = 50  # More retries for stability
        
        while True:
            try:
                if retry_count > 0:
                    print(f"\n🔄 Reconnection attempt #{retry_count}")
                
                print(f"🎬 Stream starting at {datetime.now()}")
                
                # Start FFmpeg process
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=1
                )
                
                # Monitor process and show output
                last_output_time = time.time()
                
                for line in iter(self.process.stdout.readline, ''):
                    if line:
                        # Show important FFmpeg output
                        if 'frame=' in line or 'speed=' in line:
                            print(f"\r⚡ {line.strip()[:80]}", end="", flush=True)
                            last_output_time = time.time()
                        elif 'error' in line.lower() or 'failed' in line.lower():
                            print(f"\n⚠️  {line.strip()}")
                    
                    # Check if process is still running
                    if self.process.poll() is not None:
                        break
                    
                    # Timeout check (if no output for 2 minutes)
                    if time.time() - last_output_time > 120:
                        print("\n⚠️  No output for 2 minutes, restarting...")
                        self.process.terminate()
                        break
                
                # Process ended
                return_code = self.process.returncode
                
                print(f"\n⚠️  Stream ended with code: {return_code}")
                
                retry_count += 1
                
                if retry_count >= max_retries:
                    print(f"\n✅ Reached max retries. Workflow will restart automatically.")
                    print(f"🔄 Next run scheduled in ~30 minutes (via GitHub Actions)")
                    break
                
                # Exponential backoff
                wait_time = min(retry_count * 5, 30)
                print(f"🔄 Reconnecting in {wait_time} seconds...")
                time.sleep(wait_time)
                    
            except KeyboardInterrupt:
                print("\n⚠️  Stopped by user (or workflow timeout)")
                print("🔄 Next run will start automatically")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                retry_count += 1
                
                if retry_count >= max_retries:
                    print(f"\n✅ Max retries reached. Exiting gracefully.")
                    break
                
                time.sleep(10)
        
        print("\n" + "=" * 60)
        print("👋 Stream session ended")
        print("🔄 GitHub Actions will automatically start next session")
        print("=" * 60)

def main():
    """Main function"""
    print("\n" + "=" * 60)
    print("🎬 YouTube 24/7 Live Streamer")
    print("=" * 60)
    print("✅ Runs on GitHub Actions (FREE)")
    print("✅ PC বন্ধ থাকলেও চলবে!")
    print("✅ Auto-restart every 5.5 hours")
    print("♾️  Infinite loop streaming")
    print("=" * 60 + "\n")
    
    try:
        streamer = YouTubeLiveStreamer()
        streamer.start_streaming()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()