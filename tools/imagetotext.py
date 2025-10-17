import os
import shutil
import tempfile
import requests
from pathlib import Path
import google.generativeai as genai
from mimetypes import guess_type
import sys 
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from prompts.imageprompt import image_prompt

genai.configure(api_key="AIzaSyD-OBmR-91OZt9VadJQb8X5GdisKjchOTU")
model = genai.GenerativeModel("gemini-2.5-flash")

class ImageAnalysis:
    def __init__(self):
        self.temp_dir = None

    def create_temp_directory(self):
        """Create a temporary directory for image processing"""
        if self.temp_dir:
            shutil.rmtree(self.temp_dir)
        self.temp_dir = tempfile.mkdtemp()
        return self.temp_dir

    def download_images(self, image_urls):
        """
        Download a list of image URLs into a temp folder.
        Returns list of local file paths.
        """
        temp_dir = self.create_temp_directory()
        local_files = []

        for idx, url in enumerate(image_urls, start=1):
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                file_ext = Path(url).suffix or ".jpg"
                local_path = os.path.join(temp_dir, f"image_{idx}{file_ext}")
                with open(local_path, "wb") as f:
                    shutil.copyfileobj(response.raw, f)
                local_files.append(local_path)
            else:
                print(f"⚠️ Failed to download {url}")
        return local_files

    def analyze_images(self, image_urls):
        """
        Analyze images using Gemini and return dict {url: extracted_text}.
        """
        local_files = self.download_images(image_urls)
        results = {}

        try:
            for url, file_path in zip(image_urls, local_files):
                mime_type, _ = guess_type(file_path)
                if not mime_type:
                    mime_type = "image/jpeg"  # fallback

                with open(file_path, "rb") as img_file:
                    image_bytes = img_file.read()

                response = model.generate_content(
                    [
                        image_prompt,
                        {
                            "mime_type": mime_type,
                            "data": image_bytes
                        }
                    ]
                )

                extracted_text = response.text.strip() if response.text else ""
                results[url] = extracted_text

            return results
        finally:
            if self.temp_dir:
                shutil.rmtree(self.temp_dir)
                self.temp_dir = None


# ✅ Example usage:
if __name__ == "__main__":
    image_urls = ['https://media.licdn.com/dms/image/v2/D5622AQEVAGH_EMG2hg/feedshare-shrink_1280/B56ZR5d7YRH0Ak-/0/1737204704376?e=1760572800&v=beta&t=di8h6ENrzB7pgxxD4AEpFxb6BrxC6ott4W9EFF63fUQ', 'https://media.licdn.com/dms/image/v2/D5622AQFJy1T1wXTQ7A/feedshare-shrink_2048_1536/B56ZR5d7W4GQAo-/0/1737204687465?e=1760572800&v=beta&t=JDJPPAyeaF650rF5_2Nmf0LG_AYJgNCzdr1MhkTvNrQ', 'https://media.licdn.com/dms/image/v2/D5622AQGq72VoiSicbQ/feedshare-shrink_2048_1536/B56ZR5d7XOHQAo-/0/1737204682297?e=1760572800&v=beta&t=ZaIFVXGYizL6uEjI7NnWH6XgtOpYevCuLn8U7eESL8c', 'https://media.licdn.com/dms/image/v2/D5622AQGaCsAB4sU4tg/feedshare-shrink_1280/B56ZR5d7XDHwAs-/0/1737204679511?e=1760572800&v=beta&t=kqvDBdpryMt65cDhY_No3VW9CIoNbXv_doTx1cFQbHQ', 'https://media.licdn.com/dms/image/v2/D5622AQHowxESGBfKhg/feedshare-shrink_1280/B56ZR5d7YVGsAk-/0/1737204719220?e=1760572800&v=beta&t=2qP0wfxbh33YR3lnCvZnCs_ZDk3WubDq2OqsPvQ9NzY', 'https://media.licdn.com/dms/image/v2/D5622AQHFGg8zmoxAWA/feedshare-shrink_1280/B56ZR5d7ZXHQAk-/0/1737204719372?e=1760572800&v=beta&t=f8qo4wVRDqI0vn2PxhvXGMeMVxbqAS2eWWclfwDb3AQ', 'https://media.licdn.com/dms/image/v2/D5622AQH_wZ3NmyKOww/feedshare-shrink_1280/B56ZR5d7XCHoAk-/0/1737204678730?e=1760572800&v=beta&t=UYFzT684Xgjkcc_00LHRR9CNcTwt3i5XxIFZXe0hVng', 'https://media.licdn.com/dms/image/v2/D5622AQE2tSU_ufP-bg/feedshare-shrink_2048_1536/B56ZR5d7ZFGoAo-/0/1737204679006?e=1760572800&v=beta&t=69fownPXSY2NvvHHrstCk54S7YeFEBPFTly1ns3kOQM', 'https://media.licdn.com/dms/image/v2/D5622AQEloCjs4kDR6Q/feedshare-shrink_2048_1536/B56ZR5d7WkGsAo-/0/1737204678811?e=1760572800&v=beta&t=p4POUju7Tqp_q3rDWY_Q7WgGJIbEDvYbagB8M47E62U']
    analyzer = ImageAnalysis()
    extracted_texts = analyzer.analyze_images(image_urls)
    for url, text in extracted_texts.items():
        print(f"\n🖼️ Image: {url}\n📜 Extracted Text: {text}\n")




