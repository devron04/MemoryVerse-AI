import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import Upload from './pages/Upload';
import Dashboard from './pages/Dashboard';
import KnowledgeGraph from './pages/KnowledgeGraph';
import Timeline from './pages/Timeline';
import Search from './pages/Search';
import Chat from './pages/Chat';
import CareerIntelligence from './pages/CareerIntelligence';

/**
 * MemoryVerse AI — Main App Component
 *
 * App shell with sidebar navigation and page routing.
 * Routes: Upload, Dashboard, KnowledgeGraph, Timeline, Search, Chat, CareerIntelligence.
 */
export default function App() {
  return (
    <Router>
      <div className="app-layout">
        {/* Sidebar Navigation */}
        <aside className="app-sidebar">
          <div className="sidebar-brand">
            <h1>
              Memory<span className="brand-accent">Verse</span>
            </h1>
            <p>Living Digital Identity</p>
          </div>

          <nav className="sidebar-nav">
            <span className="nav-section-label">Core</span>

            <NavLink
              to="/"
              end
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
              id="nav-dashboard"
            >
              <svg className="nav-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="3" width="7" height="7" />
                <rect x="14" y="3" width="7" height="7" />
                <rect x="3" y="14" width="7" height="7" />
                <rect x="14" y="14" width="7" height="7" />
              </svg>
              Dashboard
            </NavLink>

            <NavLink
              to="/upload"
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
              id="nav-upload"
            >
              <svg className="nav-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
              Upload
            </NavLink>

            <span className="nav-section-label">Explore</span>

            <NavLink
              to="/graph"
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
              id="nav-graph"
            >
              <svg className="nav-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="3" />
                <circle cx="4" cy="6" r="2" />
                <circle cx="20" cy="6" r="2" />
                <circle cx="4" cy="18" r="2" />
                <circle cx="20" cy="18" r="2" />
                <line x1="6" y1="7" x2="10" y2="10" />
                <line x1="18" y1="7" x2="14" y2="10" />
                <line x1="6" y1="17" x2="10" y2="14" />
                <line x1="18" y1="17" x2="14" y2="14" />
              </svg>
              Knowledge Graph
            </NavLink>

            <NavLink
              to="/timeline"
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
              id="nav-timeline"
            >
              <svg className="nav-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="12" y1="2" x2="12" y2="22" />
                <circle cx="12" cy="6" r="2" />
                <circle cx="12" cy="12" r="2" />
                <circle cx="12" cy="18" r="2" />
                <line x1="14" y1="6" x2="20" y2="6" />
                <line x1="4" y1="12" x2="10" y2="12" />
                <line x1="14" y1="18" x2="20" y2="18" />
              </svg>
              Timeline
            </NavLink>

            <NavLink
              to="/search"
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
              id="nav-search"
            >
              <svg className="nav-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
              Vector Search
            </NavLink>

            <NavLink
              to="/chat"
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
              id="nav-chat"
            >
              <svg className="nav-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" />
              </svg>
              RAG Chat
            </NavLink>

            <span className="nav-section-label">Intelligence</span>

            <NavLink
              to="/career"
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
              id="nav-career"
            >
              <svg className="nav-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
              Career Match
            </NavLink>
          </nav>
        </aside>

        {/* Main Content */}
        <main className="app-main">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/graph" element={<KnowledgeGraph />} />
            <Route path="/timeline" element={<Timeline />} />
            <Route path="/search" element={<Search />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/career" element={<CareerIntelligence />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}
