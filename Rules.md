# Rules.md — Boundaries for AI-Assisted Coding

These rules apply to any AI tool (Claude Code, Cursor, Antigravity, etc.) working on this codebase. Follow them without exception unless the human explicitly overrides one in a given session.

## 1. Stack Discipline

- Use only what's listed in `Architecture.md` Section 2. Do not introduce a new database, ORM, state management library, or CSS framework without updating `Architecture.md` first and flagging it to the human.
- Cloud-managed services (**Qdrant Cloud**, **Neo4j AuraDB**, **Cloudflare R2**, **Gemini 2.5 Flash**) are the primary default services. Do not swap them or introduce unapproved alternatives.
- Backend: FastAPI + Python only. Frontend: React + Tailwind only. No mixing in Flask, Django, Vue, or plain jQuery "just for this one part."

## 2. Cost Discipline & Deployment Target

- Primary free deployment target is **Render** (Free Web Service tier). Note that Render has an ephemeral filesystem (no persistent disk) and spins down after 15 minutes of inactivity.
- Default to managed free tiers (**Cloudflare R2** for file storage, **Qdrant Cloud** for vector embeddings, **Neo4j AuraDB** for knowledge graph, **Gemini 2.5 Flash** for LLM) so the application runs identically in local dev and deployed on Render.
- Railway is explicitly excluded (no permanent free tier).

## 3. Libraries: Prefer / Avoid

**Prefer:**
- `pydantic` for all request/response schemas — never pass raw dicts across service boundaries.
- `httpx` for outbound API calls (async-friendly, matches FastAPI).
- Official SDKs (`google-genai`, `boto3`, `qdrant-client`, `neo4j`) over hand-rolled REST calls.

**Avoid:**
- Do not add a new package to solve something 5–10 lines of plain Python already solves.
- No deprecated or unmaintained packages — if unsure, check the package's last release date before adding it.
- Do not use `pypdf`/`PyPDF2` for PDF text extraction — PyMuPDF is the standard for this project (see `Architecture.md`).

## 4. Error Handling

- Every external call (LLM API, OCR, Cloudflare R2, Qdrant Cloud, Neo4j AuraDB) must be wrapped in a try/except that fails **loud and specific**, not silent. Never swallow an exception and return an empty result without logging why.
- If an LLM call returns malformed JSON when structured output was expected, retry once with a stricter prompt before surfacing an error — do not fabricate a plausible-looking fallback response.
- User-facing errors must say what happened and what to do next (e.g., "Couldn't read this PDF — it may be a scanned image; try re-uploading as a photo instead" — not "Error 500").
- Never let a single failed document upload crash or block the rest of the batch — isolate failures per-document.

## 5. What the AI Should Do

- Write small, testable functions per service (one clear responsibility each) rather than one large handler.
- Add a docstring to every service function stating what it does, its inputs, and its outputs — this project's context gets picked up across many sessions, so self-documenting code matters more than usual.
- Ask before making an architectural decision not already specified in `Architecture.md` (e.g., how to structure a new Neo4j query, how to chunk documents for embedding).
- Update `Memory.md` at the end of each working session with what was completed, what's in progress, and any decisions made that aren't yet reflected in `Architecture.md`.
- Follow the phase order in `Phases.md` — do not start Phase 3 work while Phase 1 is incomplete or broken.

## 6. What the AI Should NOT Do

- Do not invent features not listed in `PRD.md` Section 4, even if they seem like natural extensions. Flag ideas instead of building them silently.
- Do not modify or delete a user's original uploaded file under any circumstance. All processing must operate on copies or read-only references.
- Do not fabricate data to make a demo look more complete (e.g., a fake "match score" if the Career Intelligence Engine isn't wired up yet — leave it visibly unbuilt or return an explicit "not yet available" state instead).
- Do not commit API keys, credentials, or `.env` files. Use `.env.example` with placeholder values only.
- Do not skip the confidence-scoring step in extraction to save time — it's load-bearing for the "explainable" claim in the pitch; if it's genuinely blocking progress, flag it rather than quietly dropping it.
- Do not restructure the folder layout in `Architecture.md` without discussing it first — many sessions will assume this structure holds.

## 7. Session Hygiene

- At the start of a new session, read `Memory.md` first before making any changes — don't re-derive context from scratch or guess at what's already built.
- Keep changes scoped to the current phase in `Phases.md`. Resist "while I'm in here" scope creep into future phases.
- If a rule in this file conflicts with a specific human instruction in a session, the explicit human instruction wins for that session — but flag the conflict rather than silently overriding the rule going forward.
