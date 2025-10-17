import os
from playwright.sync_api import sync_playwright

STORAGE_FILE = "linkedin_state.json"
EMAIL = "n200040@rguktn.ac.in"
PASSWORD = " "


def login_and_save_state():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.linkedin.com/login")

        # Fill login form
        page.fill("input#username", EMAIL)
        page.fill("input#password", PASSWORD)
        page.click("button[type='submit']")

        try:
            # ✅ Wait for a known element that means login succeeded
            page.goto("https://www.linkedin.com/feed/")
            print("✅ Logged in successfully")
        except Exception:
            # ⚠️ Fallback: LinkedIn may ask for OTP / Captcha
            print("⚠️ Could not auto-detect login success. If OTP/Captcha is required, solve it manually.")
            input("👉 After finishing login in the browser, press Enter here...")

        # Save session state
        context.storage_state(path=STORAGE_FILE)
        print(f"💾 Session saved to {STORAGE_FILE}")

        browser.close()


def use_saved_session():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=STORAGE_FILE)
        page = context.new_page()
        page.goto("https://www.linkedin.com/feed/")
        print("✅ Opened LinkedIn with saved session")
        input("Press Enter to close...")
        browser.close()


if __name__ == "__main__":
    if not os.path.exists(STORAGE_FILE) or os.path.getsize(STORAGE_FILE) == 0:
        login_and_save_state()
    else:
        use_saved_session()
