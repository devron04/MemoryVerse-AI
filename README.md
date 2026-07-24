# MemoryVerse AI

> Upload anything, ask anything, retrieve everything — and discover how every achievement connects to your journey and your next opportunity.

**MemoryVerse AI** is a Living Digital Identity System. Upload your certificates, resumes, project reports, and more — the system automatically categorizes them, connects them into a knowledge graph, and lets you retrieve anything with a natural-language query.

## Current Status: Phase 1 — Foundation & Ingestion Core

✅ Document upload (PDF, DOCX, images via OCR)  
✅ AI-powered extraction and categorization  
✅ Dashboard with categorized document cards  
🔲 Knowledge graph (Phase 2)  
🔲 Natural-language search (Phase 3)  
🔲 Career Intelligence Engine (Phase 4)  

## Quick Start

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Tesseract OCR** — [Install on Windows](https://github.com/UB-Mannheim/tesseract/wiki)
- **Gemini API Key** — [Get one from Google AI Studio](https://aistudio.google.com/)

### Backend Setup

```bash
cd memoryverse/backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy env file and add your API key
copy .env.example .env
# Edit .env with your GEMINI_API_KEY

# Start the server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd memoryverse/frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

The frontend runs at `http://localhost:5173`, the backend at `http://localhost:8000`.

### Tesseract OCR (for image uploads)

**Windows:** Download and install from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki).

If Tesseract isn't in your system PATH, set the `TESSERACT_CMD` environment variable in `.env`:
```
TESSERACT_CMD=C:/Program Files/Tesseract-OCR/tesseract.exe
```

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + TypeScript (Vite) |
| Backend | FastAPI (Python) |
| LLM | Gemini 2.5 Flash |
| OCR | Tesseract (pytesseract) |
| PDF Parsing | PyMuPDF |
| DOCX Parsing | python-docx |

## Project Structure

See [Architecture.md](Architecture.md) for full folder structure and technical decisions.
