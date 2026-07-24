# Memory.md — MemoryVerse AI Session Memory

## Project Status Overview

- **Current Phase**: Phase 1 Complete — Preparing for Phase 2 (Identity & Knowledge Graph).
- **Target Stack**: FastAPI (Python) + React (TypeScript/Vite) + Gemini 2.5 Flash + Cloudflare R2 + Qdrant Cloud + Neo4j AuraDB.
- **Deploy Target**: Render (Free Web Service tier).

---

## Session Log: Documentation & Infrastructure Alignment

### What Changed & Rationale
1. **LLM Provider**: Locked to **Gemini 2.5 Flash** (Google AI Studio Free Tier via `google-genai` SDK).
2. **Deployment Hosting Target**: Standardized on **Render** free Web Service tier. Removed Railway references (Railway no longer provides a persistent free tier).
3. **Render Ephemeral Filesystem & Cold Start Considerations**:
   - Render's free tier provides **no persistent local disk** and spins down after 15 minutes of inactivity (~30–60s cold start on next request).
   - Therefore, local filesystem storage cannot be the production path. **Cloudflare R2** (10GB free tier, zero egress fees) is now the primary storage default for uploaded files.
   - Self-hosted Qdrant/Neo4j Docker containers cannot run on Render free tier. Managed cloud services (**Qdrant Cloud** and **Neo4j AuraDB**) are now the primary defaults for both local dev and production.
4. **Single Target Stack Model**: Unified local development and production configurations. The codebase targets cloud-managed services (**Qdrant Cloud**, **Neo4j AuraDB**, **Cloudflare R2**, **Gemini 2.5 Flash**) directly, with local Docker retained only as an optional offline testing path.
5. **Swappable Storage Abstraction**:
   - Implemented `app/services/storage.py` providing `StorageBackend` abstraction (`CloudflareR2StorageBackend` default / `LocalStorageBackend` fallback for offline dev).
   - Added `boto3` dependency to `requirements.txt`.
   - Updated `app/api/upload.py` and `app/api/documents.py` to use `get_storage_backend(settings)`.
   - **Phase 1 core logic untouched**: All extraction (PyMuPDF/docx/Tesseract OCR), categorization, and Pydantic validation functions remain 100% preserved.

### Documents Updated
- `Architecture.md`: Updated tech stack table, app flow, integration points, and hosting constraints.
- `Rules.md`: Updated cost discipline and default service boundaries (Render, Cloudflare R2, Qdrant Cloud, Neo4j AuraDB).
- `Phases.md`: Phase 0 updated for cloud service signup; Phase 1 marked complete; Phase 6 deployment made standard.
- `.env.example` & `.env`: Configured active cloud service credentials as defaults and added Cloudflare R2 configuration settings.

---

## Next Steps

- Obtain credentials for **Qdrant Cloud** and **Neo4j AuraDB**.
- **Phase 4 — Career Intelligence Engine (Hero Feature)**: **COMPLETE & VERIFIED LIVE** ✅
  - `CareerEngine` service (`app/services/career_engine.py`) with Gemini 3.6 Flash requirement extraction, hybrid Qdrant + Neo4j matching, gap analysis, and grounded resume/cover letter synthesis.
  - Endpoints: `POST /api/career/analyze` and `POST /api/career/match` returning `200 OK`.
  - Frontend: Hero Career Match UI (`CareerIntelligence.tsx`) with circular match meter, skill evidence badges, gap list, tabbed resume/cover letter viewer, and sample JD loaders.
