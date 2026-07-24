import { useState } from 'react';
import { searchDocuments, getDocumentFileUrl } from '../api/client';
import type { SearchHit } from '../api/client';
import './Search.css';

export default function Search() {
  const [query, setQuery] = useState('');
  const [hits, setHits] = useState<SearchHit[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSearch(e?: React.FormEvent) {
    if (e) e.preventDefault();
    if (!query.trim() || loading) return;

    setLoading(true);
    setError(null);
    try {
      const res = await searchDocuments(query);
      setHits(res.hits);
      setSearched(true);
    } catch (err: any) {
      setError(err.message || 'Search failed. Check backend connection.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="search-container">
      {/* Header */}
      <div className="search-header">
        <h1>Semantic Vector Search</h1>
        <p>Perform natural language similarity search over your Qdrant vector store repository.</p>
      </div>

      {/* Search Input Bar */}
      <form className="search-bar-row" onSubmit={handleSearch}>
        <input
          type="text"
          className="search-bar-input"
          placeholder="Search certificates, skills, or projects (e.g. 'Python certificates')..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button type="submit" className="search-submit-btn" disabled={loading || !query.trim()}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {error && (
        <div className="empty-state">
          <div className="empty-icon">⚠️</div>
          <h2>Search Error</h2>
          <p>{error}</p>
        </div>
      )}

      {/* Results List */}
      {!loading && searched && hits.length === 0 && !error && (
        <div className="empty-state">
          <div className="empty-icon">🔍</div>
          <h2>No Vector Matches Found</h2>
          <p>Try searching for different keywords or upload more documents in the Upload section.</p>
        </div>
      )}

      {!loading && hits.length > 0 && (
        <div className="search-results-list">
          {hits.map((hit) => (
            <div key={hit.document_id} className="search-result-card">
              <div className="search-result-header">
                <span className="search-result-title">
                  [{hit.category}] {hit.title}
                </span>
                <span className="search-match-score">
                  {(hit.score * 100).toFixed(0)}% Vector Match
                </span>
              </div>

              <p className="search-result-snippet">"{hit.snippet}"</p>

              <div className="search-result-footer">
                <div style={{ display: 'flex', gap: '8px' }}>
                  {hit.entities.map((ent, i) => (
                    <span key={i} className="timeline-entity-tag">
                      {ent.type}: {ent.name}
                    </span>
                  ))}
                </div>

                <a
                  href={getDocumentFileUrl(hit.document_id)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="timeline-file-link"
                >
                  Download Source File
                </a>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
