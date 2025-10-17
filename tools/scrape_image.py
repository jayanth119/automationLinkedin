import os
import requests
import asyncio
from playwright.async_api import async_playwright

class LinkedInImageScraper:
    def __init__(self, post_url, email, password, isdownload=False, images_folder="linkedin_post_images"):
        self.post_url = post_url
        self.email = email
        self.password = password
        self.isdownload = isdownload
        self.images_folder = images_folder
        os.makedirs(self.images_folder, exist_ok=True)

    async def _login(self, page):
        """Login to LinkedIn using provided credentials."""
        print("🔐 Logging into LinkedIn...")
        await page.goto("https://www.linkedin.com/login", timeout=60000)
        await page.wait_for_selector('input#username')

        await page.fill('input#username', self.email)
        await page.fill('input#password', self.password)
        await page.click('button[type="submit"]')

        # Wait for successful login redirect
        await page.wait_for_load_state('networkidle')
        if "feed" in page.url or "checkpoint" not in page.url:
            print("✅ Successfully logged into LinkedIn")
        else:
            print("⚠️ Login might have failed. Please check your credentials or 2FA status.")

    async def _download_image(self, url, idx):
        try:
            r = requests.get(url, timeout=10)
            path = os.path.join(self.images_folder, f"image_{idx}.jpg")
            with open(path, "wb") as f:
                f.write(r.content)
            print(f"✅ Saved {path}")
        except Exception as e:
            print(f"❌ Failed to download {url}: {e}")

    async def _scrape_images_from_post(self, page):
        await page.goto(self.post_url)
        await page.wait_for_timeout(4000)

        img_urls = []
        idx = 1

        overlay = await page.query_selector("div.update-components-image__container span")
        if overlay:
            await overlay.click()
        else:
            first_img = await page.query_selector("div.update-components-image__container img")
            if first_img:
                await first_img.click()
            else:
                print("❌ No image overlay or preview found.")
                return []

        await page.wait_for_timeout(2000)
        first_url = None

        while True:
            current_img = await page.query_selector("img.feed-shared-image-viewer__image")
            if not current_img:
                break

            src = await current_img.get_attribute("src")
            if src:
                if first_url is None:
                    first_url = src
                elif src == first_url:
                    break

                if src not in img_urls:
                    img_urls.append(src)
                    if self.isdownload:
                        await self._download_image(src, idx)
                    idx += 1

            next_btn = await page.query_selector("button.feed-shared-image-viewer__view-image-button--next")
            if not next_btn:
                break
            await next_btn.click()
            await page.wait_for_timeout(2000)

        print(f"🎉 Found {len(img_urls)} image(s) total.")
        return img_urls

    async def run(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            # Login using provided credentials
            await self._login(page)

            # Now scrape images from the post
            img_urls = await self._scrape_images_from_post(page)
            await browser.close()
            return img_urls


if __name__ == "__main__":
    POST_URL = "https://www.linkedin.com/feed/update/urn:li:activity:7286364713590894592/"
    EMAIL = "your_email@example.com"
    PASSWORD = "your_password"

    scraper = LinkedInImageScraper(
        post_url=POST_URL,
        email=EMAIL,
        password=PASSWORD,
        isdownload=True
    )

    output_path = asyncio.run(scraper.run())
    print(f"📂 Extracted image URLs: {output_path}")
