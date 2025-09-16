import asyncio
import time
import requests
from playwright.async_api import async_playwright


class LinkedInVideoScraper:
    """
    Extract all video URLs from a given LinkedIn post URL and optionally download them.
    """

    def __init__(self, video_url, isdownload=False, output_path=".", headless=True):
        self.video_url = video_url
        self.headless = headless
        self.isdownload = isdownload
        self.video_srcs = []
        self.video_path = output_path

    async def _click_play_button(self, page):
        """Clicks the big play button if it exists."""
        try:
            await page.wait_for_selector('button.vjs-big-play-button', timeout=10000)
            await page.click('button.vjs-big-play-button')
            print("▶️ Play button clicked")
        except:
            print("❌ Play button not found or already clicked")

    async def _extract_video_srcs(self, page):
        """Extracts all video src URLs from the page."""
        try:
            self.video_srcs = await page.eval_on_selector_all(
                'video', 'els => els.map(el => el.src).filter(Boolean)'
            )
        except:
            self.video_srcs = []

    def download_video(self, url: str, filename: str = "linkedin_video.mp4"):
        """Download a video given its direct URL."""
        try:
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(filename, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            print(f"✅ Video downloaded successfully: {filename}")
        except Exception as e:
            print(f"❌ Error downloading video: {e}")

    async def run(self):
        """Main method to extract all video src URLs."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context()
            page = await context.new_page()

            print(f"🌍 Opening {self.video_url}...")
            await page.goto(self.video_url, timeout=60000, wait_until="domcontentloaded")

            await self._click_play_button(page)

            # Wait for video(s) to load
            await asyncio.sleep(3)

            await self._extract_video_srcs(page)
            await browser.close()

            # Optionally download videos
            downloaded = []
            if self.isdownload:
                import time
                for idx, url in enumerate(self.video_srcs):
                    file_name = f"{self.video_path}/linkedin_video_{idx}_{int(time.time())}.mp4"
                    self.download_video(url, file_name)
                    downloaded.append(file_name)

            return self.video_srcs


# ✅ Example usage
async def main():
    linkedin_video_url = "https://www.linkedin.com/feed/update/urn:li:activity:7369217237481656323/"
    scraper = LinkedInVideoScraper(linkedin_video_url, isdownload=False, headless=False)
    video_srcs = await scraper.run()
    print("Video src list:", video_srcs)


if __name__ == "__main__":
    asyncio.run(main())
