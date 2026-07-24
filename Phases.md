# Phases.md — Build Phases for MemoryVerse AI

Each phase ends with something demoable. Do not begin a phase until the previous one is working end-to-end — a half-finished later phase is worth less than a solid earlier one. See `solution.md` Section 9 for the original rationale.

---

## Phase 0 — Cloud Setup & Credentials

**Goal:** sign up for managed free-tier services and configure connection credentials.

- [x] Obtain Gemini API Key from Google AI Studio.
- [ ] Sign up for Qdrant Cloud (free tier) and obtain Cluster URL + API Key.
- [ ] Sign up for Neo4j AuraDB (free tier) and obtain Instance URI, User, and Password.
- [ ] Sign up for Cloudflare R2 (10GB free tier) and create Bucket + API Access Keys (`R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`).
- [x] Set up `.env` with active cloud credentials.

---

## Phase 1 — Foundation & Ingestion Core

**Goal:** a user can upload a document and see it stored, extracted, and categorized.

- [x] Backend skeleton: FastAPI app, folder structure per `Architecture.md`, `.env.example` set up.
- [x] Frontend skeleton: React app shell, routing between Upload / Dashboard / Graph / Timeline / Chat / Career pages.
- [x] File upload endpoint (PDF, DOCX, image) — stores original file unmodified (Cloudflare R2 default / Local fallback).
- [x] Text extraction service: Tesseract for images, PyMuPDF for PDFs, python-docx for DOCX.
- [x] LLM structured extraction: category, title, issuer, date, entities, confidence score via Gemini 2.5 Flash.
- [x] Basic dashboard listing uploaded documents with assigned categories.

**Demo checkpoint:** upload 3–4 mixed files, watch them appear correctly categorized within seconds.

---

## Phase 2 — Identity & Knowledge Graph

**Goal:** uploaded documents visibly connect to each other.

- [ ] Identity profile store: aggregate skills/achievements/timeline data per user as documents are added.
- [ ] Neo4j AuraDB integration: write extracted entities as graph nodes, infer relationships (shared skill/technology/date proximity).
- [ ] LLM-generated edge explanations (one line per relationship).
- [ ] Knowledge graph UI (`react-force-graph`): explorable, click a node to see connected items, click an edge to see its explanation.
- [ ] Timeline UI: chronological view of documents/events, linked to source files.

**Demo checkpoint:** upload a certificate and a related project; the graph shows the connection with a sensible explanation.

---

## Phase 3 — Retrieval

**Goal:** natural-language search returns the right original files.

- [ ] Chunking + embedding pipeline for extracted text.
- [ ] Qdrant Cloud integration: store embeddings with metadata and a pointer to the original file.
- [ ] Basic semantic search endpoint: query → embed → similarity search → return matching documents.
- [ ] Chat-style search UI: type a query, get back results with direct links to original files.

**Demo checkpoint:** type "show my Python certificates" and get back the exact right file, not a generic list.

---

## Phase 4 — Career Intelligence Engine (Hero Feature)

**Goal:** paste a job description, get evidence-backed output.

- [ ] Job description input UI.
- [ ] Requirement extraction from the JD (Gemini 2.5 Flash).
- [ ] Semantic comparison against user corpus (via Qdrant Cloud + Neo4j AuraDB graph traversal).
- [ ] Match score calculation with cited evidence (linked to real files).
- [ ] Gap analysis: what's missing relative to the JD.
- [ ] Generated resume and cover letter grounded in real uploaded documents — must cite specific real content.

**Demo checkpoint:** paste a real JD, get a match score, gap list, and a cover letter that references specific real projects/certs by name.

---

## Phase 5 — Hybrid Retrieval Upgrade & Reasoning Layer

**Goal:** retrieval and answers become explainable and multi-source.

- [ ] Upgrade search to Hybrid Retrieval: combine semantic search + keyword search + metadata filters + graph traversal.
- [ ] RAG reasoning layer: answers synthesize across multiple documents.
- [ ] Citation generation: every AI answer links back to specific source file(s).
- [ ] Proactive AI Identity Insights: dashboard surfaces unprompted observations.

**Demo checkpoint:** ask a multi-document question ("why am I suitable for an AI Engineer role?") and get a synthesized, cited answer.

---

## Phase 6 — Deployment, Polish & Deliverables

**Goal:** deployed on Render and submission-ready.

- [ ] Deploy backend and frontend to Render (connecting to Qdrant Cloud, Neo4j AuraDB, Cloudflare R2).
- [ ] UI/UX pass across all pages — consistent with `Design.md`.
- [ ] Record demo video following the narrative in `solution.md` Section 10.
- [ ] Finalize README (feature summary + screenshots, lead with Career Intelligence hero moment).
- [ ] Produce polished visual architecture diagram from `Architecture.md`.
- [ ] Finalize thought-process sheet using trade-off rationale from `solution.md`.

---

## Notes for Future Sessions

- If a phase is only partially complete when a session ends, record exactly what's done vs. pending in `Memory.md` before stopping.
- Do not jump ahead to Phase 4/5 features because they're more exciting than finishing Phase 2/3 — the phased order exists specifically so there's always a working demo.
