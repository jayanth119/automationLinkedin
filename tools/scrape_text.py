import asyncio
from playwright.async_api import async_playwright

LINKEDIN_EMAIL = "N200040@rguktn.ac.in"
LINKEDIN_PASSWORD = " "

class LinkedInTextExtractor:
    def __init__(self, url, email, password):
        self.url = url
        self.post_text = ""
        self.email = email
        self.password = password

    async def extract_text(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # Set to True for production
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            page = await context.new_page()

            try:
                # Perform login
                await self._login(page)
                
                # Navigate to the post URL
                print(f"🌐 Navigating to post: {self.url}")
                await page.goto(self.url, wait_until="domcontentloaded", timeout=30000)
                
                # Wait a bit for dynamic content to load
                await asyncio.sleep(2)
                
                print("📄 Page loaded, extracting text...")
                
                # Extract text
                await self._extract_text(page)
                
            except Exception as e:
                print(f"❌ Error extracting text: {e}")
                import traceback
                traceback.print_exc()
            finally:
                await browser.close()

        return self.post_text

    async def _login(self, page):
        """Login to LinkedIn"""
        try:
            print("🔐 Logging into LinkedIn...")
            await page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
            
            # Wait for login form
            await page.wait_for_selector("input#username", timeout=5000)
            
            # Fill login credentials
            await page.fill("input#username", self.email)
            await page.fill("input#password", self.password)
            
            # Click submit
            await page.click("button[type='submit']")
            
            # Wait for navigation by checking URL change or feed page element
            try:
                # Wait for either feed page or profile redirect
                await page.wait_for_url("**/feed/**", timeout=15000)
                print("✅ Logged in successfully - redirected to feed")
            except:
                # Alternative: wait for a feed element
                await page.wait_for_selector('[data-test-id="main-feed-activity-card"]', timeout=15000)
                print("✅ Logged in successfully - feed loaded")
            
        except Exception as e:
            print(f"❌ Login failed: {e}")
            # Take screenshot for debugging
            await page.screenshot(path="login_error.png")
            print("📸 Screenshot saved as login_error.png")
            raise

    async def _extract_text(self, page):
        """Extract text from LinkedIn post using multiple selectors"""
        
        # First, try to click "See more" button if it exists
        try:
            see_more = await page.query_selector('button.feed-shared-inline-show-more-text__see-more-less-toggle')
            if see_more:
                await see_more.click()
                await asyncio.sleep(1)
                print("👁️ Expanded 'See more' text")
        except:
            pass
        
        selectors = [
            # Most common selectors for LinkedIn posts
            'div.feed-shared-update-v2__description',
            'div.update-components-text',
            'span.break-words',
            'div.feed-shared-text',
            'div.feed-shared-inline-show-more-text',
            '[data-test-id="main-feed-activity-card"] div.feed-shared-text',
            'div.update-components-text.update-components-update-v2__commentary',
            '[data-test-id="main-feed-activity-card"] .feed-shared-inline-show-more-text',
            'div.feed-shared-update-v2__description-wrapper',
        ]
        
        for sel in selectors:
            try:
                el = await page.query_selector(sel)
                if el:
                    text = await el.inner_text()
                    if text and text.strip():
                        self.post_text = text.strip()
                        print(f"✅ Text extracted using selector: {sel}")
                        return
            except Exception as e:
                continue
        
        # If no text found, try getting all text from the activity card
        if not self.post_text:
            try:
                print("⚠️ Trying fallback method...")
                activity_card = await page.query_selector('[data-test-id="main-feed-activity-card"]')
                if activity_card:
                    # Get all text but filter out common UI elements
                    all_text = await activity_card.inner_text()
                    # Basic cleanup - remove common button texts
                    unwanted = ['Like', 'Comment', 'Repost', 'Send', 'Follow', 'Connect']
                    lines = [line.strip() for line in all_text.split('\n') if line.strip()]
                    lines = [line for line in lines if line not in unwanted and len(line) > 10]
                    if lines:
                        self.post_text = '\n'.join(lines)
                        print("✅ Text extracted using fallback method")
                        return
            except:
                pass
        
        if not self.post_text:
            print("❌ No text found with any selector")
            # Save page content for debugging
            content = await page.content()
            with open("page_debug.html", "w", encoding="utf-8") as f:
                f.write(content)
            print("📄 Page HTML saved to page_debug.html for debugging")

if __name__ == "__main__":
    linkedin_url = "https://www.linkedin.com/feed/update/urn:li:activity:7369217237481656323/"
    text_extractor = LinkedInTextExtractor(linkedin_url, LINKEDIN_EMAIL, LINKEDIN_PASSWORD)
    
    post_text = asyncio.run(text_extractor.extract_text())
    print("\n" + "="*50)
    print("EXTRACTED TEXT:")
    print("="*50)
    print(post_text if post_text else "No text found")
    print("="*50)