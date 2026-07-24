# Architecture.md — MemoryVerse AI

## 1. App Flow (High Level)

```
User Upload (file or URL)
    ↓
OCR / Text Extraction  (Tesseract, PyMuPDF, python-docx)
    ↓
LLM Structured Extraction  (Gemini 2.5 Flash: skills, dates, issuer, category, confidence score)
    ↓
Identity Profile Update  (skills / achievements / timeline / career profile)
    ↓
Knowledge Graph Update  (Neo4j AuraDB — relationships between entities)
    ↓
Chunk + Embed  →  Vector DB  (Qdrant Cloud)
    ↓
Hybrid Retrieval  (semantic + keyword + metadata + graph traversal)
    ↓
RAG Reasoning + Citation Generation  (Gemini 2.5 Flash)
    ↓
Career Intelligence Engine  (job match / gap analysis / resume + cover letter)
    ↓
Natural Language Answer + Link to Original File  (stored on Cloudflare R2)
```

## 2. Technical Stack (Locked — Single Target Stack)

| Layer | Technology | Notes |
|---|---|---|
| Frontend | React + Tailwind CSS | See `Design.md` for tokens |
| Backend | FastAPI (Python) | Async endpoints for LLM/OCR calls; deployed on Render |
| OCR | Tesseract (`pytesseract`) | Scanned certificates/images |
| PDF parsing | PyMuPDF (`fitz`) | Text-based PDFs |
| DOCX parsing | `python-docx` | Resumes, reports |
| LLM | Gemini 2.5 Flash (`google-genai` SDK) | Extraction, categorization, edge explanations, RAG answers, resume/cover letter generation |
| Embeddings | Hosted embeddings API (OpenAI or Voyage); fallback: `sentence-transformers` locally | Do not self-host BGE-M3 for this build — unnecessary infra weight |
| Vector database | Qdrant Cloud (managed free tier) | Default primary vector store; no local server needed |
| Knowledge graph | Neo4j AuraDB (managed free tier) | Default primary graph store; queried via Cypher |
| Graph rendering | `react-force-graph` | Interactive node-link UI |
| File storage | Cloudflare R2 (10GB free, zero egress fees) | Primary default storage for unmodified original files (Local filesystem fallback for offline dev) |
| Hosting | Render (Free Web Service) | Primary deploy target. Note: Ephemeral filesystem (requires R2) & 15-min spin-down (~30-60s cold start) |
| Auth | Supabase Auth (email/password) | Minimal — single-user demo doesn't need more |

> [!IMPORTANT]
> **Unified Architecture & Hosting Constraints**: Render's free Web Service tier features an **ephemeral filesystem** (no persistent disk storage) and spins down after 15 minutes of inactivity (~30–60s cold start). Therefore, the application is built directly against cloud-managed services (**Cloudflare R2**, **Qdrant Cloud**, and **Neo4j AuraDB**) as the single primary default stack, ensuring seamless operation locally and when deployed. Local Docker containers are an optional convenience for offline testing only.

## 3. Repository / Folder Structure

```
memoryverse/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI entrypoint
│   │   ├── api/
│   │   │   ├── upload.py           # POST /upload
│   │   │   ├── documents.py        # GET /documents, GET /documents/{id}
│   │   │   ├── search.py           # POST /search (natural language)
│   │   │   ├── graph.py            # GET /graph
│   │   │   ├── timeline.py         # GET /timeline
│   │   │   └── career.py           # POST /career/match
│   │   ├── services/
│   │   │   ├── extraction.py       # OCR / PDF / DOCX text extraction
│   │   │   ├── llm_client.py       # Gemini API client wrapper
│   │   │   ├── llm_extraction.py   # LLM structured extraction + confidence scoring
│   │   │   ├── categorization.py   # Category assignment
│   │   │   ├── storage.py          # Swappable storage backend (R2 / Local)
│   │   │   ├── document_store.py   # Document metadata store
│   │   │   ├── embeddings.py       # Chunking + embedding calls
│   │   │   ├── vector_store.py     # Qdrant Cloud client wrapper
│   │   │   ├── graph_store.py      # Neo4j AuraDB client wrapper (Cypher queries)
│   │   │   ├── retrieval.py        # Hybrid retrieval logic
│   │   │   ├── reasoning.py        # RAG + citation generation
│   │   │   └── career_intelligence.py  # Job matching, gap analysis, doc generation
│   │   ├── models/
│   │   │   └── schemas.py          # Pydantic models
│   │   └── config.py                # Env vars, API keys
│   ├── tests/
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Upload.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── KnowledgeGraph.tsx
│   │   │   ├── Timeline.tsx
│   │   │   ├── Chat.tsx
│   │   │   └── CareerIntelligence.tsx
│   │   ├── components/
│   │   ├── styles/                 # tokens.css — see Design.md
│   │   └── api/                    # fetch wrappers to backend
│   └── package.json
│
├── PRD.md
├── Architecture.md
├── Rules.md
├── Phases.md
├── Design.md
├── Memory.md                       # session log and context
├── solution.md
└── README.md
```

## 4. Key Data Models (Conceptual)

- **Document**: id, filename, original_file_url, category, extracted_text, entities[], confidence, uploaded_at.
- **Entity**: id, type (skill/technology/organization/role), name, source_document_ids[].
- **Relationship (graph edge)**: source_entity_id, target_entity_id, relationship_type, explanation (LLM-generated).
- **TimelineEvent**: date, title, linked_document_id, linked_entity_ids[].
- **CareerMatch**: job_description_text, match_score, matched_evidence[], gaps[], generated_resume, generated_cover_letter.

## 5. Integration Points

- Every backend service that touches the LLM (extraction, categorization, edge explanation, RAG answers, career intelligence) goes through `llm_client.py` — one place to change models, add retries, or swap providers.
- File storage goes through `storage.py` (swappable between Cloudflare R2 default and Local filesystem for offline dev).
- Vector DB (Qdrant Cloud) and Graph DB (Neo4j AuraDB) are accessed strictly through `vector_store.py` and `graph_store.py` wrappers.
- The frontend never talks directly to cloud storage, Qdrant, Neo4j, or LLM APIs — everything goes through the FastAPI backend.
