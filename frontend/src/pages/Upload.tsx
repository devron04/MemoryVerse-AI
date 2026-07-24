import { useState, useRef, useCallback } from 'react';
import { uploadFile, type DocumentResponse, type ApiError } from '../api/client';
import './Upload.css';

/**
 * Upload Page — drag-and-drop file upload with progress feedback.
 * Accepts PDF, DOCX, PNG, JPG/JPEG per Architecture.md.
 * Shows upload status and extraction results per document.
 */

interface UploadResult {
  file: File;
  status: 'pending' | 'uploading' | 'success' | 'error';
  document?: DocumentResponse;
  error?: string;
  suggestion?: string;
}

export default function Upload() {
  const [uploads, setUploads] = useState<UploadResult[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const ACCEPTED_TYPES = [
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'image/png',
    'image/jpeg',
    'image/jpg',
  ];

  const ACCEPTED_EXTENSIONS = '.pdf,.docx,.png,.jpg,.jpeg';

  /**
   * Process a single file upload.
   * Per Rules.md §3: per-document error isolation.
   */
  const processFile = useCallback(async (file: File, index: number) => {
    setUploads(prev => {
      const updated = [...prev];
      updated[index] = { ...updated[index], status: 'uploading' };
      return updated;
    });

    try {
      const result = await uploadFile(file);
      setUploads(prev => {
        const updated = [...prev];
        updated[index] = {
          ...updated[index],
          status: 'success',
          document: result.document,
        };
        return updated;
      });
    } catch (err: any) {
      const apiError = err as ApiError;
      setUploads(prev => {
        const updated = [...prev];
        updated[index] = {
          ...updated[index],
          status: 'error',
          error: apiError.message || 'Upload failed',
          suggestion: apiError.suggestion || 'Please try again.',
        };
        return updated;
      });
    }
  }, []);

  /**
   * Handle files selected via input or drag-drop.
   */
  const handleFiles = useCallback((files: FileList | File[]) => {
    const fileArray = Array.from(files);
    const startIndex = uploads.length;

    const newUploads: UploadResult[] = fileArray.map(file => ({
      file,
      status: 'pending' as const,
    }));

    setUploads(prev => [...prev, ...newUploads]);

    // Process each file independently (per-document isolation)
    fileArray.forEach((file, i) => {
      processFile(file, startIndex + i);
    });
  }, [uploads.length, processFile]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files);
    }
  }, [handleFiles]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const getCategoryColorClass = (category: string): string => {
    const goldCategories = ['Certifications', 'Achievements'];
    return goldCategories.includes(category) ? 'gold' : 'sage';
  };

  const getConfidenceLevel = (confidence: number): string => {
    if (confidence >= 0.8) return 'high';
    if (confidence >= 0.5) return 'medium';
    return 'low';
  };

  return (
    <div className="upload-page">
      <div className="page-header">
        <h1>Upload Documents</h1>
        <p>
          Drop your certificates, resumes, project reports, and more.
          We'll extract and categorize everything automatically.
        </p>
      </div>

      {/* Drop Zone */}
      <div
        className={`upload-zone ${isDragging ? 'dragging' : ''}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => fileInputRef.current?.click()}
        role="button"
        tabIndex={0}
        id="upload-drop-zone"
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            fileInputRef.current?.click();
          }
        }}
      >
        <div className="upload-zone-content">
          <div className="upload-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
          </div>
          <h3>Drop files here or click to browse</h3>
          <p className="upload-hint">
            PDF, DOCX, PNG, JPG — certificates, resumes, project reports, internship letters
          </p>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={ACCEPTED_EXTENSIONS}
          onChange={(e) => e.target.files && handleFiles(e.target.files)}
          className="upload-input-hidden"
          id="file-upload-input"
        />
      </div>

      {/* Upload Results */}
      {uploads.length > 0 && (
        <div className="upload-results">
          <h2>Processing Results</h2>
          <div className="upload-results-list">
            {uploads.map((upload, i) => (
              <div
                key={i}
                className={`upload-result-card ${upload.status}`}
              >
                <div className="upload-result-header">
                  <div className="upload-result-status">
                    {upload.status === 'uploading' && (
                      <span className="status-indicator uploading">
                        <span className="spinner" />
                        Processing…
                      </span>
                    )}
                    {upload.status === 'success' && (
                      <span className="status-indicator success">✓ Done</span>
                    )}
                    {upload.status === 'error' && (
                      <span className="status-indicator error">✗ Failed</span>
                    )}
                    {upload.status === 'pending' && (
                      <span className="status-indicator pending">Queued</span>
                    )}
                  </div>
                  <span className="upload-filename">{upload.file.name}</span>
                </div>

                {/* Success: show extraction results */}
                {upload.status === 'success' && upload.document && (
                  <div className="upload-result-details">
                    <div className="result-row">
                      <span className={`category-badge ${getCategoryColorClass(upload.document.category)}`}>
                        {upload.document.category}
                      </span>
                      <div className="confidence-meter">
                        <div className="confidence-bar">
                          <div
                            className={`confidence-fill ${getConfidenceLevel(upload.document.confidence)}`}
                            style={{ width: `${upload.document.confidence * 100}%` }}
                          />
                        </div>
                        <span>{Math.round(upload.document.confidence * 100)}%</span>
                      </div>
                    </div>
                    <h4 className="result-title">{upload.document.title}</h4>
                    {upload.document.issuer && (
                      <p className="result-meta">
                        <span className="meta-label">Issuer:</span> {upload.document.issuer}
                      </p>
                    )}
                    {upload.document.date && (
                      <p className="result-meta">
                        <span className="meta-label">Date:</span> {upload.document.date}
                      </p>
                    )}
                    {upload.document.entities.length > 0 && (
                      <div className="result-entities">
                        {upload.document.entities.map((entity, j) => (
                          <span key={j} className="entity-tag">
                            {entity.name}
                          </span>
                        ))}
                      </div>
                    )}
                    {upload.document.summary && (
                      <p className="result-summary">{upload.document.summary}</p>
                    )}
                  </div>
                )}

                {/* Error: show user-friendly message */}
                {upload.status === 'error' && (
                  <div className="upload-result-error">
                    <p className="error-message">{upload.error}</p>
                    {upload.suggestion && (
                      <p className="error-suggestion">{upload.suggestion}</p>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
