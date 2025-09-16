import json
import requests
from playwright.async_api import async_playwright
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from PIL import Image
import pytesseract
import os
import shutil
import time

class LinkedInDocumentScraper:
    def __init__(self, post_url, isdownload = False ,output_dir="linkedin_documents"):
        self.post_url = post_url
        self.output_dir = output_dir
        self.isdownload = isdownload
        self.images_folder = "pages"
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.images_folder, exist_ok=True)
        self.generated_pdfs = []  # store list of pdf paths

    async def _fetch_manifest(self, page):
        try:
            iframe_elem = await page.wait_for_selector(
                'iframe[data-id="feed-paginated-document-content"], iframe[class*="document"], iframe[data-test-id="document-container"]',
                timeout=5000
            )
            iframe_json = await iframe_elem.get_attribute("data-native-document-config")

            if not iframe_json:
                print("⚠️ Could not find document config JSON in iframe")
                return None

            try:
                config = json.loads(iframe_json)
            except Exception as e:
                print(f"⚠️ Failed to parse iframe JSON: {e}")
                return None

            doc = config.get("doc", {})
            manifest_url = doc.get("manifestUrl")
            if not manifest_url:
                print("⚠️ No manifestUrl found in document config")
                return None

            return manifest_url.replace("&amp;", "&")

        except Exception as e:
            print(f"ℹ️ No document iframe found or timeout: {e}")
            return None

    def _fetch_image_pages(self, manifest_url):
        print(f"📑 Fetching manifest: {manifest_url}")
        manifest = requests.get(manifest_url).json()
        per_resolutions = manifest.get("perResolutions", [])
        if not per_resolutions:
            print("⚠️ No perResolutions found in manifest")
            return []

        per_resolutions = sorted(per_resolutions, key=lambda x: x.get("width", 0), reverse=True)
        image_manifest_url = per_resolutions[0].get("imageManifestUrl")

        if not image_manifest_url:
            print("⚠️ No imageManifestUrl found")
            return []

        print(f"🖼 Fetching image manifest: {image_manifest_url}")
        image_manifest = requests.get(image_manifest_url).json()
        return image_manifest.get("pages", [])

    def _save_pdf(self, pages):
        timestamp = int(time.time())
        output_pdf = os.path.join(self.output_dir, f"linkedin_document_{timestamp}.pdf")
        c = canvas.Canvas(output_pdf, pagesize=A4)
        a4_width, a4_height = A4

        for idx, img_url in enumerate(pages, start=1):
            print(f"📄 Downloading page {idx}/{len(pages)}: {img_url}")
            img_data = requests.get(img_url).content
            img_path = os.path.join(self.images_folder, f"page_{idx}.jpg")
            with open(img_path, "wb") as f:
                f.write(img_data)

            img = Image.open(img_path)
            img_width, img_height = img.size
            ratio = min(a4_width / img_width, a4_height / img_height)
            new_width = img_width * ratio
            new_height = img_height * ratio
            x = (a4_width - new_width) / 2
            y = (a4_height - new_height) / 2

            c.drawImage(ImageReader(img), x, y, new_width, new_height)
            c.showPage()

        c.save()
        self.generated_pdfs.append(output_pdf)
        print(f"🎉 Document saved as {output_pdf} with {len(pages)} pages!")
        return output_pdf

    def extract_text_from_images(self, pages):
        """Use OCR to extract text from downloaded page images"""
        ocr_texts = []
        for idx, img_url in enumerate(pages, start=1):
            img_path = os.path.join(self.images_folder, f"page_{idx}.jpg")
            if not os.path.exists(img_path):
                img_data = requests.get(img_url).content
                with open(img_path, "wb") as f:
                    f.write(img_data)
            text = pytesseract.image_to_string(Image.open(img_path))
            ocr_texts.append(text)
        return ocr_texts

    async def run(self, combine_pages=True):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            print(f"🌍 Opening {self.post_url}...")
            await page.goto(self.post_url, timeout=60000, wait_until="domcontentloaded")

            manifest_url = await self._fetch_manifest(page)
            if not manifest_url:
                await browser.close()
                return "" if combine_pages else []

            pages = self._fetch_image_pages(manifest_url)
            if not pages:
                print("⚠️ No pages found.")
                await browser.close()
                return "" if combine_pages else []
            if(self.isdownload):
                self._save_pdf(pages)

            # Extract text via OCR
            pdf_texts = self.extract_text_from_images(pages)

            # Cleanup temp image folder
            if os.path.exists(self.images_folder):
                shutil.rmtree(self.images_folder)

            await browser.close()
            
            if combine_pages:
                return " ".join(pdf_texts)  # return single combined string
            return pdf_texts  # return list per page



# Example usage
import asyncio

async def main():
    linkedin_post_url = "https://www.linkedin.com/feed/update/urn:li:activity:7363079806671876097/"
    scraper = LinkedInDocumentScraper(linkedin_post_url)
    full_text = await scraper.run()
    print(full_text[:1000])  


if __name__ == "__main__":
    asyncio.run(main())
