import { useState, useEffect } from 'react';
import { getDocuments, getDocumentFileUrl, type DocumentResponse } from '../api/client';
import './Dashboard.css';

/**
 * Dashboard Page — card grid of all uploaded documents.
 * Per Design.md §4: card grid, category color-coded (gold for achievements,
 * sage for skills/projects), extracted title, date. No numbered markers.
 */

export default function Dashboard() {
  const [documents, setDocuments] = useState<DocumentResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDocuments();
  }, []);

  async function loadDocuments() {
    try {
      setLoading(true);
      setError(null);
      const result = await getDocuments();
      setDocuments(result.documents);
    } catch (err: any) {
      setError(err.message || 'Failed to load documents');
    } finally {
      setLoading(false);
    }
  }

  const getCategoryColorClass = (category: string): string => {
    const goldCategories = ['Certifications', 'Achievements'];
    return goldCategories.includes(category) ? 'gold' : 'sage';
  };

  const getConfidenceLevel = (confidence: number): string => {
    if (confidence >= 0.8) return 'high';
    if (confidence >= 0.5) return 'medium';
    return 'low';
  };

  const formatDate = (dateStr: string): string => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    } catch {
      return dateStr;
    }
  };

  const getCategoryIcon = (category: string): string => {
    const icons: Record<string, string> = {
      Projects: '📐',
      Skills: '⚡',
      Certifications: '🏅',
      Internships: '💼',
      Achievements: '🏆',
      Academics: '🎓',
    };
    return icons[category] || '📄';
  };

  if (loading) {
    return (
      <div className="dashboard-page">
        <div className="page-header">
          <h1>Dashboard</h1>
          <p>Your digital identity at a glance.</p>
        </div>
        <div className="loading-state">
          <span className="spinner large" />
          <p>Loading documents…</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard-page">
        <div className="page-header">
          <h1>Dashboard</h1>
          <p>Your digital identity at a glance.</p>
        </div>
        <div className="error-state">
          <p className="error-message">{error}</p>
          <button className="btn btn-secondary" onClick={loadDocuments}>
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-page">
      <div className="page-header">
        <h1>Dashboard</h1>
        <p>
          {documents.length === 0
            ? 'Upload documents to begin building your digital identity.'
            : `${documents.length} document${documents.length !== 1 ? 's' : ''} in your identity vault.`}
        </p>
      </div>

      {documents.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📁</div>
          <h2>No documents yet</h2>
          <p>
            Upload your certificates, resumes, and project reports to see them
            automatically categorized and connected.
          </p>
        </div>
      ) : (
        <>
          {/* Category Summary */}
          <div className="category-summary">
            {Object.entries(
              documents.reduce((acc, doc) => {
                acc[doc.category] = (acc[doc.category] || 0) + 1;
                return acc;
              }, {} as Record<string, number>)
            ).map(([category, count]) => (
              <div key={category} className={`category-stat ${getCategoryColorClass(category)}`}>
                <span className="stat-icon">{getCategoryIcon(category)}</span>
                <span className="stat-count">{count}</span>
                <span className="stat-label">{category}</span>
              </div>
            ))}
          </div>

          {/* Document Grid */}
          <div className="document-grid">
            {documents.map(doc => (
              <div key={doc.id} className="card document-card" id={`doc-${doc.id}`}>
                <div className="card-header">
                  <span className={`category-badge ${getCategoryColorClass(doc.category)}`}>
                    {getCategoryIcon(doc.category)} {doc.category}
                  </span>
                  <div className="confidence-meter">
                    <div className="confidence-bar">
                      <div
                        className={`confidence-fill ${getConfidenceLevel(doc.confidence)}`}
                        style={{ width: `${doc.confidence * 100}%` }}
                      />
                    </div>
                    <span>{Math.round(doc.confidence * 100)}%</span>
                  </div>
                </div>

                <h3 className="card-title">{doc.title}</h3>

                {doc.issuer && (
                  <p className="card-issuer">{doc.issuer}</p>
                )}

                {doc.summary && (
                  <p className="card-summary">{doc.summary}</p>
                )}

                {doc.entities.length > 0 && (
                  <div className="card-entities">
                    {doc.entities.slice(0, 5).map((entity, i) => (
                      <span key={i} className="entity-tag">{entity.name}</span>
                    ))}
                    {doc.entities.length > 5 && (
                      <span className="entity-tag more">+{doc.entities.length - 5}</span>
                    )}
                  </div>
                )}

                <div className="card-footer">
                  <span className="card-date">
                    {doc.date ? formatDate(doc.date) : formatDate(doc.uploaded_at)}
                  </span>
                  <a
                    href={getDocumentFileUrl(doc.id)}
                    className="card-download"
                    target="_blank"
                    rel="noopener noreferrer"
                    title="Download original file"
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                      <polyline points="7 10 12 15 17 10" />
                      <line x1="12" y1="15" x2="12" y2="3" />
                    </svg>
                  </a>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
