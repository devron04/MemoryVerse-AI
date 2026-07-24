import { useEffect, useState } from 'react';
import { getTimeline, getDocumentFileUrl } from '../api/client';
import type { TimelineEvent } from '../api/client';
import './Timeline.css';

export default function Timeline() {
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadTimeline() {
      try {
        setLoading(true);
        const data = await getTimeline();
        setEvents(data.events);
      } catch (err: any) {
        setError(err.message || 'Failed to load growth timeline');
      } finally {
        setLoading(false);
      }
    }
    loadTimeline();
  }, []);

  return (
    <div className="timeline-container">
      {/* Header */}
      <div className="timeline-header">
        <h1>Growth Timeline</h1>
        <p>A chronological record of every documented milestone, linked back to source files.</p>
      </div>

      {loading && (
        <div className="empty-state">
          <div className="empty-icon">📅</div>
          <h2>Loading Growth Timeline...</h2>
        </div>
      )}

      {error && (
        <div className="empty-state">
          <div className="empty-icon">⚠️</div>
          <h2>Timeline Error</h2>
          <p>{error}</p>
        </div>
      )}

      {!loading && events.length === 0 && !error && (
        <div className="empty-state">
          <div className="empty-icon">📅</div>
          <h2>No Milestones Yet</h2>
          <p>
            Upload your certificates, project reports, and internship letters to build your chronological identity timeline.
          </p>
          <span className="phase-badge">Phase 2 — Active</span>
        </div>
      )}

      {/* Vertical Timeline Track */}
      {!loading && events.length > 0 && (
        <div className="timeline-track">
          {events.map((event) => {
            const isGold = ['Certifications', 'Achievements'].includes(event.category);
            return (
              <div key={event.id} className={`timeline-item ${isGold ? 'gold' : ''}`}>
                <div className="timeline-marker" />

                <div className={`timeline-card ${isGold ? 'gold' : ''}`}>
                  <div className="timeline-card-meta">
                    <span className="timeline-date">{event.date}</span>
                    <span className="timeline-category-badge">{event.category}</span>
                  </div>

                  <h2 className="timeline-title">{event.title}</h2>

                  {event.issuer && (
                    <div className="timeline-issuer">Issued by {event.issuer}</div>
                  )}

                  {event.summary && (
                    <p className="timeline-summary">{event.summary}</p>
                  )}

                  {event.entities.length > 0 && (
                    <div className="timeline-entities">
                      {event.entities.map((entity, i) => (
                        <span key={i} className="timeline-entity-tag">
                          {entity.type}: {entity.name}
                        </span>
                      ))}
                    </div>
                  )}

                  <a
                    href={getDocumentFileUrl(event.document_id)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="timeline-file-link"
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                      <polyline points="7 10 12 15 17 10" />
                      <line x1="12" y1="15" x2="12" y2="3" />
                    </svg>
                    Download Original File
                  </a>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
