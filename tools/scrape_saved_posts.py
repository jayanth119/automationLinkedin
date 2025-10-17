import os
import json
import csv
from playwright.sync_api import sync_playwright

class LinkedInSavedPostsScraper:
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.posts_data = []

    def login(self, page):
        print("🔑 Logging into LinkedIn...")
        page.goto("https://www.linkedin.com/login")
        page.fill("input#username", self.email)
        page.fill("input#password", self.password)
        page.click("button[type=submit]")
        page.wait_for_selector("input[placeholder='Search']", timeout=60000)
        print("✅ Logged in!")

    def open_saved_posts(self, page):
        print("📂 Opening Saved Posts...")
        page.goto("https://www.linkedin.com/my-items/saved-posts/")
        page.wait_for_selector("[data-chameleon-result-urn]", timeout=60000)

        # Scroll to load more posts
        for _ in range(10):
            page.mouse.wheel(0, 3000)
            page.wait_for_timeout(2000)

    def extract_posts(self, page):
        print("📌 Extracting saved posts...")
        posts = page.query_selector_all("[data-chameleon-result-urn]")

        for i, post in enumerate(posts, start=1):
            urn = post.get_attribute("data-chameleon-result-urn")
            post_url = f"https://www.linkedin.com/feed/update/{urn}/" if urn and "urn:li:activity" in urn else ""
            self.posts_data.append({
                "id": i,
                "urn": urn,
                "url": post_url
            })

        print(f"✅ Extracted {len(self.posts_data)} saved posts")

    def save_data(self, json_file="linkedin_saved_posts.json", csv_file="linkedin_saved_posts.csv"):
        # Save JSON
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(self.posts_data, f, ensure_ascii=False, indent=4)

        # Save CSV
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "urn", "url"])
            writer.writeheader()
            for row in self.posts_data:
                writer.writerow(row)

        print(f"💾 Data saved to {json_file} & {csv_file}")

    def run(self):
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()

            self.login(page)
            self.open_saved_posts(page)
            self.extract_posts(page)
            self.save_data()

            browser.close()


if __name__ == "__main__":
    LINKEDIN_EMAIL = "N200040@rguktn.ac.in"
    LINKEDIN_PASSWORD = " "

    scraper = LinkedInSavedPostsScraper(LINKEDIN_EMAIL, LINKEDIN_PASSWORD)
    scraper.run()
