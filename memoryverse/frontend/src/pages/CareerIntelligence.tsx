import { useState } from 'react';
import { analyzeCareerMatch, getDocumentFileUrl } from '../api/client';
import type { CareerAnalysisResponse } from '../api/client';
import './CareerIntelligence.css';

export default function CareerIntelligence() {
  const [jobTitle, setJobTitle] = useState('Senior AI Engineer');
  const [company, setCompany] = useState('Google DeepMind');
  const [jobDescription, setJobDescription] = useState(
    `Role: Senior AI Engineer\nCompany: Google DeepMind\nRequirements:\n- Strong background in Python, PyTorch/TensorFlow, and Large Language Models (LLMs).\n- Experience with RAG pipelines, vector databases (Qdrant, Pinecone), and Knowledge Graphs (Neo4j).\n- Demonstrated experience in document processing, OCR (Tesseract, PyMuPDF), and REST APIs with FastAPI.\n- Proven track record of building production AI agents.`
  );

  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState<CareerAnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'resume' | 'cover' | 'breakdown'>('breakdown');
  const [copied, setCopied] = useState(false);

  const sampleJDs = [
    {
      title: 'Senior AI Engineer',
      company: 'Google DeepMind',
      jd: `Role: Senior AI Engineer\nRequirements:\n- Python, LLMs, PyTorch, RAG architectures, Vector DBs (Qdrant), Neo4j Knowledge Graphs.\n- Text extraction & OCR pipelines with PyMuPDF & Tesseract.\n- FastAPI REST API backend development.`,
    },
    {
      title: 'Full Stack AI Developer',
      company: 'Anthropic',
      jd: `Role: Full Stack AI Developer\nRequirements:\n- React, Vite, TypeScript frontend with custom CSS styling.\n- FastAPI, Python backend integration.\n- LLM structured JSON extraction, RAG search, and Vector DB retrieval.`,
    },
  ];

  async function handleAnalyze(e?: React.FormEvent) {
    if (e) e.preventDefault();
    if (!jobDescription.trim() || loading) return;

    setLoading(true);
    setError(null);

    try {
      const result = await analyzeCareerMatch({
        job_title: jobTitle,
        company: company,
        job_description: jobDescription,
      });
      setAnalysis(result);
      setActiveTab('breakdown');
    } catch (err: any) {
      setError(err.message || 'Failed to complete Career Match analysis.');
    } finally {
      setLoading(false);
    }
  }

  function handleCopy(text: string) {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="career-container">
      {/* Header */}
      <div className="career-header">
        <h1>Career Intelligence Engine</h1>
        <p>Hero Feature — Paste a target Job Description to generate evidence-grounded match scores, gap analysis, and tailored applications.</p>
      </div>

      <div className="career-layout">
        {/* Left Panel: Form Input */}
        <div className="form-panel">
          <div className="form-group">
            <label className="form-label">Target Job Title</label>
            <input
              type="text"
              className="form-input"
              value={jobTitle}
              onChange={(e) => setJobTitle(e.target.value)}
              placeholder="e.g. Senior AI Engineer"
            />
          </div>

          <div className="form-group">
            <label className="form-label">Company Name</label>
            <input
              type="text"
              className="form-input"
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              placeholder="e.g. Google DeepMind"
            />
          </div>

          <div className="form-group">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <label className="form-label">Job Description</label>
              <div className="sample-jds-row">
                {sampleJDs.map((s, i) => (
                  <button
                    key={i}
                    type="button"
                    className="sample-jd-btn"
                    onClick={() => {
                      setJobTitle(s.title);
                      setCompany(s.company);
                      setJobDescription(s.jd);
                    }}
                  >
                    Load {s.title}
                  </button>
                ))}
              </div>
            </div>
            <textarea
              className="form-textarea"
              rows={10}
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              placeholder="Paste raw target job description text here..."
            />
          </div>

          <button
            type="button"
            className="analyze-btn"
            disabled={loading || !jobDescription.trim()}
            onClick={handleAnalyze}
          >
            {loading ? 'Analyzing Corpus & Synthesizing Grounded Match...' : '⚡ Run Career Match Analysis'}
          </button>
        </div>

        {/* Right Panel: Analysis Results */}
        <div className="results-panel">
          {error && (
            <div className="empty-state">
              <div className="empty-icon">⚠️</div>
              <h2>Analysis Error</h2>
              <p>{error}</p>
            </div>
          )}

          {!analysis && !loading && !error && (
            <div className="empty-state">
              <div className="empty-icon">🎯</div>
              <h2>Ready for Career Analysis</h2>
              <p>Paste a job description on the left and click 'Run Career Match Analysis' to generate an evidence-grounded score and tailored application.</p>
              <span className="phase-badge">Phase 4 — Hero Feature Active</span>
            </div>
          )}

          {loading && (
            <div className="empty-state">
              <div className="empty-icon">⚡</div>
              <h2>Analyzing Digital Identity Corpus...</h2>
              <p>Extracting requirements with Gemini 3.6 Flash and querying Qdrant Cloud + Neo4j AuraDB...</p>
            </div>
          )}

          {analysis && !loading && (
            <>
              {/* Score Header Card */}
              <div className="score-card">
                <div
                  className="score-circle"
                  style={{ '--score-pct': analysis.overall_score } as React.CSSProperties}
                >
                  <span className="score-value">{analysis.overall_score}%</span>
                </div>
                <div className="score-details">
                  <h2>{jobTitle} Match</h2>
                  <div className="sub-scores-row">
                    <span className="sub-score-item">
                      Skills Match: <strong>{analysis.skills_score}%</strong>
                    </span>
                    <span className="sub-score-item">
                      Evidence Score: <strong>{analysis.experience_score}%</strong>
                    </span>
                  </div>
                </div>
              </div>

              {/* Tabs Bar */}
              <div className="doc-tabs">
                <button
                  className={`doc-tab-btn ${activeTab === 'breakdown' ? 'active' : ''}`}
                  onClick={() => setActiveTab('breakdown')}
                >
                  Match Breakdown & Gaps
                </button>
                <button
                  className={`doc-tab-btn ${activeTab === 'resume' ? 'active' : ''}`}
                  onClick={() => setActiveTab('resume')}
                >
                  Tailored Resume
                </button>
                <button
                  className={`doc-tab-btn ${activeTab === 'cover' ? 'active' : ''}`}
                  onClick={() => setActiveTab('cover')}
                >
                  Tailored Cover Letter
                </button>
              </div>

              {/* Tab 1: Breakdown & Gaps */}
              {activeTab === 'breakdown' && (
                <div className="doc-viewer">
                  <h3 style={{ fontFamily: 'var(--font-display)', color: 'var(--text-primary)', marginBottom: 'var(--space-3)' }}>
                    Skill Evidence & Matching
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)', marginBottom: 'var(--space-6)' }}>
                    {analysis.matched_skills.map((skill, idx) => (
                      <div key={idx} className="citation-card" style={{ flexDirection: 'column', alignItems: 'flex-start', gap: '4px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                          <strong style={{ color: skill.status === 'matched' ? 'var(--accent-sage)' : 'var(--accent-gold)' }}>
                            {skill.status === 'matched' ? '✓' : '⚠️'} {skill.skill}
                          </strong>
                          <span className="confidence-badge">
                            {skill.status === 'matched' ? `${(skill.confidence * 100).toFixed(0)}% Evidence Match` : 'Gap Identified'}
                          </span>
                        </div>
                        {skill.evidence_title && (
                          <span className="citation-snippet">
                            Source Document: <strong>{skill.evidence_title}</strong>
                          </span>
                        )}
                        {skill.evidence_doc_id && (
                          <a
                            href={getDocumentFileUrl(skill.evidence_doc_id)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="citation-download-link"
                          >
                            View Verified File
                          </a>
                        )}
                      </div>
                    ))}
                  </div>

                  {analysis.missing_gaps.length > 0 && (
                    <>
                      <h3 style={{ fontFamily: 'var(--font-display)', color: 'var(--accent-gold)', marginBottom: 'var(--space-2)' }}>
                        Identified Career Gaps
                      </h3>
                      <ul style={{ color: 'var(--text-muted)', fontSize: 'var(--text-sm)', paddingLeft: 'var(--space-5)' }}>
                        {analysis.missing_gaps.map((gap, gIdx) => (
                          <li key={gIdx} style={{ marginBottom: '4px' }}>{gap}</li>
                        ))}
                      </ul>
                    </>
                  )}
                </div>
              )}

              {/* Tab 2: Tailored Resume */}
              {activeTab === 'resume' && (
                <div>
                  <button className="copy-btn" onClick={() => handleCopy(analysis.tailored_resume)}>
                    {copied ? '✓ Copied!' : 'Copy Resume'}
                  </button>
                  <div className="doc-viewer">
                    <pre>{analysis.tailored_resume}</pre>
                  </div>
                </div>
              )}

              {/* Tab 3: Cover Letter */}
              {activeTab === 'cover' && (
                <div>
                  <button className="copy-btn" onClick={() => handleCopy(analysis.cover_letter)}>
                    {copied ? '✓ Copied!' : 'Copy Cover Letter'}
                  </button>
                  <div className="doc-viewer">
                    <pre>{analysis.cover_letter}</pre>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
