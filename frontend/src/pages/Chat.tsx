import { useState, useRef, useEffect } from 'react';
import { chatSearch, getDocumentFileUrl } from '../api/client';
import type { ChatMessage, Citation } from '../api/client';
import './Chat.css';

export default function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content: 'Hello! I am MemoryVerse AI. Ask me anything about your uploaded certificates, skills, internships, or project reports. Every response is grounded in your verified records.',
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const threadEndRef = useRef<HTMLDivElement | null>(null);

  const promptChips = [
    'Show my Python certificates',
    'Summarize my AI project reports',
    'What machine learning skills do I have?',
    'List my internship achievements',
  ];

  useEffect(() => {
    threadEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  async function handleSend(queryText?: string) {
    const messageText = queryText || input;
    if (!messageText.trim() || loading) return;

    const userMessage: ChatMessage = { role: 'user', content: messageText };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await chatSearch({
        message: messageText,
        history: messages,
      });

      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.answer,
        citations: response.citations,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `⚠️ Search Error: ${err.message || 'Failed to complete vector RAG search. Check backend status.'}`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="chat-container">
      {/* Header */}
      <div className="chat-header">
        <h1>Identity RAG Chat</h1>
        <p>Ask natural language questions backed by Qdrant vector search and Gemini synthesis.</p>
      </div>

      {/* Prompt Chip Shortcuts */}
      <div className="prompt-chips">
        {promptChips.map((chip, i) => (
          <button key={i} className="prompt-chip" onClick={() => handleSend(chip)}>
            {chip}
          </button>
        ))}
      </div>

      {/* Messages Thread */}
      <div className="messages-thread">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message-bubble ${msg.role}`}>
            <div className="message-header">
              <span className="message-author">
                {msg.role === 'user' ? 'You' : 'MemoryVerse AI'}
              </span>
              {msg.role === 'assistant' && msg.citations && msg.citations.length > 0 && (
                <span className="confidence-badge">Verified Evidence</span>
              )}
            </div>

            <div className="message-content">
              {msg.content}

              {/* Citations Card Block */}
              {msg.citations && msg.citations.length > 0 && (
                <div className="citations-wrapper">
                  <div className="citations-title">CITED SOURCE DOCUMENTS</div>
                  {msg.citations.map((citation: Citation, cIdx: number) => (
                    <div key={cIdx} className="citation-card">
                      <div className="citation-info">
                        <span className="citation-doc-title">
                          [{citation.category}] {citation.title}
                        </span>
                        <span className="citation-snippet">"{citation.snippet}"</span>
                      </div>
                      <a
                        href={getDocumentFileUrl(citation.document_id)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="citation-download-link"
                      >
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                          <polyline points="7 10 12 15 17 10" />
                          <line x1="12" y1="15" x2="12" y2="3" />
                        </svg>
                        View File
                      </a>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="message-bubble assistant">
            <div className="message-header">
              <span className="message-author">MemoryVerse AI</span>
            </div>
            <div className="message-content" style={{ color: 'var(--text-muted)' }}>
              Searching vector repository and synthesizing evidence...
            </div>
          </div>
        )}

        <div ref={threadEndRef} />
      </div>

      {/* Input Bar */}
      <form
        className="chat-input-bar"
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
      >
        <input
          type="text"
          className="chat-input"
          placeholder="Ask a question about your verified career history..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button type="submit" className="send-btn" disabled={loading || !input.trim()}>
          {loading ? 'Searching...' : 'Send'}
        </button>
      </form>
    </div>
  );
}
