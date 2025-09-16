import asyncio
import pandas as pd
from langgraph.graph import StateGraph
import os
import sys
import re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.scrape_document import LinkedInDocumentScraper
from tools.imagetotext import ImageAnalysis
from tools.videototext import VideoAnalysis
from tools.scrape_image import LinkedInImageScraper
from tools.scrape_text import LinkedInTextExtractor
from tools.scrape_video import LinkedInVideoScraper
from prompts.documentprompt import document_prompt
from state.state import ExtractState
from langchain_google_genai import ChatGoogleGenerativeAI
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


def clean_for_pdf(text: str) -> str:
    """Remove/replace HTML-like tags so ReportLab Paragraph doesn't crash."""
    text = text.replace("`", "")
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"<.*?>", "", text)
    text = text.replace("**", "").replace("*", "")
    return text.strip()


def markdown_to_story(text, styles):
    story = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            story.append(Spacer(1, 8))
            continue
        if line.startswith("# "):
            story.append(Paragraph(line[2:], styles["Heading1"]))
        elif line.startswith("## "):
            story.append(Paragraph(line[3:], styles["Heading2"]))
        elif line.startswith("- "):
            story.append(Paragraph("• " + line[2:], styles["Normal"]))
        elif re.match(r"^\d+\.", line):
            story.append(Paragraph(line, styles["Normal"]))
        else:
            story.append(Paragraph(line, styles["Normal"]))
    return story


def ensure_list(item):
    """Ensure the item is a list. Wrap string in list, or return empty list if None."""
    if isinstance(item, list):
        return item
    elif isinstance(item, str) and item.strip():
        return [item]
    else:
        return []

async def text_scraper(state: ExtractState):
    try:
        extractor = LinkedInTextExtractor(state.get("url"))
        post_text = await extractor.extract_text()
        state["text"] = post_text or ""
        if state["text"]:
            print("✅ Text extracted")
    except Exception as e:
        print(f"❌ Text scraping failed: {e}")
        state["text"] = ""
    return state


async def image_ocr(state: ExtractState):
    try:
        scraper = LinkedInImageScraper(post_url=state.get("url"))
        output_path = await scraper.run()
        analyzer = ImageAnalysis()
        extracted_texts = analyzer.analyze_images(output_path)
        texts = [text for _, text in extracted_texts.items()]
        state["images"] = texts if texts else []
        if state["images"]:
            print("✅ Image text extracted")
    except Exception as e:
        print(f"❌ Image scraping failed: {e}")
        state["images"] = []
    return state


async def document_scraper(state: dict):
    try:
        url = state.get("url")
        if not url:
            print("❌ No URL provided in state")
            state["documents"] = ""
            return state

        scraper = LinkedInDocumentScraper(url)
        docs_text = await scraper.run(combine_pages=True)

        state["documents"] = docs_text or ""
        if state["documents"]:
            print("✅ Document text extracted")
        else:
            print("ℹ️ No documents found for this post")
    except Exception as e:
        print(f"❌ Document scraping failed: {e}")
        state["documents"] = ""
    return state


async def video_scraper(state: ExtractState):
    try:
        scraper = LinkedInVideoScraper(state.get("url"))
        videos = await scraper.run()
        analyzer = VideoAnalysis()
        summaries = analyzer.analyze_video(videos)
        texts = [text for _, text in zip(videos, summaries)]
        state["videos"] = texts or []
        if state["videos"]:
            print("✅ Video text extracted")
    except Exception as e:
        print(f"❌ Video scraping failed: {e}")
        state["videos"] = []
    return state



graph = StateGraph(ExtractState)

graph.add_node("text", text_scraper)
graph.add_node("image", image_ocr)
graph.add_node("document", document_scraper)
graph.add_node("video", video_scraper)

graph.add_edge("text", "image")
graph.add_edge("image", "document")
graph.add_edge("document", "video")

graph.set_entry_point("text")
graph.set_finish_point("video")

pipeline = graph.compile()



async def run_pipeline_for_posts(posts, save_format="pdf", filename="combined_notes"):
    all_notes = []

    for post in posts:
        state: ExtractState = {
            "url": post.get("url"),
            "text": "",
            "images": [],
            "documents": "",
            "videos": [],
            "notes": "",
        }
        final_state = await pipeline.ainvoke(state)

        # Combine all text safely
        combined_text = "\n\n".join(
            ensure_list(final_state.get("text")) +
            ensure_list(final_state.get("images")) +
            ensure_list(final_state.get("documents")) +
            ensure_list(final_state.get("videos"))
        ).strip()

        if not combined_text:
            notes = f"Post {post.get('id')}: No content available."
        else:
            combined_text = clean_for_pdf(combined_text)
            llm = ChatGoogleGenerativeAI(
                api_key=" ",
                model="gemini-1.5-flash",
                temperature=0
            )
            prompt = document_prompt.format(
                post_id=post.get('id'),
                combined_text=combined_text
            )
            resp = await llm.ainvoke(prompt)
            notes = clean_for_pdf(resp.content)

        all_notes.append(f"# Post {post.get('id')} Notes\n{notes}")

    # Final combined notes
    combined_notes = "\n\n".join(all_notes)

    if save_format == "pdf":
        pdf_file = f"{filename}.pdf"
        doc = SimpleDocTemplate(pdf_file, pagesize=A4)
        styles = getSampleStyleSheet()
        story = [Paragraph("Combined Structured Notes", styles["Heading1"]), Spacer(1, 12)]
        story.extend(markdown_to_story(combined_notes, styles))
        doc.build(story)
        print(f"✅ Saved combined notes to {pdf_file}")

    elif save_format == "excel":
        excel_file = f"{filename}.xlsx"
        df = pd.DataFrame([{"Notes": combined_notes}])
        df.to_excel(excel_file, index=False)
        print(f"✅ Saved combined notes to {excel_file}")

    return combined_notes



if __name__ == "__main__":
    posts = [
        {"id": 1, "url": "https://www.linkedin.com/feed/update/urn:li:activity:7363079806671876097/"},
        
    ]
    asyncio.run(run_pipeline_for_posts(posts, save_format="pdf", filename="all_posts_notes"))
