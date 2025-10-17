import os
import asyncio
import uuid
import sys
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
from typing import TypedDict
import pandas as pd
from langgraph.graph import StateGraph

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.scrape_document import LinkedInDocumentScraper
from tools.imagetotext import ImageAnalysis
from tools.videototext import VideoAnalysis
from tools.scrape_image import LinkedInImageScraper
from tools.scrape_text import LinkedInTextExtractor
from tools.scrape_video import LinkedInVideoScraper
from tools.scrape_post import LinkedInPostExtractor
from tools.scrape_saved_posts import LinkedInSavedPostsScraper
from tools.classifypost import LinkedInPostClassifier
from prompts.documentprompt import document_prompt
from langchain_google_genai import ChatGoogleGenerativeAI
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import re

app = Flask(__name__)
OUTPUT_DIR = "outputs"
SESSIONS_DIR = os.path.join(OUTPUT_DIR, "sessions")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(SESSIONS_DIR, exist_ok=True)
CORS(app)

# Session storage
active_sessions = {}

# ==================== STATE MANAGEMENT ====================
class ExtractState(TypedDict, total=False):
    url: str
    email: str
    password: str
    text: str
    images: list
    documents: str
    videos: list
    notes: str
    saved_posts: list
    classified_posts: dict
    session_id: str

# ==================== UTILITY FUNCTIONS ====================
def clean_for_pdf(text: str) -> str:
    """Remove/replace HTML-like tags so ReportLab Paragraph doesn't crash."""
    text = text.replace("`", "")
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"<.*?>", "", text)
    text = text.replace("**", "").replace("*", "")
    return text.strip()

def markdown_to_story(text, styles):
    """Convert markdown to ReportLab story elements."""
    story = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            story.append(Spacer(1, 8))
            continue
        if line.startswith("# "):
            story.append(Paragraph(clean_for_pdf(line[2:]), styles["Heading1"]))
        elif line.startswith("## "):
            story.append(Paragraph(clean_for_pdf(line[3:]), styles["Heading2"]))
        elif line.startswith("- "):
            story.append(Paragraph("• " + clean_for_pdf(line[2:]), styles["Normal"]))
        elif re.match(r"^\d+\.", line):
            story.append(Paragraph(clean_for_pdf(line), styles["Normal"]))
        else:
            story.append(Paragraph(clean_for_pdf(line), styles["Normal"]))
    return story

def ensure_list(item):
    """Ensure the item is a list."""
    if isinstance(item, list):
        return item
    elif isinstance(item, str) and item.strip():
        return [item]
    else:
        return []

# ==================== LANGGRAPH NODES ====================
async def saved_posts_node(state: ExtractState):
    """Extract saved posts from LinkedIn."""
    try:
        email = state.get("email")
        password = state.get("password")

        if not email or not password:
            print("❌ Missing email or password in state")
            state["saved_posts"] = []
            return state

        print("🚀 Extracting saved posts...")
        scraper = LinkedInSavedPostsScraper(email, password)
        await asyncio.to_thread(scraper.run)

        if os.path.exists("linkedin_saved_posts.json"):
            with open("linkedin_saved_posts.json", "r", encoding="utf-8") as f:
                state["saved_posts"] = json.load(f)
            print(f"✅ Loaded {len(state['saved_posts'])} saved posts")
        else:
            state["saved_posts"] = []
            print("⚠️ No saved posts found")

    except Exception as e:
        print(f"❌ Saved posts extraction failed: {e}")
        state["saved_posts"] = []

    return state

async def classify_posts_node(state: ExtractState):
    """Classify saved posts."""
    try:
        posts = state.get("saved_posts", [])
        if not posts:
            print("⚠️ No saved posts to classify")
            state["classified_posts"] = {}
            return state

        print("🚀 Classifying saved posts...")
        classifier = LinkedInPostClassifier(posts)
        grouped_posts = await classifier.classify_all()

        classifier.save_to_excel("saved_posts_classified.xlsx")
        classifier.save_grouped_to_excel("saved_posts_grouped.xlsx")

        state["classified_posts"] = grouped_posts
        print("✅ Posts classified successfully")

    except Exception as e:
        print(f"❌ Classification failed: {e}")
        state["classified_posts"] = {}

    return state

async def text_scraper_node(state: ExtractState):
    """Extract text from LinkedIn post."""
    try:
        email = state.get("email")
        password = state.get("password")
        url = state.get("url")

        if not url:
            state["text"] = ""
            return state

        print("🚀 Extracting text...")
        extractor = LinkedInTextExtractor(url, email=email, password=password)
        post_text = await extractor.extract_text()
        state["text"] = post_text or ""

        if state["text"]:
            print("✅ Text extracted")
        else:
            print("⚠️ No text found")

    except Exception as e:
        print(f"❌ Text scraping failed: {e}")
        state["text"] = ""

    return state

async def image_ocr_node(state: ExtractState):
    """Extract and analyze images from LinkedIn post."""
    try:
        email = state.get("email")
        password = state.get("password")
        url = state.get("url")

        if not url:
            state["images"] = []
            return state

        print("🚀 Extracting images...")
        scraper = LinkedInImageScraper(post_url=url, email=email, password=password)
        output_path = await scraper.run()
        analyzer = ImageAnalysis()
        extracted_texts = analyzer.analyze_images(output_path)
        texts = [text for _, text in extracted_texts.items()]
        state["images"] = texts if texts else []

        if state["images"]:
            print(f"✅ {len(state['images'])} images extracted")
        else:
            print("⚠️ No images found")

    except Exception as e:
        print(f"❌ Image scraping failed: {e}")
        state["images"] = []

    return state

async def document_scraper_node(state: ExtractState):
    """Extract documents from LinkedIn post."""
    try:
        url = state.get("url")

        if not url:
            state["documents"] = ""
            return state

        print("🚀 Extracting documents...")
        scraper = LinkedInDocumentScraper(url)
        docs_text = await scraper.run(combine_pages=True)
        state["documents"] = docs_text or ""

        if state["documents"]:
            print("✅ Documents extracted")
        else:
            print("⚠️ No documents found")

    except Exception as e:
        print(f"❌ Document scraping failed: {e}")
        state["documents"] = ""

    return state

async def video_scraper_node(state: ExtractState):
    """Extract and analyze videos from LinkedIn post."""
    try:
        url = state.get("url")

        if not url:
            state["videos"] = []
            return state

        print("🚀 Extracting videos...")
        scraper = LinkedInVideoScraper(url)
        videos = await scraper.run()
        analyzer = VideoAnalysis()
        summaries = analyzer.analyze_video(videos)
        texts = [text for text in summaries]
        state["videos"] = texts or []

        if state["videos"]:
            print(f"✅ {len(state['videos'])} videos extracted")
        else:
            print("⚠️ No videos found")

    except Exception as e:
        print(f"❌ Video scraping failed: {e}")
        state["videos"] = []

    return state

async def post_extractor_node(state: ExtractState):
    """Extract all post data."""
    try:
        email = state.get("email")
        password = state.get("password")
        url = state.get("url")

        if not url:
            state["text"], state["images"], state["videos"], state["documents"] = "", [], [], []
            return state

        print("🚀 Extracting post data...")
        extractor = LinkedInPostExtractor(url, email=email, password=password)
        await extractor.run()

        state["text"] = extractor.data.get("text", "")
        state["images"] = extractor.data.get("images", [])
        state["videos"] = extractor.data.get("videos", [])
        state["documents"] = extractor.data.get("documents", [])

        print("✅ All post data extracted")

    except Exception as e:
        print(f"❌ Post extraction failed: {e}")
        state["text"], state["images"], state["videos"], state["documents"] = "", [], [], []

    return state

# ==================== LANGGRAPH COMPILATION ====================
def create_pipeline():
    """Create and compile the LangGraph pipeline."""
    graph = StateGraph(ExtractState)

    # Add nodes
    graph.add_node("saved_posts", saved_posts_node)
    graph.add_node("classify_posts", classify_posts_node)
    graph.add_node("post", post_extractor_node)
    graph.add_node("text", text_scraper_node)
    graph.add_node("image", image_ocr_node)
    graph.add_node("document", document_scraper_node)
    graph.add_node("video", video_scraper_node)

    # Add edges
    graph.add_edge("saved_posts", "classify_posts")
    graph.add_edge("classify_posts", "post")
    graph.add_edge("post", "text")
    graph.add_edge("text", "image")
    graph.add_edge("image", "document")
    graph.add_edge("document", "video")

    # Set entry and finish points
    graph.set_entry_point("saved_posts")
    graph.set_finish_point("video")

    return graph.compile()

# Create global pipeline
pipeline = create_pipeline()

# ==================== FLASK ENDPOINTS ====================
@app.route("/api/login", methods=["POST"])
def login():
    """Authenticate and create session."""
    try:
        data = request.json
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"error": "Missing email or password"}), 400

        session_id = str(uuid.uuid4())
        active_sessions[session_id] = {
            "email": email,
            "password": password,
            "created_at": datetime.now().isoformat(),
            "posts_processed": 0
        }

        session_file = os.path.join(SESSIONS_DIR, f"{session_id}.json")
        with open(session_file, "w") as f:
            json.dump(active_sessions[session_id], f)

        return jsonify({
            "message": "Login successful",
            "session_id": session_id,
            "email": email
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/verify-session", methods=["POST"])
def verify_session():
    """Verify session."""
    try:
        data = request.json
        session_id = data.get("session_id")

        if not session_id or session_id not in active_sessions:
            return jsonify({"error": "Invalid or expired session"}), 401

        session = active_sessions[session_id]
        return jsonify({
            "valid": True,
            "email": session["email"],
            "posts_processed": session["posts_processed"],
            "created_at": session["created_at"]
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/logout", methods=["POST"])
def logout():
    """Logout and destroy session."""
    try:
        data = request.json
        session_id = data.get("session_id")

        if session_id in active_sessions:
            del active_sessions[session_id]
            session_file = os.path.join(SESSIONS_DIR, f"{session_id}.json")
            if os.path.exists(session_file):
                os.remove(session_file)

        return jsonify({"message": "Logout successful"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/summarize", methods=["POST"])
async def summarize_post():
    """Summarize single LinkedIn post."""
    try:
        data = request.json
        session_id = data.get("session_id")
        post_url = data.get("url")
        save_format = data.get("format", "pdf").lower()

        if not session_id or session_id not in active_sessions:
            return jsonify({"error": "Invalid or expired session"}), 401

        if not post_url:
            return jsonify({"error": "Missing post URL"}), 400

        if save_format not in ["pdf", "excel"]:
            return jsonify({"error": "Format must be 'pdf' or 'excel'"}), 400

        session = active_sessions[session_id]
        post_id = str(uuid.uuid4())[:8]
        filename = f"notes_{post_id}"

        # Initialize state
        initial_state: ExtractState = {
            "url": post_url,
            "email": session["email"],
            "password": session["password"],
            "text": "",
            "images": [],
            "documents": "",
            "videos": [],
            "notes": "",
            "saved_posts": [],
            "classified_posts": {},
            "session_id": session_id
        }

        # Run pipeline
        print(f"🔄 Running pipeline for {post_url}")
        final_state = asyncio.run(pipeline.ainvoke(initial_state))

        # Combine extracted text
        combined_text = "\n\n".join(
            ensure_list(final_state.get("text", "")) +
            ensure_list(final_state.get("images", [])) +
            ensure_list(final_state.get("documents", "")) +
            ensure_list(final_state.get("videos", []))
        ).strip()

        if not combined_text:
            notes = f"Post {post_id}: No content available."
        else:
            combined_text = clean_for_pdf(combined_text)
            llm = ChatGoogleGenerativeAI(
                api_key="AIzaSyD-OBmR-91OZt9VadJQb8X5GdisKjchOTU",
                model="gemini-2.5-flash",
                temperature=0
            )
            prompt = document_prompt.format(
                post_id=post_id,
                combined_text=combined_text
            )
            resp = await llm.ainvoke(prompt)
            notes = clean_for_pdf(resp.content)

        # Save output
        output_content = f"# Post {post_id} Notes\n{notes}"

        if save_format == "pdf":
            pdf_file = os.path.join(OUTPUT_DIR, f"{filename}.pdf")
            doc = SimpleDocTemplate(pdf_file, pagesize=A4)
            styles = getSampleStyleSheet()
            story = [Paragraph("LinkedIn Post Summary", styles["Heading1"]), Spacer(1, 12)]
            story.extend(markdown_to_story(output_content, styles))
            doc.build(story)
        else:
            excel_file = os.path.join(OUTPUT_DIR, f"{filename}.xlsx")
            df = pd.DataFrame([{"Post ID": post_id, "Notes": notes}])
            df.to_excel(excel_file, index=False)

        session["posts_processed"] += 1
        return jsonify({
            "message": "Summary generated successfully",
            "download_link": f"/api/download/{filename}.{save_format}",
            "file_id": post_id,
            "format": save_format
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/download/<filename>", methods=["GET"])
def download_file(filename):
    """Download generated file."""
    try:
        file_path = os.path.join(OUTPUT_DIR, filename)

        if not os.path.abspath(file_path).startswith(os.path.abspath(OUTPUT_DIR)):
            return jsonify({"error": "Invalid file path"}), 403

        if not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 404

        return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "active_sessions": len(active_sessions),
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route("/", methods=["GET"])
def index():
    """Welcome endpoint."""
    return jsonify({
        "message": "LinkedIn Post Summarizer API with LangGraph",
        "version": "2.0",
        "endpoints": {
            "login": "POST /api/login",
            "verify_session": "POST /api/verify-session",
            "logout": "POST /api/logout",
            "summarize": "POST /api/summarize",
            "download": "GET /api/download/<filename>",
            "health": "GET /api/health"
        }
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)