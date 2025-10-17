import os
from playwright.async_api import async_playwright

SESSION_FILE = "linkedin_state.json"

class LinkedInSession:
    def __init__(self, session_file=SESSION_FILE):
        self.session_file = session_file
        self.context = None
        self.browser = None

    async def get_context(self):
        """Return a valid authenticated Playwright context"""
        if self.context:
            return self.context

        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)

        if os.path.exists(self.session_file) and os.path.getsize(self.session_file) > 0:
            print("✅ Using saved LinkedIn session.")
            self.context = await self.browser.new_context(storage_state=self.session_file)
        else:
            raise Exception("❌ No saved session found. Please log in once manually.")

        return self.context

    async def close(self):
        """Close browser and playwright properly"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
