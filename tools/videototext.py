import os
import cv2
import shutil
import tempfile
import requests
from pathlib import Path
from mimetypes import guess_type
import google.generativeai as genai
import sys 
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from prompts.videoprompt import video_prompt 

genai.configure(api_key=" ")
model = genai.GenerativeModel("gemini-1.5-flash")


class VideoAnalysis:
    def __init__(self):
        self.temp_dir = None

    def create_temp_directory(self):
        """Create a temporary directory for video frame extraction"""
        if self.temp_dir:
            self.cleanup()
        self.temp_dir = tempfile.mkdtemp()
        return self.temp_dir

    def download_videos(self, video_urls):
        """Download videos into temp folder and return local file paths"""
        temp_dir = self.create_temp_directory()
        local_files = []

        for idx, url in enumerate(video_urls, start=1):
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                file_ext = Path(url).suffix or ".mp4"
                local_path = os.path.join(temp_dir, f"video_{idx}{file_ext}")
                with open(local_path, "wb") as f:
                    shutil.copyfileobj(response.raw, f)
                local_files.append(local_path)
            else:
                print(f"⚠️ Failed to download {url}")
        return local_files

    def extract_frames(self, video_path, frame_interval=60):
        """
        Extract frames from video at specified intervals.
        Returns list of frame paths.
        """
        frames_dir = os.path.join(self.temp_dir, "frames")
        os.makedirs(frames_dir, exist_ok=True)

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")

        frame_count = 0
        saved_count = 0
        frame_paths = []

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % frame_interval == 0:
                frame_path = os.path.join(frames_dir, f"{Path(video_path).stem}_frame_{saved_count:04d}.jpg")
                cv2.imwrite(frame_path, frame)
                frame_paths.append(frame_path)
                saved_count += 1

            frame_count += 1

        cap.release()
        return frame_paths

    def analyze_video(self, video_urls):
        """
        Analyze list of videos using Gemini and return list of extracted texts.
        """
        local_files = self.download_videos(video_urls)
        results = []

        try:
            for video_file in local_files:
                frame_paths = self.extract_frames(video_file)

                if not frame_paths:
                    results.append("⚠️ No frames extracted from video.")
                    continue

                # Use first 5 frames for summary (to save tokens)
                selected_frames = frame_paths[:5]

                frame_inputs = []
                for frame in selected_frames:
                    with open(frame, "rb") as f:
                        image_bytes = f.read()
                    mime_type, _ = guess_type(frame)
                    mime_type = mime_type or "image/jpeg"
                    frame_inputs.append({"mime_type": mime_type, "data": image_bytes})

                # Ask Gemini for video understanding
                response = model.generate_content(
                    [ video_prompt, *frame_inputs]
                )

                results.append(response.text.strip() if response.text else "")

            return results
        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up temporary directory"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            self.temp_dir = None


if __name__ == "__main__":
    video_urls = ['https://dms.licdn.com/playlist/vid/v2/D5605AQGJJFdPWzOBmQ/mp4-640p-30fp-crf28/B56ZkS26weHIBs-/0/1756958300850?e=2147483647&v=beta&t=VboDZBKoYjvuCOEaJhdLEoSiohxGgPFWHtju3HlDIj4']
    analyzer = VideoAnalysis()
    summaries = analyzer.analyze_video(video_urls)

    for url, text in zip(video_urls, summaries):
        print(f"\n🎬 Video: {url}\n📜 Extracted Summary: {text}\n")
