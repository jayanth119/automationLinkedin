import os
import asyncio
import pandas as pd
from tools.scrape_document import LinkedInDocumentScraper
from tools.scrape_image import LinkedInImageScraper  
from tools.scrape_text import LinkedInTextExtractor  
from tools.scrape_video import  LinkedInVideoScraper

class LinkedInPostExtractor:
    def __init__(self, url, email, password, state_file="linkedin_state.json", output_folder="linkedin_post_data"):
        self.url = url
        self.email = email
        self.password = password
        self.state_file = state_file
        self.output_folder = output_folder
        os.makedirs(self.output_folder, exist_ok=True)
        self.data = {"url": url, "text": "", "images": [], "videos": [], "documents": []}

    async def run(self):
        # Extract documents (sync)
        pdf_path = os.path.join(self.output_folder, "linkedin_document.pdf")
        document_scraper = LinkedInDocumentScraper(self.url, pdf_path)
        doc = await document_scraper.run()
        if doc:
            self.data["documents"].append(self.output_folder)
            

        # Extract text
        text_extractor = LinkedInTextExtractor(self.url)
        self.data["text"] = await text_extractor.extract_text()

        # Extract images
        image_scraper = LinkedInImageScraper(post_url=self.url, images_folder=self.output_folder)
        images = await image_scraper.run()
        if images:
            self.data["images"].extend(images)

        # Extract video (sync)
        loop = asyncio.get_event_loop()
        video_src = await loop.run_in_executor(None, lambda: LinkedInVideoScraper(self.url, headless=True).run())
        if video_src:
            self.data["videos"].append(video_src)

        # Save metadata
        self._save_metadata()

    def _save_metadata(self):
        csv_path = os.path.join(self.output_folder, "post_data.csv")
        rows = []

        if self.data["text"]:
            rows.append({"type": "text", "value": self.data["text"]})
        rows.extend([{"type": "image", "value": img} for img in self.data["images"]])
        rows.extend([{"type": "video", "value": v} for v in self.data["videos"]])
        rows.extend([{"type": "document", "value": d} for d in self.data["documents"]])

        df = pd.DataFrame(rows)
        df.to_csv(csv_path, index=False, encoding="utf-8")
        print(f"💾 Metadata saved in {csv_path}")

# Run the async extractor
if __name__ == "__main__":
    url = "https://www.linkedin.com/feed/update/urn:li:activity:7372869654186405889/"
    extractor = LinkedInPostExtractor(url, "N200040@rguktn.ac.in", "HAKUNAmatata1@")
    
    if asyncio.get_event_loop().is_running():
        asyncio.create_task(extractor.run())
    else:
        asyncio.run(extractor.run())