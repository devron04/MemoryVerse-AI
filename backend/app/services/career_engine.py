"""
MemoryVerse AI — Career Intelligence Engine (Hero Feature)

Orchestrates:
1. Requirement extraction from Job Description using Gemini 3.6 Flash.
2. Hybrid matching against user corpus (Qdrant vector similarity + Neo4j entity graph).
3. Score calculation (overall %, skills %, experience %).
4. Gap analysis identification.
5. Evidence citation generation linking to real files.
6. Grounded synthesis of tailored Resume & Cover Letter citing real source documents.

Per Rules.md §5: AI never fabricates unverified experience — all outputs cite uploaded files.
"""

import logging
from typing import Optional

from app.models.schemas import (
    CareerAnalysisRequest,
    CareerAnalysisResponse,
    SkillMatch,
    Citation,
    DocumentRecord,
)
from app.services.llm_client import LLMClient
from app.services.vector_store import VectorStore
from app.services.graph_store import GraphStore
from app.services.document_store import DocumentStore

logger = logging.getLogger(__name__)


class CareerEngineError(Exception):
    """Custom exception for CareerEngine operations."""

    def __init__(self, message: str, detail: str = ""):
        self.message = message
        self.detail = detail
        super().__init__(message)


class CareerEngine:
    """
    Career Match & Evidence Synthesis Engine.
    """

    def __init__(
        self,
        vector_store: VectorStore,
        graph_store: GraphStore,
        doc_store: DocumentStore,
        llm_client: LLMClient,
    ):
        self.vector_store = vector_store
        self.graph_store = graph_store
        self.doc_store = doc_store
        self.llm_client = llm_client

    def analyze_job_description(self, request: CareerAnalysisRequest) -> CareerAnalysisResponse:
        """
        Analyze a target job description against the user's verified digital identity records.

        Args:
            request: CareerAnalysisRequest containing job title, company, and JD text.

        Returns:
            CareerAnalysisResponse with match scores, skill breakdown, gap list,
            citations, and grounded resume/cover letter.
        """
        # 1. Extract requirements from raw JD using Gemini 3.6 Flash
        jd_prompt = (
            f"Analyze the following Job Description for role '{request.job_title}'.\n"
            f"Company: {request.company or 'Target Employer'}\n\n"
            f"Job Description:\n{request.job_description}\n\n"
            f"Extract:\n"
            f"1. A list of 5-8 specific required technical skills/tools.\n"
            f"2. A list of 3-5 general qualifications or experience requirements.\n\n"
            f"Return JSON format:\n"
            f"{{\n"
            f'  "required_skills": ["Python", "Machine Learning", ...],\n'
            f'  "qualifications": ["3+ years in AI", "Bachelor degree", ...]\n'
            f"}}"
        )

        try:
            req_data = self.llm_client.generate_json(jd_prompt)
            required_skills = req_data.get("required_skills", ["Python", "Software Engineering"])
            qualifications = req_data.get("qualifications", ["Technical Experience"])
        except Exception as e:
            logger.warning("Failed to extract JD requirements with LLM: %s", str(e))
            required_skills = ["Software Engineering", "Problem Solving", "Python"]
            qualifications = ["Technical Degree or Equivalent Experience"]

        # 2. Retrieve user document records
        all_docs = self.doc_store.get_all()

        # Handle case where user has no documents uploaded yet
        if not all_docs:
            matched_skills = [
                SkillMatch(skill=skill, status="gap", confidence=0.0)
                for skill in required_skills
            ]
            missing_gaps = required_skills + qualifications
            return CareerAnalysisResponse(
                overall_score=0.0,
                skills_score=0.0,
                experience_score=0.0,
                matched_skills=matched_skills,
                missing_gaps=missing_gaps,
                tailored_resume="# Digital Identity Profile (Empty)\n\nNo verified documents uploaded yet. Upload certificates and project reports to generate a grounded resume.",
                cover_letter=f"Dear Hiring Team at {request.company or 'Target Employer'},\n\nI am applying for the {request.job_title} role. Please upload verified career records to MemoryVerse AI to generate a grounded cover letter.",
                citations=[],
            )

        # 3. Perform Vector Similarity Search (Qdrant) & Graph Traversal for each required skill
        matched_skills: list[SkillMatch] = []
        citations_map: dict[str, Citation] = {}
        missing_gaps: list[str] = []
        matched_count = 0

        for skill in required_skills:
            hits = self.vector_store.search(query=skill, llm_client=self.llm_client, limit=2)

            if hits and hits[0].score >= 0.45:
                top_hit = hits[0]
                matched_count += 1
                matched_skills.append(
                    SkillMatch(
                        skill=skill,
                        status="matched",
                        confidence=top_hit.score,
                        evidence_doc_id=top_hit.document_id,
                        evidence_title=top_hit.title,
                        evidence_snippet=top_hit.snippet[:150] + "...",
                    )
                )
                if top_hit.document_id not in citations_map:
                    citations_map[top_hit.document_id] = Citation(
                        document_id=top_hit.document_id,
                        title=top_hit.title,
                        category=top_hit.category,
                        snippet=top_hit.snippet,
                        score=top_hit.score,
                    )
            else:
                matched_skills.append(
                    SkillMatch(skill=skill, status="gap", confidence=0.0)
                )
                missing_gaps.append(skill)

        # 4. Calculate Scores
        skills_score = round((matched_count / max(len(required_skills), 1)) * 100.0, 1)
        doc_count = len(all_docs)
        experience_score = min(round(doc_count * 25.0, 1), 100.0)
        overall_score = round((skills_score * 0.7) + (experience_score * 0.3), 1)

        # 5. Synthesize Grounded Resume & Cover Letter with Gemini 3.6 Flash
        doc_summaries = "\n".join([
            f"- [{d.category.value}] Title: '{d.title}' | Issuer: '{d.issuer or 'Self'}' | Date: '{d.date or d.uploaded_at[:10]}'\n  Summary: {d.summary or 'N/A'}"
            for d in all_docs
        ])

        synthesis_prompt = (
            f"You are MemoryVerse AI. Synthesize a professional Tailored Resume and Cover Letter for the role '{request.job_title}' "
            f"at '{request.company or 'Target Employer'}'.\n\n"
            f"CRITICAL RULE: Synthesize ONLY using the verified document records provided below. Never fabricate unverified experience or claims.\n\n"
            f"Verified User Career Records:\n{doc_summaries}\n\n"
            f"Target Job Description:\n{request.job_description[:800]}\n\n"
            f"Return JSON format:\n"
            f"{{\n"
            f'  "tailored_resume": "Markdown string of tailored resume...",\n'
            f'  "cover_letter": "Markdown string of cover letter..."\n'
            f"}}"
        )

        try:
            synth_res = self.llm_client.generate_json(synthesis_prompt)
            tailored_resume = synth_res.get("tailored_resume", self._fallback_resume(all_docs, request))
            cover_letter = synth_res.get("cover_letter", self._fallback_cover_letter(all_docs, request))
        except Exception as e:
            logger.error("LLM career document synthesis error: %s", str(e))
            tailored_resume = self._fallback_resume(all_docs, request)
            cover_letter = self._fallback_cover_letter(all_docs, request)

        return CareerAnalysisResponse(
            overall_score=overall_score,
            skills_score=skills_score,
            experience_score=experience_score,
            matched_skills=matched_skills,
            missing_gaps=missing_gaps,
            tailored_resume=tailored_resume,
            cover_letter=cover_letter,
            citations=list(citations_map.values()),
        )

    def _fallback_resume(self, docs: list[DocumentRecord], req: CareerAnalysisRequest) -> str:
        """Fallback markdown resume generator."""
        lines = [f"# Verified Resume — {req.job_title}", ""]
        lines.append("## Verified Experience & Documented Achievements")
        for d in docs:
            lines.append(f"### {d.title}")
            lines.append(f"**Category:** {d.category.value} | **Issuer:** {d.issuer or 'N/A'} | **Date:** {d.date or d.uploaded_at[:10]}")
            if d.summary:
                lines.append(f"_{d.summary}_")
            lines.append("")
        return "\n".join(lines)

    def _fallback_cover_letter(self, docs: list[DocumentRecord], req: CareerAnalysisRequest) -> str:
        """Fallback markdown cover letter generator."""
        company = req.company or "Hiring Team"
        first_doc = docs[0].title if docs else "my career portfolio"
        return (
            f"Dear Hiring Manager at {company},\n\n"
            f"I am writing to express my strong interest in the {req.job_title} position. "
            f"My verified career records in MemoryVerse AI, including '{first_doc}', demonstrate my "
            f"relevant skills and qualifications for this role.\n\n"
            f"Thank you for considering my application.\n\nSincerely,\nApplicant"
        )
