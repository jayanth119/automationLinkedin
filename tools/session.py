import os
import json
from playwright.sync_api import sync_playwright

STORAGE_FILE = "linkedin_state.json"
EMAIL = "n200040@rguktn.ac.in"
PASSWORD = "HAKUNAmatata1@"

def login_and_save_state():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.linkedin.com/login")

        page.fill("input#username", EMAIL)
        page.fill("input#password", PASSWORD)
        page.click("button[type='submit']")
        page.wait_for_load_state("networkidle")
        # wait 60 seconds
        page.wait_for_timeout(60000)
        

        print("✅ Logged in successfully")
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
