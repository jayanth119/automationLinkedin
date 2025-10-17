import asyncio
from playwright.async_api import async_playwright

class LinkedInPostExtractor:
    """
    Unified extractor for all LinkedIn post content types
    """
    def __init__(self, url, email, password):
        self.url = url
        self.email = email
        self.password = password
        self.data = {
            "text": "",
            "images": [],
            "videos": [],
            "documents": ""
        }

    async def run(self):
        """Extract all content from the LinkedIn post"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            page = await context.new_page()

            try:
                # Login
                await self._login(page)
                
                # Navigate to post
                print(f"🌍 Opening {self.url}...")
                await page.goto(self.url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(2)

                # Extract all content types
                await self._extract_text(page)
                await self._extract_images(page)
                await self._extract_videos(page)
                await self._extract_documents(page)

                print("✅ Post extraction completed")

            except Exception as e:
                print(f"❌ Post extraction failed: {e}")
                import traceback
                traceback.print_exc()
            finally:
                await browser.close()

        return self.data

    async def _login(self, page):
        """Login to LinkedIn"""
        try:
            print("🔐 Logging into LinkedIn...")
            await page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
            
            await page.wait_for_selector("input#username", timeout=5000)
            await page.fill("input#username", self.email)
            await page.fill("input#password", self.password)
            await page.click("button[type='submit']")
            
            try:
                await page.wait_for_url("**/feed/**", timeout=15000)
                print("✅ Logged in successfully")
            except:
                await page.wait_for_selector('[data-test-id="main-feed-activity-card"]', timeout=15000)
                print("✅ Logged in successfully")
                
        except Exception as e:
            print(f"❌ Login failed: {e}")
            raise

    async def _extract_text(self, page):
        """Extract text content from the post"""
        try:
            # Try to expand "See more" if present
            see_more = await page.query_selector('button.feed-shared-inline-show-more-text__see-more-less-toggle')
            if see_more:
                await see_more.click()
                await asyncio.sleep(0.5)

            selectors = [
                'div.feed-shared-update-v2__description',
                'div.update-components-text',
                'span.break-words',
                'div.feed-shared-text',
                'div.feed-shared-inline-show-more-text',
            ]

            for sel in selectors:
                el = await page.query_selector(sel)
                if el:
                    text = await el.inner_text()
                    if text and text.strip():
                        self.data["text"] = text.strip()
                        print(f"✅ Text extracted")
                        return

            print("⚠️ No text found")

        except Exception as e:
            print(f"⚠️ Text extraction error: {e}")

    async def _extract_images(self, page):
        """Extract images from the post"""
        try:
            image_selectors = [
                'img.feed-shared-image__image',
                'img[class*="ivm-view-attr__img"]',
                'div.feed-shared-update-v2__content img'
            ]

            images = []
            for sel in image_selectors:
                elements = await page.query_selector_all(sel)
                for el in elements:
                    src = await el.get_attribute('src')
                    if src and 'media.licdn.com' in src:
                        images.append(src)

            self.data["images"] = list(set(images))  # Remove duplicates
            
            if self.data["images"]:
                print(f"✅ Found {len(self.data['images'])} images")
            else:
                print("⚠️ No images found")

        except Exception as e:
            print(f"⚠️ Image extraction error: {e}")

    async def _extract_videos(self, page):
        """Extract videos from the post"""
        try:
            # Try to find video elements
            video_selectors = [
                'video',
                'div[class*="feed-shared-external-video"]',
                'div[data-test-id="video-player"]'
            ]

            videos = []
            for sel in video_selectors:
                elements = await page.query_selector_all(sel)
                for el in elements:
                    # Try to get video source
                    src = await el.get_attribute('src')
                    if src:
                        videos.append(src)
                    else:
                        # Check for source tag inside video
                        source = await el.query_selector('source')
                        if source:
                            src = await source.get_attribute('src')
                            if src:
                                videos.append(src)

            self.data["videos"] = list(set(videos))
            
            if self.data["videos"]:
                print(f"✅ Found {len(self.data['videos'])} videos")
            else:
                print("⚠️ No videos found")

        except Exception as e:
            print(f"⚠️ Video extraction error: {e}")

    async def _extract_documents(self, page):
        """Extract document content from the post"""
        try:
            # Look for document iframes
            doc_iframe = await page.query_selector('iframe[data-id="feed-paginated-document-content"]')
            
            if not doc_iframe:
                print("ℹ️ No document iframe found")
                return

            # Switch to iframe and extract text
            frame = await doc_iframe.content_frame()
            if frame:
                doc_text = await frame.inner_text('body')
                if doc_text and doc_text.strip():
                    self.data["documents"] = doc_text.strip()
                    print("✅ Document text extracted")
                else:
                    print("⚠️ Document iframe found but empty")
            else:
                print("⚠️ Could not access document iframe content")

        except Exception as e:
            print(f"ℹ️ No document found or timeout: {e}")


if __name__ == "__main__":
    # Test the extractor
    from scrape_text import LINKEDIN_EMAIL, LINKEDIN_PASSWORD
    
    test_url = "https://www.linkedin.com/feed/update/urn:li:activity:7319825593749893120/"
    
    extractor = LinkedInPostExtractor(test_url, LINKEDIN_EMAIL, LINKEDIN_PASSWORD)
    data = asyncio.run(extractor.run())
    
    print("\n" + "="*50)
    print("EXTRACTION RESULTS:")
    print("="*50)
    print(f"\nText: {data['text'][:200] if data['text'] else 'None'}...")
    print(f"Images: {len(data['images'])} found")
    print(f"Videos: {len(data['videos'])} found")
    print(f"Documents: {'Yes' if data['documents'] else 'No'}")
    print("="*50)