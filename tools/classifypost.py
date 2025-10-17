import asyncio
import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
import os 
import sys 
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.scrape_text import LinkedInTextExtractor
from prompts.classifyprompt import classify_prompt   

class LinkedInPostClassifier:
    def __init__(self, posts, model="gemini-2.5-flash"):
        self.posts = posts
        self.llm = ChatGoogleGenerativeAI(
            model=model , 
            api_key="AIzaSyD-OBmR-91OZt9VadJQb8X5GdisKjchOTU"  )
        self.prompt = ChatPromptTemplate.from_template(classify_prompt)
        self.results = []

    async def process_post(self, post):
        scraper = LinkedInTextExtractor(post["url"])
        text = await scraper.extract_text()
        
        text = text[:2000] if text else "No content found."

        chain = self.prompt | self.llm
        topic = await chain.ainvoke({"content": text})
        topic_name = topic.content.strip()

        result = {
            "id": post["id"],
            "urn": post["urn"],
            "url": post["url"],
            "description": text[:300],
            "topic": topic_name
        }
        self.results.append(result)

    async def classify_all(self):
        for post in self.posts:
            await self.process_post(post)
        return self.group_by_topic()

    def group_by_topic(self):
        grouped = {}
        for r in self.results:
            grouped.setdefault(r["topic"], []).append(r)
        return grouped

    def save_to_excel(self, filename="classified_posts.xlsx"):
        df = pd.DataFrame(self.results)
        df.to_excel(filename, index=False)
        print(f"✅ Results saved to {filename}")

    def save_grouped_to_excel(self, filename="grouped_posts.xlsx"):
        """Save grouped topics into one sheet per topic"""
        grouped = self.group_by_topic()
        with pd.ExcelWriter(filename) as writer:
            for topic, posts in grouped.items():
                df = pd.DataFrame(posts)
                df.to_excel(writer, sheet_name=topic[:30], index=False)
        print(f"✅ Grouped results saved to {filename}")


# Example usage
saved_posts = [
    {"id": 1, "urn": "urn:li:activity:7369094910425124867", "url": "https://www.linkedin.com/feed/update/urn:li:activity:7369094910425124867/"},
    {"id": 2, "urn": "urn:li:activity:7372869654186405889", "url": "https://www.linkedin.com/feed/update/urn:li:activity:7372869654186405889/"},
    {"id": 3, "urn": "urn:li:activity:7331292413484826625", "url": "https://www.linkedin.com/feed/update/urn:li:activity:7331292413484826625/"},
    {"id": 4, "urn": "urn:li:activity:7319825593749893120", "url": "https://www.linkedin.com/feed/update/urn:li:activity:7319825593749893120/"},
    {"id": 5, "urn": "urn:li:activity:7257979467673858049", "url": "https://www.linkedin.com/feed/update/urn:li:activity:7257979467673858049/"},
    {"id": 6, "urn": "urn:li:activity:7255817329404436480", "url": "https://www.linkedin.com/feed/update/urn:li:activity:7255817329404436480/"},
    {"id": 7, "urn": "urn:li:activity:7180268569799135232", "url": "https://www.linkedin.com/feed/update/urn:li:activity:7180268569799135232/"},
    {"id": 8, "urn": "urn:li:activity:7057926297695498240", "url": "https://www.linkedin.com/feed/update/urn:li:activity:7057926297695498240/"}
]

async def main():

    classifier = LinkedInPostClassifier(saved_posts)
    grouped = await classifier.classify_all()

    # Save flat results
    classifier.save_to_excel()

    # Save grouped by topic (one sheet per topic)
    classifier.save_grouped_to_excel()

    # Print grouping summary
    for topic, posts in grouped.items():
        print(f"\n📌 Topic: {topic}")
        for p in posts:
            print(f"   - {p['url']}")

if __name__ == "__main__":
    asyncio.run(main())
