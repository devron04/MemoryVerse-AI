# PRD.md — MemoryVerse AI

## 1. What We're Building

MemoryVerse AI is a **Living Digital Identity System**. Users upload the scattered documents of their academic and professional life — certificates, resumes, project reports, internship letters, portfolio links — and the system automatically categorizes them, connects them into a knowledge graph, builds a growth timeline, and lets the user retrieve anything with a natural-language query.

The system's defining capability: paste a job description, and it produces an evidence-backed match score, gap analysis, and a tailored resume/cover letter generated from the user's own real documents.

**One-line pitch:** *Upload anything, ask anything, retrieve everything — and discover how every achievement connects to your journey and your next opportunity.*

Full context and rationale: see `solution.md`.

## 2. Target Users

- **Primary:** students and early-career professionals with certificates, projects, and internships scattered across drives, emails, and folders, who need to quickly assemble evidence of their skills (for resumes, job applications, or portfolio sites).
- **Secondary (future):** career counselors or recruiters who want a structured, evidence-backed view of a candidate's real history rather than a self-reported resume.

For this build, we design and demo for the **primary user only**. Multi-user/recruiter views are out of scope (see Section 5).

## 3. Problem This Solves

Traditional cloud storage (Drive, Dropbox, local folders) can save files but cannot:
- Understand what a document proves (a certificate proves a skill; a skill enables a project).
- Connect documents to each other (which project used the skill from that certificate?).
- Answer natural questions ("show my AI projects") without manual folder search.
- Turn stored history into something actionable, like a tailored application for a specific job.

## 4. Core Features (Must-Have for MVP)

1. **Document upload & extraction** — PDF, DOCX, images (OCR), and portfolio/GitHub URLs. Original files always preserved and retrievable unchanged.
2. **Automatic categorization** — every document is classified into Projects, Skills, Certifications, Internships, Achievements, or Academics, with structured metadata (dates, issuer, technologies) extracted automatically. No manual sorting required.
3. **Knowledge graph of relationships** — the system infers and displays connections (Certification → Skill → Project → Internship → Career Path), each with a plain-language explanation of why they're connected.
4. **Growth timeline** — a chronological, visual view of the user's documented journey, each entry linked back to its source file.
5. **Natural-language retrieval** — queries like "show my AI projects" or "show my latest resume" return the actual original files, not just a list of names.
6. **Career Intelligence Engine (hero feature)** — paste a job description, get a match score with cited evidence, a gap analysis of missing skills/experience, and a generated resume and cover letter grounded in the user's real documents.

## 5. Explicitly Out of Scope (for this build)

- Multi-user accounts, sharing, or permissions.
- Recruiter-facing dashboards.
- Live LinkedIn/GitHub sync (beyond a one-time URL fetch at upload time).
- Mobile app (web-responsive only).
- Payment/subscription systems.

These are documented as future scope in `solution.md` Section 13 — do not build them now, and do not let their existence expand what "must-have" means.

## 6. Success Criteria

The system succeeds if a first-time user can:
1. Upload 4–5 mixed documents and see them auto-categorized within seconds, with no manual sorting step.
2. Open the knowledge graph and immediately see at least one real, correctly-inferred relationship with a sensible explanation.
3. Type a natural-language query and get back the exact original file they were thinking of.
4. Paste a real job description and receive a match score plus a cover letter that references specific, real things from their uploaded documents (not generic filler text).

If all four hold up live in a demo, the PRD is satisfied.

## 7. Non-Functional Requirements

- **Original files are never modified.** Extraction and analysis are read-only operations on a copy/reference; the source file a user uploaded must always be retrievable byte-for-byte.
- **Every AI-generated claim must be traceable** to a specific uploaded document. No unattributed or fabricated "facts" about the user.
- **Categorization and retrieval should feel instant** in the demo (a few seconds per document, sub-second for search) — this is a judged criterion, not just a nice-to-have.
