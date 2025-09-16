# 📄 LinkedIn Content Scraper & Analyzer

This project automates the process of extracting **documents, images, videos, and text** from LinkedIn posts. It converts them into **structured PDFs** and integrates with an **AI-powered pipeline** for further analysis.

The system uses **Playwright** for LinkedIn scraping, **PyMuPDF & OCR** for document parsing, and **LangGraph** for pipeline orchestration.

---

## 🚀 Features

* ✅ Scrape LinkedIn posts for **documents, images, videos, text**
* ✅ Extract & format **multi-page PDFs**
* ✅ OCR support for scanned/embedded text
* ✅ AI-powered **text & video analysis**
* ✅ Modular **LangGraph pipeline**
* ✅ Error handling & retry logic

---

## 📂 Project Structure

```
project-root/
│── tools/
│   ├── scrape_document.py   # LinkedIn Document Scraper
│   ├── scrape_image.py      # Image Scraper
│   ├── scrape_text.py       # Text Scraper
│   ├── videototext.py       # Video frame + OCR pipeline
│   ├── imagetotext.py       # OCR for images
│
│── pipeline/
│   ├── extractor.py         # LangGraph pipeline definition
│
│── output/
│   ├── *.pdf                # Generated PDFs
│
│── README.md
│── requirements.txt
```

---

## ⚙️ Installation

### 1️⃣ Clone the repo

```bash
git clone https://github.com/jayanth119/automationLinkedin.git
cd automationLinkedin
```

### 2️⃣ Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows
```

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Install Playwright browsers

```bash
playwright install
```

---

## 🚀 Usage

Run the LinkedIn pipeline:

```bash
python main.py
```

Or use the **LangGraph pipeline** for AI-powered extraction:

```python
import asyncio
from pipeline.extractor import run_pipeline

asyncio.run(run_pipeline("https://www.linkedin.com/feed/update/..."))
```

---

## 🧩 Tech Stack

* **Python 3.10+**
* **Playwright** – Web scraping
* **ReportLab** – PDF generation
* **PyMuPDF / OCR** – Text extraction
* **LangGraph** – Pipeline orchestration
* **Pandas** – Data handling
* **PIL / OpenCV** – Image & video processing

---

## 📊 Software Diagrams (Mermaid)

### 1. System Flow

```mermaid
flowchart TD
    A[LinkedIn Post URL] --> B{Content Type?}
    B -->|Document| C[Scrape Document]
    B -->|Image| D[Scrape Image]
    B -->|Video| E[Extract Video Frames + OCR]
    B -->|Text| F[Extract Post Text]
    C --> G[PDF Generator]
    D --> G
    E --> G
    F --> G
    G --> H[AI Analysis Pipeline]
    H --> I[Final Structured Report]
```

---

### 2. Sequence of Operations

```mermaid
sequenceDiagram
    participant User
    participant Scraper
    participant PDFGen
    participant Pipeline
    User->>Scraper: Provide LinkedIn URL
    Scraper->>Scraper: Identify content type
    Scraper->>PDFGen: Save extracted content as PDF
    PDFGen->>Pipeline: Send PDFs for AI analysis
    Pipeline-->>User: Return insights
```

---

### 3. Architecture

```mermaid
graph TD
    subgraph Client
        U[User Input]
    end

    subgraph Backend
        S1[Playwright Scraper]
        S2[OCR / PyMuPDF]
        S3[PDF Generator]
        S4[LangGraph Pipeline]
    end

    subgraph Storage
        O[Output PDFs]
    end

    U --> S1
    S1 --> S2
    S2 --> S3
    S3 --> O
    S3 --> S4
    S4 --> U
```

---

### 4. Data Pipeline

```mermaid
graph LR
    URL[LinkedIn URL] --> DETECT{Detect Content Type}
    DETECT --> DOC[Document Scraper]
    DETECT --> IMG[Image Scraper]
    DETECT --> VID[Video Analyzer]
    DETECT --> TXT[Text Scraper]
    DOC --> PDF
    IMG --> PDF
    VID --> PDF
    TXT --> PDF
    PDF --> ANALYZE[AI Analysis]
    ANALYZE --> REPORT[Final Report]
```

---

## 📌 Future Enhancements

* [ ] Support for **LinkedIn Carousel Posts**
* [ ] Deploy as **FastAPI service**
* [ ] Add **Extention** for reports
* [ ] Extend support for **Twitter & Medium scraping**

---

✨ Built with passion by \[Jayanth chukka] 🚀


