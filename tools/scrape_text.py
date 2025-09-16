import os
import time
import asyncio
from playwright.async_api import async_playwright

LINKEDIN_EMAIL = "N200040@rguktn.ac.in"
LINKEDIN_PASSWORD = "HAKUNAmatata1@"

class LinkedInTextExtractor:
    def __init__(self, url, state_file="linkedin_state.json"):
        self.url = url
        self.post_text = ""
        self.state_file = state_file

    async def extract_text(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)

            if os.path.exists(self.state_file):
                print("🔄 Using saved session")
                context = await browser.new_context(storage_state=self.state_file)
            else:
                context = await browser.new_context()
                print("📝 No saved session found")

            page = await context.new_page()
            await self._handle_authentication(context, page)

            try:
                await page.goto(self.url, wait_until="domcontentloaded")
                print("📄 Page loaded, extracting text...")
                await self._extract_text(page)
            except Exception as e:
                print(f"❌ Error extracting text: {e}")
            finally:
                await browser.close()

        return self.post_text

    async def _handle_authentication(self, context, page):
        await page.goto("https://www.linkedin.com/feed/")
        if "login" in page.url or "challenge" in page.url:
            print("❌ Session expired, performing login...")
            await self._login(page)
            await self._save_state(context)
        else:
            print("✅ Session valid")

    async def _save_state(self, context):
        await context.storage_state(path=self.state_file)
        print("💾 Session saved")

    async def _login(self, page):
        await page.goto("https://www.linkedin.com/login")
        await page.fill("input#username", LINKEDIN_EMAIL)
        await page.fill("input#password", LINKEDIN_PASSWORD)
        await page.click("button[type='submit']")
        await asyncio.sleep(5)

    async def _extract_text(self, page):
        selectors = [
            'div.update-components-text.update-components-update-v2__commentary',
            'div.feed-shared-text',
            '[data-test-id="main-feed-activity-card"] .feed-shared-inline-show-more-text'
        ]
        for sel in selectors:
            el = await page.query_selector(sel)
            if el:
                self.post_text = (await el.inner_text()).strip()
                print(f"✅ Text extracted using selector: {sel}")
                break
        if not self.post_text:
            print("❌ No text found")

if __name__ == "__main__":
    linkedin_url = "https://www.linkedin.com/feed/update/urn:li:activity:7369217237481656323/"
    text_extractor = LinkedInTextExtractor(linkedin_url)
    
    post_text = asyncio.run(text_extractor.extract_text())
    print(post_text)
